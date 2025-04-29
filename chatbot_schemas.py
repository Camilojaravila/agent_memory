from pydantic import BaseModel, Field
from typing import Annotated, Literal, List, Optional, Dict, Union
from typing_extensions import TypedDict
from langgraph.graph import add_messages
from langchain_core.messages import BaseMessage # Importante para el estado

# Schema para el output del NODO de análisis de fórmulas
class FormulaInfo(BaseModel):
    key: str = Field(..., description="La clave única de la fórmula (ej. 'CAC')")
    name: str = Field(..., description="El nombre descriptivo de la fórmula (ej. 'Costo de Adquisición de Clientes')")
    params_required: List[str] = Field(..., description="Lista de nombres de los parámetros necesarios para calcular esta fórmula.")
    is_calculated: bool = Field(..., description="True si el usuario parece querer calcular esta fórmula, False si solo busca información.")

# Schema para el NODO de routing
class RouterOutput(BaseModel):
    decision: Literal["formula", "chatbot"] = Field(description="El siguiente paso a tomar: analizar fórmulas o ir al chatbot.")

# Schema para el NODO de extracción de parámetros (si se usa)
class ExtractedParams(BaseModel):
    # Permite valores None si no se encuentran
    params: Dict[str, Optional[Union[float, int, str]]] = Field(description="Diccionario con parámetros extraídos y sus valores.")


class List_Formula(BaseModel):
    formulas: List[FormulaInfo]

# Estado Principal del Grafo LangGraph
class State(TypedDict):
    # Historial de mensajes (fundamental)
    messages: Annotated[List[BaseMessage], add_messages]

    # Decisión del router
    decision: Optional[Literal["formula", "chatbot"]]

    # Resultado del análisis de fórmulas (lista de objetos FormulaInfo)
    analyzed_formulas: Optional[List[FormulaInfo]]

    # Opcional: Podrías añadir un campo para parámetros extraídos si es necesario pasarlos explícitamente
    # extracted_params_for_calc: Optional[Dict[str, ExtractedParams]] # Ej: {'CAC': ExtractedParams(...)}