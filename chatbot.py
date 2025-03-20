from langgraph.graph import StateGraph, END, START
import agent  # Import the graph builder from agent.py
from postgres_db import checkpoint
from chatbot_schemas import Route, State, List_Formula
import prompts
import formulas  # Import the formulas module

# Augment the LLM with schema for structured output
router = agent.llm.with_structured_output(Route)
formula_params = agent.llm.with_structured_output(List_Formula)


def chatbot(state: State):
    messages = state["messages"][-2:]
    session_id = state["messages"][0].additional_kwargs["session_id"]
    formulas_list = state.get("formulas")

    # Filter and format messages for LLM input
    llm_messages = []
    for message in messages:
        if isinstance(message, agent.HumanMessage):
            llm_messages.append(message)
        elif isinstance(message, agent.SystemMessage) and message.content:  # Check if SystemMessage has content
            llm_messages.append(message)

    # Construct the message string for the LLM
    message_content = ""
    for msg in llm_messages:
      message_content += msg.content + "\n"

    if formulas_list:
        message_content += "\nFormulas found:\n"
        for formula in formulas_list:
            message_content += f"- {formula.name}: {formula.params}\n"

    return {"messages": agent.call_model(message_content, session_id)}



def make_calculations(state: State):
    user_message = state["messages"][-1]
    session_id = state["messages"][0].additional_kwargs["session_id"]
    # Use LLM to extract formula and parameters
    calculation_request: List_Formula = formula_params.invoke(
        [
            prompts.prompt_calculation,
            user_message,
        ]
    )
    results = []
    missing_params = {}

    for formula_item in calculation_request.formulas:
        formula_name = formula_item.key.lower()  # Use formula_item.key instead of name.lower()
        required_params = {param.lower(): None for param in formulas.formulas_list[formulas.formula_names.index(formula_item.key)]["params"]} #gets the required params from the formulas_list
        provided_params = {k.lower(): v for k, v in {p.lower(): None for p in formula_item.params}.items()} #gets the provided params.

        all_params_present = True
        for param in required_params:
            if param not in provided_params:
                all_params_present = False
                if formula_name not in missing_params:
                    missing_params[formula_name] = []
                missing_params[formula_name].append(param)
            else:
                required_params[param] = provided_params[param]

        if all_params_present:
            result = formulas.calculate_formula(formula_name, required_params)
            if result is not None:
                results.append(f"{formula_item.name}: {result}")
            else:
                results.append(f"Could not calculate {formula_item.name}.")
        else:
            results.append(f"Missing parameters for {formula_item.name}.")

    if missing_params:
        missing_params_message = "Por favor necesito los siguientes parámetros:\n"
        for formula, params in missing_params.items():
            missing_params_message += f"{formula}: {', '.join(params)}\n"
        return {"messages": [{"role": "system", "content": missing_params_message}], "formulas": calculation_request.formulas} #Added the formulas in the state.
    else:
        return {"messages": [{"role": "system", "content": "\n".join(results)}], "formulas": calculation_request.formulas} #Added the formulas in the state.


def router_step(state: State):
    # Run the augmented LLM with structured output to serve as routing logic
    decision = router.invoke(
        [
            prompts.prompt_formulas,
            state["messages"][-1],
        ]
    )
    return {"decision": decision.step}

def should_calculate(state: State):
    # Return the node name you want to visit next
    return state["decision"]



builder = StateGraph(state_schema=State)
builder.add_node("chatbot", chatbot)
builder.add_node("formula", make_calculations)
builder.add_node("router", router_step)

builder.add_edge(START, "router")
builder.add_conditional_edges("router", should_calculate, {
    "formula": "formula",
    "chatbot": "chatbot"
})
builder.add_edge("formula", "chatbot")
builder.add_edge("chatbot", END)


# Compile the graph using the builder from agent.py
graph = builder.compile(checkpointer=checkpoint)

        
def stream_graph_updates(user_input: str, session_id: str):
    """Handles user input, processes through the graph, and returns a response."""
    config = {"configurable": {"session_id": session_id, 'thread_id': session_id}}
    events =  graph.stream({"messages": [{"role": "user", "content": user_input, "session_id": session_id}]}, config)
    for event in events:
        for value in event.values():
            if "messages" in value:  # Check if "messages" key exists
                if isinstance(value["messages"], list):
                    last_message = value["messages"][-1]
                else:
                    last_message = value["messages"]

                if hasattr(last_message, 'content'):
                    yield {"assistant_response": last_message.content}
                elif isinstance(last_message, dict) and "content" in last_message:
                    yield {"assistant_response": last_message["content"]}
                else:
                    yield {"assistant_response": "(Unexpected response format)"}
            elif "decision" in value: #check if decision key exists
                yield {"decision": value["decision"]} #yield the decision value
            else:
                 yield {"event_value": str(value)} #yield the entire event value for debugging.


def get_response(user_input: str, session_id: str):
    nodes = list()
    for response in stream_graph_updates(user_input, session_id):
        nodes.append(response)

    return nodes

def get_steps(session_id: str):
    """Retrieves the chat history from the graph."""
    config = {"configurable": {"thread_id": session_id}}
    return graph.get_state(config)

def get_history(session_id: str):
    return agent.get_chat_messages(session_id)

def get_session_ids():
    return agent.get_session_ids()