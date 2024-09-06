import os
import warnings
import logging
import datetime
from sqlalchemy import create_engine, Column, Integer, String, BigInteger, DateTime, Float, ARRAY
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.dialects.postgresql import ARRAY
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import weaviate
import json

Base = declarative_base()

# Silence all warnings
warnings.filterwarnings("ignore")
Base = declarative_base()

logging.getLogger("sqlalchemy").setLevel(logging.ERROR)


class AgentConversation(Base):
    __tablename__ = "agents_agent_final_run"
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


class AgentMemory:
    def __init__(self):
        self.database_url = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
        self.engine = create_engine(self.database_url, echo=False)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        
        # Initialize sentence transformer for encoding
        self.encoder = SentenceTransformer('all-MiniLM-L6-v2')
        
        self.weaviate_client = weaviate.Client(
            url="https://9bdretuzqa6sdq98tde6ww.c0.us-east1.gcp.weaviate.cloud",
            auth_client_secret=weaviate.AuthApiKey(api_key="ZDAAIqZWGfzxMdjNJzOO4yCigAtTujlefGAN")
        )
        self._create_schema()
        
        # Create a directory to store embeddings
        self.embedding_dir = os.path.join(os.getcwd(), 'embeddings')
        os.makedirs(self.embedding_dir, exist_ok=True)
        
    def _create_schema(self):
        schema = {
            "classes": [{
                "class": "AgentMemory",
                "vectorizer": "none",  # We'll provide our own vectors
                "properties": [
                    {"name": "user_id", "dataType": ["int"]},
                    {"name": "run_id", "dataType": ["int"]},
                    {"name": "tool", "dataType": ["string"]},
                    {"name": "status", "dataType": ["string"]},
                    {"name": "attempt", "dataType": ["string"]},
                    {"name": "stdout", "dataType": ["text"]},
                    {"name": "stderr", "dataType": ["text"]},
                    {"name": "created_at", "dataType": ["date"]}
                ]
            }]
        }
        # Check if the schema already exists
        existing_schema = self.weaviate_client.schema.get()
        existing_classes = [c['class'] for c in existing_schema['classes']]
        
        if "AgentMemory" not in existing_classes:
            self.weaviate_client.schema.create_class(schema['classes'][0])
        else:
            print("AgentMemory schema already exists. Skipping creation.")

    def save_conversation_memory(self, user_id, run_id, previous_subtask_tool, previous_subtask_result, previous_subtask_attempt, previous_subtask_output, previous_subtask_errors):
        session = self.Session()
        try:
            memory_text = f"Run ID: {run_id}\nUser ID: {user_id}\nTool: {previous_subtask_tool}\nStatus: {previous_subtask_result}\nAttempt: {previous_subtask_attempt}\nStdout: {previous_subtask_output}\nStderr: {previous_subtask_errors}"
            embedding = self.encoder.encode(memory_text).tolist()

            conversation = AgentConversation(
                user_id=user_id,
                run_id=run_id,
                tool=str(previous_subtask_tool),
                status=str(previous_subtask_result),
                attempt=str(previous_subtask_attempt),
                stdout=str(previous_subtask_output),
                stderr=str(previous_subtask_errors)
            )
            session.add(conversation)
            session.commit()

            # Save embedding to a file
            current_time = datetime.datetime.utcnow()
            rfc3339_time = current_time.isoformat("T") + "Z"
            memory_data = {
                "user_id": user_id,
                "run_id": run_id,
                "tool": str(previous_subtask_tool),
                "status": str(previous_subtask_result),
                "attempt": str(previous_subtask_attempt),
                "stdout": str(previous_subtask_output),
                "stderr": str(previous_subtask_errors),
                "created_at": rfc3339_time
            }
            memory_text = json.dumps(memory_data)
            embedding = self.encoder.encode(memory_text).tolist()
            
            self.weaviate_client.data_object.create(
                class_name="AgentMemory",
                data_object=memory_data,
                vector=embedding
            )

        finally:
            session.close()

    def get_conversation_memory(self, run_id, previous_subtask_output):
        session = self.Session()
        try:
            # Short-term memory (last 5 steps)
            short_term_conversations = (
                session.query(AgentConversation)
                .filter_by(run_id=run_id)
                .order_by(AgentConversation.created_at.desc())
                .limit(5)
                .all()
            )
            short_term_memories = []
            for conversation in reversed(short_term_conversations):
                short_term_memories.append({
                    "tool": conversation.tool,
                    "status": conversation.status,
                    "attempt": conversation.attempt,
                    "stdout": conversation.stdout,
                    "stderr": conversation.stderr,
                })

            # Long-term memory (vector search using Weaviate)
            query_text = previous_subtask_output
            query_embedding = self.encoder.encode(query_text).tolist()
            
            # Perform vector search in Weaviate
            results = (
                self.weaviate_client.query
                .get("AgentMemory", ["user_id", "run_id", "tool", "status", "attempt", "stdout", "stderr", "created_at"])
                .with_near_vector({"vector": query_embedding})
                .with_limit(2)
                .with_additional(["distance"])
                .do()
            )

            long_term_memories = results['data']['Get']['AgentMemory']
            

            # Combine short-term and long-term memories
            full_output_mems = "Short-term Memory (Last 5 actions)\n" + "-" * 100 + "\n"
            for idx, item in enumerate(short_term_memories):
                formatted_string = "\n".join([f"{key}: {value}" for key, value in item.items()])
                full_output_mems += f"Action {idx + 1}\n{formatted_string}\n" + "-" * 100 + "\n"

            full_output_mems += "\nLong-term Memory (Similar past experiences)\n" + "-" * 100 + "\n"
            for idx, item in enumerate(long_term_memories):
                formatted_string = "\n".join([f"{key}: {value}" for key, value in item.items() if key != 'created_at'])
                full_output_mems += f"Experience {idx + 1} (Created: {item['created_at']})\n{formatted_string}\n" + "-" * 100 + "\n"

            return full_output_mems
        finally:
            session.close()