import os
import json
from pathlib import Path
from openai import AzureOpenAI
from dotenv import load_dotenv
import numpy as np

load_dotenv()

class LLM_Embeddings:
    def __init__(self):
        self.client = AzureOpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            api_version="2023-05-15",
            azure_endpoint=os.getenv("AZURE_ENDPOINT_EMBEDDING"),
        )


    def save_embeddings(self, embeddings, filename):
        try:
            with open(filename, "w", encoding="utf-8") as f:
                json_embeddings = {k: v.tolist() for k, v in embeddings.items()}
                json.dump(json_embeddings, f)
            print("Successfully saved embeddings to ", filename)
        except IOError as io_error:
            print("Error saving embeddings to file: ", io_error)
            raise


    def load_embeddings(self, filename):
        try:
            print(f"Loading embeddings from file: {filename}")
            with open(filename, "r", encoding="utf-8") as f:
                json_embeddings = json.load(f)
                embeddings = {k: np.array(v) for k, v in json_embeddings.items()}
            print("Successfully loaded embeddings from ", filename)
            return embeddings
        except FileNotFoundError:
            print("File not found: ", filename)
            raise
        except IOError as io_error:
            print("Error loading embeddings from file", io_error)
            raise

    def get_openai_embedding(
        self, text, model = "text-embedding-ada-002"
    ):
        response = self.client.embeddings.create(
            model=model,
            input=text,
        )
        embedding_vector = np.array(response.data[0].embedding)
        return embedding_vector


    def cosine_similarity(self, a, b):
        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
    
    def find_most_similar_tools(
        self, query, embedding_dict, top_n = 1
    ):
        try:
            query_vector = self.get_openai_embedding(query)
        except (ConnectionError, ValueError) as e:
            print("Error generating embedding for query:", str(e))
            return []

        similarities = {}
        for tool_name, vector in embedding_dict.items():
            similarity = self.cosine_similarity(query_vector, vector)
            similarities[tool_name] = similarity

        sorted_tools = sorted(
            similarities.items(), key=lambda item: item[1], reverse=True
        )
        return sorted_tools[:top_n]
    
tool_descriptions = {
    "list_databases": "List all databases in MongoDB instance.",
    "list_collections": "List all collections in a specific database.",
    "find_documents": "Find documents in a collection.",
    "insert_document": "Insert a new document into a collection.",
    "insert_many_documents": "Insert multiple documents into a collection.",
    "update_document": "Update a single document in a collection.",
    "update_many_documents": "Update multiple documents in a collection.",
    "delete_document": "Delete a single document from a collection.",
    "delete_many_documents": "Delete multiple documents from a collection.",
    "count_documents": "Count documents in a collection.",
    "create_collection": "Create a new collection in a database.",
    "drop_collection": "Drop (delete) a collection from a database."
}

EMBEDDING_FILE = TOKEN_FILE = Path(__file__).parent.parent / "tools_embeddings.json"

try:
    llm_embeddings = LLM_Embeddings()
    global_tool_embeddings = llm_embeddings.load_embeddings(EMBEDDING_FILE)
except FileNotFoundError:
    global_tool_embeddings = {}
    for tool_name, description in tool_descriptions.items():
        try:
            embedding_result = llm_embeddings.get_openai_embedding(description)
            global_tool_embeddings[tool_name] = embedding_result
        except (ConnectionError, ValueError) as e:
            print("Error :", str(e))
    llm_embeddings.save_embeddings(global_tool_embeddings, EMBEDDING_FILE)
    print(f"Generated and saved new embeddings to  {EMBEDDING_FILE}")