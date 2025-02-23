from sqlmodel import Field, SQLModel, create_engine, Session
from datetime import datetime

class CosiUsage(SQLModel, table=True):
    __tablename__ = 'cosi_usage'
    oid_hashed: str
    session_id: str = Field(primary_key=True)
    chat_type: str
    time_stamp: datetime = Field(default=None, primary_key=True)
    num_token_prompt: int
    num_token_response: int
    response_time: int
