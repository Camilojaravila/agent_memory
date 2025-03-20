from typing import Annotated, Dict

formula_names = ["ROI", "CAC", "LTV", "CTS", "Tasa de Retencion", "ROAS", "MRR", "ARR", "NPS",
                     "Burn Rate", "Runway", "TAM", "SAM", "SOM", "CAP", "GMV", "ARPA", "ARPU"]

formulas_list = [
    {
        'key': 'ROI',
        'name': 'Retorno de la Inversión',
        'params': ['Beneficio Neto', 'Costo de la Inversión']
    },
    {
        'key': 'CAC',
        'name': 'Costo de Adquisición de Clientes',
        'params': ['Gastos Totales de Ventas y Marketing', 'Número de Nuevos Clientes Adquiridos']
    },
    {
        'key': 'LTV',
        'name': 'Valor de Vida del Cliente',
        'params': ['Ingreso Promedio por Usuario', 'Margen Bruto (%)', 'Tasa de Deserción de Clientes']
    },
    {
        'key': 'CTS',
        'name': 'Costo de Servicio',
        'params': ['Costo Total del Servicio', 'Número de Clientes Atendidos']
    },
    {
        'key': 'Tasa de Retencion',
        'name': 'Tasa de Retención',
        'params': ['Clientes al Final del Período', 'Nuevos Clientes Adquiridos', 'Clientes al Inicio del Período']
    },
    {
        'key': 'ROAS',
        'name': 'Retorno sobre el Gasto en Publicidad',
        'params': ['Ingresos Generados por Publicidad', 'Costo de Publicidad']
    },
    {
        'key': 'MRR',
        'name': 'Ingresos Mensuales Recurrentes',
        'params': ['Cantidad de Clientes', 'Ingreso Promedio por Cliente por Mes']
    },
    {
        'key': 'ARR',
        'name': 'Ingresos Anuales Recurrentes',
        'params': ['MRR']
    },
    {
        'key': 'NPS',
        'name': 'Net Promoter Score',
        'params': ['% Promotores', '% Detractores']
    },
    {
        'key': 'Burn Rate',
        'name': 'Tasa de Consumo de Efectivo',
        'params': ['Efectivo Inicial', 'Efectivo Final', 'Número de Meses']
    },
    {
        'key': 'Runway',
        'name': 'Duración del Capital',
        'params': ['Efectivo Disponible', 'Burn Rate']
    },
    {
        'key': 'TAM',
        'name': 'Mercado Total Direccionable',
        'params': ['Tamaño del Mercado Total', 'Precio Promedio por Unidad']
    },
    {
        'key': 'SAM',
        'name': 'Mercado Accesible Direccionable',
        'params': ['Porción del TAM accesible', 'Precio Promedio por Unidad']
    },
    {
        'key': 'SOM',
        'name': 'Mercado Obtenible Servible',
        'params': ['Porción del SAM capturable', 'Precio Promedio por Unidad']
    },
    {
        'key': 'CAP',
        'name': 'Costo de Adquisición de Producto',
        'params': ['Costo Total de Producción del Producto', 'Número de Unidades Producidas']
    },
    {
        'key': 'GMV',
        'name': 'Gross Merchandise Value - Valor Bruto de Mercancía',
        'params': ['Precio Total de Venta', 'Cantidad de Productos Vendidos']
    },
    {
        'key': 'ARPA',
        'name': 'Average Revenue per Account - Ingreso Promedio por Cuenta',
        'params': ['Ingresos Totales', 'Número de Cuentas o Clientes Activos']
    },
    {
        'key': 'ARPU',
        'name': 'Average Revenue per User - Ingreso Promedio por Usuario',
        'params': ['Ingresos Totales', 'Número de Usuarios Activos']
    }
]

def calculate_formula(formula_name: str, params: Dict[str, float]) -> float:
    """Calculates the result of a given formula."""
    try:
        if formula_name.lower() == "roi":
            return (params["beneficio_neto"] / params["costo_inversion"]) * 100
        elif formula_name.lower() == "cac":
            return params["gastos_ventas_marketing"] / params["numero_nuevos_clientes"]
        elif formula_name.lower() == "ltv":
            return (params["ingreso_promedio_usuario"] * params["margen_bruto"]) / params["tasa_desercion"]
        elif formula_name.lower() == "cts":
            return params["costo_total_servicio"] / params["numero_clientes_atendidos"]
        elif formula_name.lower() == "tasa_retencion":
            return ((params["clientes_final_periodo"] - params["nuevos_clientes_adquiridos"]) / params["clientes_inicio_periodo"]) * 100
        elif formula_name.lower() == "roas":
            return params["ingresos_generados_publicidad"] / params["costo_publicidad"]
        elif formula_name.lower() == "mrr":
            return params["cantidad_clientes"] * params["ingreso_promedio_cliente_mes"]
        elif formula_name.lower() == "arr":
            return params["mrr"] * 12
        elif formula_name.lower() == "nps":
            return params["porcentaje_promotores"] - params["porcentaje_detractores"]
        elif formula_name.lower() == "burn_rate":
            return (params["efectivo_inicial"] - params["efectivo_final"]) / params["numero_meses"]
        elif formula_name.lower() == "runway":
            return params["efectivo_disponible"] / params["burn_rate"]
        elif formula_name.lower() == "tam":
            return params["tamano_mercado_total"] * params["precio_promedio_unidad"]
        elif formula_name.lower() == "sam":
            return params["porcion_tam_accesible"] * params["precio_promedio_unidad"]
        elif formula_name.lower() == "som":
            return params["porcion_sam_capturable"] * params["precio_promedio_unidad"]
        elif formula_name.lower() == "cap":
            return params["costo_total_produccion"] / params["numero_unidades_producidas"]
        elif formula_name.lower() == "gmv":
            return params["precio_total_venta"] * params["cantidad_productos_vendidos"]
        elif formula_name.lower() == "arpa":
            return params["ingresos_totales"] / params["numero_cuentas_clientes"]
        elif formula_name.lower() == "arpu":
            return params["ingresos_totales"] / params["numero_usuarios_activos"]
        else:
            return None
    except KeyError:
        return None
    except Exception as e:
        print(f"Error calculating formula: {e}")
        return None