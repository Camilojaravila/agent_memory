# Servicio: Niilo Chat

## 1. Propósito

**Niilo Chat** es el backend del agente multimodal de Niilo. Su función principal es procesar y responder las consultas de los usuarios utilizando un Large Language Model (LLM) enriquecido con contexto de documentos almacenados en Weaviate. También es capaz de realizar cálculos de fórmulas económicas predefinidas.

## 2. Tecnologías y Dependencias

* **Lenguaje:** Python
* **Framework:** FastAPI
* **Dependencias Clave:**
    * **Gemini (Vertex AI):** Para las capacidades del LLM.
    * **MongoDB:** Para almacenar información de sesión o logs.
    * **Weaviate:** Base de datos vectorial para el contexto y los documentos.

## 3. Configuración

La configuración del servicio se gestiona a través de variables de entorno y secretos en Google Secret Manager.

### Variables de Entorno

| Variable                 | Descripción                                                              |
| ------------------------ | ------------------------------------------------------------------------ |
| `GOOGLE_PROJECT_ID`      | El ID del proyecto en Google Cloud Platform (GCP).                       |
| `GOOGLE_APPLICATION_CREDENTIALS` | La ruta al archivo de credenciales JSON de una IAM.              |
| `WCD_URL`                | La URL de la instancia de Weaviate Cloud.                                |
| `WCD_API_KEY`            | La API Key para autenticarse con Weaviate Cloud.                         |
| `WCD_CRED_SECRET_NAME`   | Nombre del secreto en Secret Manager con la configuración de Weaviate.   |
| `DB_SECRET_NAME`         | Nombre del secreto en Secret Manager con la configuración de AlloyDB.    |
| `AGENT_SECRET_NAME`      | Nombre del secreto en Secret Manager con la configuración de los agentes.|
| `ENV`                    | Entorno de ejecución (e.g., `development`, `production`).                |

## 4. Ejecución de la Aplicación

### A) Usando Docker (Recomendado)
Utiliza el `Dockerfile` en esta carpeta para construir y ejecutar la imagen del servicio.

```bash
# 1. Construir la imagen
docker build -t niilo-chat .

# 2. Ejecutar el contenedor (asegúrate de pasar las variables de entorno)
docker run -p 8080:8080 --env-file .env niilo-chat
```

### B) De forma Local (para desarrollo)
1.  **Crea y activa un entorno virtual:**
    ```bash
    python -m venv venv
    source venv/bin/activate
    ```
2.  **Instala las dependencias:**
    ```bash
    pip install -r requirements.txt
    ```
3.  **Ejecuta la aplicación con Uvicorn:**
    ```bash
    uvicorn main:app --host 0.0.0.0 --port 8080
    ```

## 5. Estructura del Código

La aplicación está organizada por servicios.

```
app/
  ├── agent.py      # Definición y lógica del agente conversacional
  ├── chatbot.py    # Orquestación principal del chat
  ├── prompts.py    # Plantillas de prompts para el LLM
  └── main.py       # Punto de entrada de la aplicación FastAPI y routers
```

## 6. Documentación de la API

La documentación interactiva de la API está disponible gracias a FastAPI. Con la aplicación en marcha, visítala en:

* **`http://localhost:8080/docs`**