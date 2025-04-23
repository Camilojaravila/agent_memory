from langchain_google_alloydb_pg import AlloyDBEngine, AlloyDBChatMessageHistory
#from langchain_google_alloydb_pg import AlloyDBSaver
from google.cloud.alloydb.connector import IPTypes
from dotenv import load_dotenv
import os
from google.oauth2 import service_account
import json

load_dotenv('.env')

# Load the service account key file
with open(os.getenv('GOOGLE_APPLICATION_CREDENTIALS'), "r") as f:
    service_account_info = json.load(f)

# Create credentials
credentials = service_account.Credentials.from_service_account_info(
    service_account_info
)


engine = AlloyDBEngine.from_instance(
    os.getenv('GOOGLE_PROJECT_ID'),
    region=os.getenv('REGION'),
    cluster=os.getenv('CLUSTER'),
    instance=os.getenv('INSTANCE'),
    database=os.getenv('DATABASE'),
    ip_type=IPTypes.PUBLIC,
)

engine.init_chat_history_table(table_name=os.getenv('TABLE_NAME'))

checkpoint = AlloyDBSaver.create_sync(engine)


def init_tables():
    engine.init_chat_history_table(table_name=os.getenv('TABLE_NAME'))
    engine.init_checkpoint_table(table_name=os.getenv('TABLE_NAME'))

def close_connection():
    engine.close()


def get_by_session_id(session_id: str):
    return AlloyDBChatMessageHistory.create_sync(
        engine,
        session_id=session_id,
        table_name=os.getenv('TABLE_NAME'),
        # schema_name=SCHEMA_NAME,
    )

