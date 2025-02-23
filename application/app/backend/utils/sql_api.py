from sqlmodel import SQLModel, create_engine, Session
from sqlalchemy import DateTime
import os
from contextlib import contextmanager
from backend.schemas.sql_schemas.cosi_usage import CosiUsage
from typing import Dict


class SQLHandler():
    def __init__(self):
        self.engine = create_engine(os.environ["CONNECTION_STRING"], echo=True)

    @contextmanager
    def session(self):
        session = Session(self.engine)
        try:
            yield session
            session.commit()
        except:
            session.rollback()
            raise
        finally:
            session.close()

    def insert_row(self, sql_model: SQLModel, data: Dict):
        with self.session() as session:
            row = sql_model(**data)
            session.add(row)
            return row

def log_usage(oid_hashed: str, session_id: str, chat_type: str, num_token_prompt: int | None, num_token_response: int | None, response_time: int):
    usage_data = {
        "oid_hashed": oid_hashed,
        "session_id": session_id,
        "chat_type": chat_type,
        "num_token_prompt": num_token_prompt,
        "num_token_response": num_token_response,
        "response_time": response_time
    }
    sql_handler = SQLHandler()
    return sql_handler.insert_row(CosiUsage, data=usage_data)
