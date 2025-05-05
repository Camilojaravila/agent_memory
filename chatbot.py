from langgraph.graph import StateGraph, END, START
from typing import List, Optional
import agent, connection, formulas, prompts
from chatbot_schemas import State, RouterOutput, FormulaInfo, ExtractedParams, List_Formula
from helpers import time_now
from uuid import uuid4
from formulas import formulas_list
import json
import logging
import uuid
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),  # Salida a consola
        #logging.FileHandler("chatbot.log")  # También a archivo
    ]
)
logger = logging.getLogger(__name__)


def get_last_human_message(messages: List[agent.BaseMessage]) -> Optional[agent.HumanMessage]:
    """Extrae el contenido del último mensaje humano."""
    for msg in reversed(messages):
        if isinstance(msg, agent.HumanMessage):
            return msg
    return None

def route_request(state: State) -> dict:
    """Nodo Router: Decide si ir a 'formula' o 'chatbot'."""
    logger.info("--- Ejecutando Nodo: route_request ---")
    last_human_message = get_last_human_message(state['messages'])
    if not last_human_message:
        logger.warning("No se encontró mensaje humano para el routing. Defecto: chatbot.")
        return {"decision": "chatbot"}
    # Usa LLM estructurado para tomar la decisión
    router_runnable = prompts.prompt_router | agent.llm_structured.with_structured_output(RouterOutput)
    try:
        routing_decision: RouterOutput = router_runnable.invoke({"question": last_human_message.content})
        logger.info(f"Decisión del Router: {routing_decision.decision}")
        return {"decision": routing_decision.decision}
    except Exception as e:
        logger.error(f"Error durante el routing: {e}", exc_info=True)
        return {"decision": "chatbot"} # Fallback seguro

def analyze_formulas_node(state: State) -> dict:
    """Nodo Análisis Fórmulas: Identifica fórmulas y la intención (calc/info)."""
    logger.info("--- Ejecutando Nodo: analyze_formulas_node ---")
    last_human_message = get_last_human_message(state['messages'])
    analyzed_formulas_list: FormulaInfo = [] # Especifica el tipo esperado
    if not last_human_message:
        logger.warning("No se encontró mensaje humano para analizar fórmulas.")
    else:
        # Prepara el diccionario de entrada con AMBAS variables requeridas por el prompt
        input_data_for_prompt = {
            "question": last_human_message.content,
            "formulas_json": str(formulas_list) # Convierte la lista real a string JSON aquí
        }
        logger.debug(f"Input para prompt_formula_analysis: {input_data_for_prompt.keys()}")

        analysis_runnable = prompts.prompt_formula_analysis | agent.llm_structured.with_structured_output(List_Formula)
        try:
            # Invoca el runnable con el diccionario de entrada completo
            analysis_result = analysis_runnable.invoke(input_data_for_prompt)
            # Procesa el resultado (debería ser List[FormulaInfo])
            if isinstance(analysis_result, List_Formula):
                # Validación adicional opcional (ej: asegurar que los items son FormulaInfo)
                analyzed_formulas_list = [f for f in analysis_result.formulas if isinstance(f, FormulaInfo)]
                logger.info(f"Fórmulas Analizadas (tipo {type(analysis_result)}): {[f.__dict__ for f in analyzed_formulas_list]}")
            else:
                # Manejar casos donde with_structured_output falle o devuelva otro tipo
                logger.warning(f"Salida inesperada de analysis_runnable: {type(analysis_result)}. Se esperaba FormulaInfo.")
                # Podrías intentar parsear si es un AIMessage con JSON string, como fallback
                if hasattr(analysis_result, 'content') and isinstance(analysis_result.content, str):
                    try:
                        parsed_list = json.loads(analysis_result.content)
                        validated_formulas = [FormulaInfo(**item) for item in parsed_list]
                        analyzed_formulas_list = validated_formulas
                        logger.info(f"Fórmulas Analizadas (parseado de string): {[f.dict() for f in analyzed_formulas_list]}")
                    except Exception as parse_err:
                        logger.error(f"Error parseando fallback JSON: {parse_err}", exc_info=True)
                # Si no se puede procesar, la lista quedará vacía
        except Exception as e:
            logger.error(f"Error durante la invocación/procesamiento del análisis de fórmulas: {e}", exc_info=True)
            import traceback
            traceback.print_exc()
            analyzed_formulas_list = [] # Resetea en caso de error
    # Devuelve la lista (posiblemente vacía) al estado
    return {"analyzed_formulas": analyzed_formulas_list}

def calculation_node(state: State) -> dict:
    """Nodo Cálculo: Intenta calcular o pide parámetros."""
    logger.info("--- Ejecutando Nodo: calculation_node ---")
    analyzed_formulas: List[FormulaInfo] = state.get("analyzed_formulas", [])
    messages_to_add: List[agent.BaseMessage] = []
    session_id = state['messages'][0].additional_kwargs.get('session_id') if state['messages'] else None
    missing_params_map = {} # { 'formula_key': ['param1', 'param2'] }
    ai_kwargs = {
        "created_at": time_now(),
        # Podrías añadir más info relevante del AI aquí:
        "model_used": agent.MODEL_NAME, # Si está accesible
        # "token_usage": response_metadata.get("usage_metadata"), # Si obtienes metadata
    }

    formulas_needing_calc = [f for f in analyzed_formulas if f.is_calculated]
    if not formulas_needing_calc:
        logger.info("No hay fórmulas marcadas para cálculo. Pasando al chatbot.")
        # No añadir mensajes, el chatbot se encargará de explicar si es necesario
        return {}
    # --- Lógica de Extracción de Parámetros ---
    # Implementación básica: Buscar en el último mensaje (MEJORAR ESTO)
    last_human_message = get_last_human_message(state['messages'])
    for formula_info in formulas_needing_calc:
        required = formula_info.params_required
        provided_values = {} # { 'param_name': value }
        missing = []
        # AQUÍ VA LA LÓGICA DE EXTRACCIÓN - Ejemplo Placeholder (NO USAR EN PRODUCCIÓN)
        logger.info(f"Buscando parámetros para {formula_info.key}: {required}")
        # Intenta extraerlos del último mensaje (esto es muy básico)
        # Necesitas una estrategia robusta: LLM dedicado, regex, etc.
        # Por ahora, asumiremos que no se encuentran para forzar la petición
        for param in required:
            # if param_found_and_value_extracted(param, last_human_message):
            #    provided_values[param] = extracted_value
            # else:
            missing.append(param) # Asume que falta por ahora
        if not missing:
             # --- Realizar Cálculo ---
             try:
                 # Asegúrate que los valores en provided_values son numéricos
                 numeric_params = {k: float(v) for k, v in provided_values.items() if v is not None} # Convertir a float
                 result = formulas.calculate_formula(formula_info.key, numeric_params)
                 if result is not None:
                     msg_content = f"Calculé el {formula_info.name} ({formula_info.key}): {result}"
                     messages_to_add.append(agent.AIMessage(
                         content=msg_content, 
                         id = f"formula_{uuid.uuid4()}",
                         additional_kwargs=ai_kwargs
                         ))
                     logger.info(msg_content)
                 else:
                     msg_content = f"No pude calcular el {formula_info.name} ({formula_info.key}) con los datos."
                     messages_to_add.append(agent.AIMessage(
                                                            content=msg_content, 
                                                            id = f"formula_{uuid.uuid4()}",
                                                            additional_kwargs=ai_kwargs
                                                            ))
                     logger.info(msg_content)
             except Exception as e:
                 logger.error(f"Error calculando {formula_info.key}: {e}", exc_info=True)
                 messages_to_add.append(agent.AIMessage(content=f"Tuve un problema al calcular el {formula_info.name}.",
                                                        id = f"formula_{uuid.uuid4()}",
                                                        additional_kwargs=ai_kwargs
                                                        ))
        else:
            # --- Registrar Parámetros Faltantes ---
            missing_params_map[formula_info.key] = missing
            logger.info(f"Parámetros faltantes para {formula_info.key}: {missing}")
    # --- Generar Mensaje de Petición de Parámetros (si aplica) ---
    if missing_params_map:
        prompt_missing = "Para poder calcular, necesito algunos datos más:\n"
        for key, params in missing_params_map.items():
            formula_name = next((f.name for f in analyzed_formulas if f.key == key), key)
            prompt_missing += f"- Para **{formula_name} ({key})**: {', '.join(params)}\n"
        prompt_missing += "¿Me los podrías dar?"
        messages_to_add.append(agent.AIMessage(
            content=prompt_missing,
            id = f"formula_{uuid.uuid4()}",
            additional_kwargs=ai_kwargs
            ))
        logger.info("Generando petición de parámetros.")
    # Devuelve los mensajes generados (resultados o peticiones)
    return {"messages": messages_to_add}


def chatbot_node(state: State) -> dict:
    """Nodo Chatbot: Ejecuta la cadena RAG principal de Niilo."""
    logger.info("--- Ejecutando Nodo: chatbot_node ---")
    session_id = state['messages'][0].additional_kwargs.get('session_id') if state['messages'] else None
    if not session_id:
        logger.error("Error crítico: Falta session_id en el estado.")
        return {"messages": [agent.AIMessage(
            content=f"Lo siento, hubo un error interno {session_id}.", 
            id= f"chatbot_{uuid.uuid4()}",
            additional_kwargs=ai_kwargs)
            ]}
    config = {"configurable": {"session_id": session_id}}
    last_human_message = get_last_human_message(state['messages'])

    if not last_human_message:
        # Si el último mensaje fue del sistema (p.ej., pidiendo parámetros), Niilo no debería decir nada nuevo aún.
        logger.info("No hay nuevo mensaje humano. Niilo espera respuesta.")
        # Devolver estado sin añadir mensaje de Niilo
        return {}
    # Ejecuta la cadena RAG con historial
    try:
        # Pasamos el contenido del último mensaje humano como 'question'
        ai_message: agent.AIMessage = agent.chain_with_history.invoke({"question": last_human_message}, config=config)
        # --- Añadir explicaciones si fórmulas 'is_calculated=false' ---
        analyzed_formulas = state.get("analyzed_formulas", [])
        
        formulas_to_explain = [f for f in analyzed_formulas if not f.is_calculated]
        explanation_suffix = ""
        if formulas_to_explain:
            explanation_suffix = "\n\nSobre las fórmulas que mencionaste y no calculamos:\n"
            # Aquí Niilo debería generar la explicación como parte de su lógica interna
            # El prompt ya le indica que lo haga. No es necesario añadir texto aquí,
            # PERO podrías pasarle explícitamente qué explicar si el prompt no es suficiente.
            # Por simplicidad, confiamos en el prompt de Niilo.
            # for f_info in formulas_to_explain:
            #    explanation_suffix += f"- **{f_info.name} ({f_info.key})**: [Explicación breve aquí]\n"
            pass # Confiar en el prompt de Niilo para manejar esto internamente basado en su contexto.
        

        final_content = ai_message.content
        
        logger.info(f"Respuesta de Niilo (RAG): {final_content}")
        ai_message.__setattr__('content', final_content)
        return {"messages": [ai_message]}
    except Exception as e:
        logger.error(f"Error en la cadena RAG de Niilo: {e}", exc_info=True)
        try:
            ai_id = ai_message.id
            ai_kwargs = ai_message.additional_kwargs
        except:
            ai_id = f"chatbot_{uuid.uuid4()}"
            ai_kwargs = {
                "created_at": time_now(),
                # Podrías añadir más info relevante del AI aquí:
                "model_used": agent.MODEL_NAME, # Si está accesible
                # "token_usage": response_metadata.get("usage_metadata"), # Si obtienes metadata
            }
        
        return {"messages": [agent.AIMessage(
            content="Uff, tuve un problema procesando eso. ¿Intentamos de nuevo?", 
            id = ai_id,
            additional_kwargs=ai_kwargs
            )]}

# --- Construcción del Grafo ---
builder = StateGraph(State)

# Añadir Nodos
builder.add_node("router", route_request)
builder.add_node("analyze_formulas", analyze_formulas_node)
builder.add_node("calculate", calculation_node)
builder.add_node("chatbot", chatbot_node)

# Definir Flujo
builder.add_edge(START, "router")
builder.add_conditional_edges(
    "router",
    lambda state: state["decision"], # Función de condición basada en la salida del router
    {
        "formula": "analyze_formulas", # Si es 'formula', analiza
        "chatbot": "chatbot",        # Si es 'chatbot', va directo a Niilo
    }
)
builder.add_edge("analyze_formulas", "calculate") # Después de analizar, siempre intenta calcular/pedir params
builder.add_edge("calculate", "chatbot") # Después de calcular/pedir, deja que Niilo responda
builder.add_edge("chatbot", END) # La respuesta de Niilo es el final del turno

# Compilar el Grafo con Checkpointer
graph = builder.compile(checkpointer=agent.checkpoint)


# --- Funciones de Invocación y Streaming (Adaptadas) ---

def stream_graph_updates(user_input: str, session_id: str):
    """Maneja input, procesa en grafo, y produce eventos de streaming."""
    config = {"configurable": {"thread_id": session_id, "session_id": session_id,}}

    additional_configs = {
        "session_id": session_id,
        "created_at": time_now(),
        }

    initial_message = agent.HumanMessage(
        content=user_input,
        id = f"user_{uuid.uuid4()}",
        additional_kwargs= additional_configs# Importante para el estado inicial
    )

    logger.info(f"--- Input del ususario: {user_input} ---")

    # Usar stream_mode="updates" para obtener salidas de nodos a medida que ocurren
    events = graph.stream({"messages": [initial_message]}, config=config, stream_mode="updates")
    for event in events:
        for node_name, node_output in event.items():
            act_time = time_now()
        
            logger.debug(f"Output from node '{node_name}': {node_output}")
            # Busca mensajes añadidos por el nodo actual
            if isinstance(node_output, dict) and "messages" in node_output:
                new_messages = node_output["messages"]
                if isinstance(new_messages, list) and new_messages:
                    # Solo produce el contenido del último mensaje AI añadido por este nodo
                    last_msg = new_messages[-1]
                    if isinstance(last_msg, agent.AIMessage):
                        yield {
                            "assistant_response": last_msg.content,
                            "id": last_msg.id,
                            "created_at": last_msg.additional_kwargs.get('created_at', act_time),
                            }
                    elif isinstance(last_msg, dict) and last_msg.get("type") == "ai": # Compatibilidad
                        yield {
                            "assistant_response": last_msg.get("content", ""),
                            "id": last_msg.get("id"),
                            "created_at": last_msg.get("additional_kwargs").get('created_at', act_time),
                            }
            elif not node_output:
                yield {
                    "event_value": "pass",
                    "created_at": act_time,
                       }
            elif "decision" in node_output: #check if decision key exists
                yield {
                    "decision": node_output["decision"],
                    "created_at": act_time,
                    } #yield the decision value
            else:
                 yield {
                     "event_value": str(node_output),
                     "created_at": act_time,
                     } #yield the entire event value for debugging.
            # Podrías añadir yields para otros datos del estado si es necesario (ej: 'decision')


def get_response(user_input: str, session_id: str) -> List[dict]:
    """Obtiene la(s) respuesta(s) del asistente para una entrada de usuario."""
    responses = []
    stream = stream_graph_updates(user_input, session_id)
    for chunk in stream:
        if "assistant_response" in chunk:
            responses.append(chunk) # Acumula todas las respuestas generadas en el turno
    # Si no hubo respuestas en el stream (raro), intenta obtener el estado final
    if not responses:
         try:
            final_state = graph.get_state({"configurable": {"thread_id": session_id}})
            if final_state and 'messages' in final_state:
                 last_message = final_state['messages'][-1]
                 if isinstance(last_message, agent.AIMessage):
                      responses.append({"assistant_response": last_message.content})
         except Exception as e:
             logger.error(f"Error obteniendo estado final: {e}")

    return responses if responses else [{"assistant_response": "(No se generó respuesta)"}]


def get_steps(session_id: str):
    """Retrieves the chat history from the graph."""
    config = {"configurable": {"thread_id": session_id}}
    return graph.get_state(config)

def get_history(session_id: str):
    messages = agent.get_chat_messages(session_id)
    user_session = connection.get_session_user(session_id)
    messages_id = [m.id for m in messages]
    info = connection.get_message_revision(messages_id)
    messages_info = {m.message_id: m.__dict__ for m in info}
    resp = []

    for message in messages:
        message_info = messages_info.get(message.id, {})
        structured_message = {
            "message_id": message.id,
            "session_id": session_id,
            "user_id": user_session.user_id,
            "content": message.content,
            "type": message.type,
            "created_at": message.additional_kwargs.get('created_at'),
            "like": message_info.get("like", False),
            "feedback": message_info.get("feedback", []),
            "observations": message_info.get("observations", ''),
        }
        resp.append(structured_message)

    return resp

def get_session_ids(user_id: str):
    sessions = connection.get_sessions_by_user(user_id)
    resp = []
    for session in sessions:
        user_message = agent.get_chat_messages(str(session.session_id))
        resp.append({
            'session_id': session.session_id,
            'created_at': session.created_at,
            'last_update': session.updated_at,
            'user_id': session.user_id,
            'first_message': user_message[0].content if user_message else ""
        })
    return resp

def get_new_session_id(**kwargs):
    data = dict(**kwargs)
    return connection.create_session(data)

def update_timestamp(session_id: str):
    info = {
        'updated_at': time_now()
    }

    connection.update_user_session(session_id, info)

def delete_conversation(session_id: str):
    info = {
        'is_active': False
    }

    return connection.update_user_session(session_id, info)

def update_message(info):

    info['created_at'] = time_now()

    return connection.create_message_revision(info)
