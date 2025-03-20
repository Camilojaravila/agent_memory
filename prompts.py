from langchain_core.messages import SystemMessage
from formulas import formulas_list

list_formulas = "\n".join([f"{f['key']} - {f['name']}" for f in formulas_list])

router_instructions = f"""
Eres un agente experto que va a definir la ruta de un input de un usuario.

Vas a tomar la decisión entre si un usuario quiere realizar un cálculo de unas fórmulas determinadas o simplemente está haciendo una pregunta.

Las fórmulas son: {list_formulas}

Si tienes información sobre el usuario preguntando sobre esas fórmulas, debes responder 'formula'. Si no, responde 'chatbot'.


"""

prompt_formulas = SystemMessage(content=router_instructions)

formula_instruction = f"""
Eres un agente experto en la clasifiación de formulas a utilizar. vas a seleccionar una o más de estas fórmulas basado en la información del usuario:

{formulas_list}

Vas a devolver una lista de fórmulas seleccionadas con todas sus llaves y valores. en caso de que ninguna fórmula sea seleccionada devuelve una lista vacía.
También, para cada una de las formulas que selecciones, analiza si quiere que sea calculada o no esa fórmula. Es decir, si quiere que sea calculada o solo quiere obtener información sobre ella.
Para cada fórmula que analices agrega la llave 'is_calculated' que será un valor booleano. True si analizas que la fórmula quiere que sea calculada, False de lo contrario.

Devuelve una lista con JSON de fórmulas seleccionada según el input del usuario.
"""

prompt_calculation = SystemMessage(content=formula_instruction)

def get_prompt_params(params_list):
    params_instruction = f"""
    Vas a validar si existe la información de los siguientes valores:

    {params_list}

    Vas a devolver un diccionario como llave los parámetros listados y como valor el valor que hayas asociado, en caso que no hayas asociado ningún valor coloca un None.
    """

    prompt_params = SystemMessage(content=params_instruction)

    return prompt_params