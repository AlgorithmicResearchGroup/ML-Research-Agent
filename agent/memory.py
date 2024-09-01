import os
import warnings
import logging
import datetime
from sqlalchemy import create_engine, Column, Integer, String, BigInteger, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


Base = declarative_base()

# Silence all warnings
warnings.filterwarnings("ignore")
Base = declarative_base()

logging.getLogger("sqlalchemy").setLevel(logging.ERROR)


class AgentConversation(Base):
    __tablename__ = "agents_agent"
    id = Column(Integer, primary_key=True)
    run_id = Column(BigInteger, nullable=False)
    tool = Column(String)
    status = Column(String)
    attempt = Column(String)
    stdout = Column(String)
    stderr = Column(String)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow)
    user_id = Column(Integer)
    
    
    
class AgenMemory:
    def __init__(self):
        self.database_url = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
        self.engine = create_engine(self.database_url, echo=False)
        # Base class for our classes definitions
        self.base = declarative_base()
        Base.metadata.create_all(self.engine)

        self.session = sessionmaker(bind=self.engine)
        self.db_session = self.session()
        
        
        
    def save_conversation_memory(self, user_id, run_id, previous_subtask_tool, previous_subtask_result, previous_subtask_attempt, previous_subtask_output, previous_subtask_errors):
        conversatoin = AgentConversation(
            user_id=user_id,
            run_id=run_id,
            tool=str(previous_subtask_tool),
            status=str(previous_subtask_result),
            attempt=str(previous_subtask_attempt),
            stdout=str(previous_subtask_output),
            stderr=str(previous_subtask_errors),
        )
        self.db_session.add(conversatoin)
        self.db_session.commit()
        
        
    def get_conversation_memory(self, run_id):
        conversations = (
            self.db_session.query(AgentConversation).filter_by(run_id=run_id).all()
        )
        memories = []
        full_output_mems = ""
        for conversation in conversations[-5:]:
            previous_subtask_tool = conversation.tool
            previous_subtask_result = conversation.status
            previous_subtask_attempt = conversation.attempt
            previous_subtask_output = conversation.stdout
            previous_subtask_errors = conversation.stderr
            memories.append(
                {
                    "tool": previous_subtask_tool,
                    "status": previous_subtask_result,
                    "attempt": previous_subtask_attempt,
                    "stdout": previous_subtask_output,
                    "stderr": previous_subtask_errors,
                }
            )

            full_output_mems = "Last 10 Attempts\n" + "-" * 100 + "\n"
            for idx, item in enumerate(memories[-10:]):
                formatted_string = "\n".join([f"{value}" for value in item.values()])
                full_output_mems += (
                    f"Attempt {idx + 1}\n{formatted_string}\n" + "-" * 100 + "\n"
                )

            # full_output_mems = "Last 5 Attempts\n" + "-" * 20 + "\n"
            # for idx, item in enumerate(memories[-5:]):
            #     previous_subtask_attempt = item['attempt']
            #     full_output_mems += f"Attempt {idx + 1}:\n{previous_subtask_attempt}\n" + "-" * 20 + "\n"

        return full_output_mems