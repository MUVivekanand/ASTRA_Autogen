import os
from typing import Optional, Dict, Any
from pymongo import MongoClient
from pymongo.errors import PyMongoError
from bson import ObjectId
from fastmcp import FastMCP
from dotenv import load_dotenv
import json

load_dotenv()

mcp = FastMCP(name="mongodb-mcp")

# MongoDB configuration
MONGO_URI = os.getenv("MONGO_URI")
mongo_client: Optional[MongoClient] = None


def get_mongo_client() -> MongoClient:
    """Get or create MongoDB client"""
    global mongo_client
    if mongo_client is None:
         mongo_client = MongoClient(MONGO_URI)
    return mongo_client


def serialize_document(doc: Dict[str, Any]) -> Dict[str, Any]:
    """Convert MongoDB document to JSON-serializable format"""
    if doc is None:
        return None
    
    serialized = {}
    for key, value in doc.items():
        if isinstance(value, ObjectId):
            serialized[key] = str(value)
        elif isinstance(value, dict):
            serialized[key] = serialize_document(value)
        elif isinstance(value, list):
            serialized[key] = [serialize_document(item) if isinstance(item, dict) else item for item in value]
        else:
            serialized[key] = value
    return serialized


@mcp.tool()
async def list_databases() -> str:
    """
    List all databases in MongoDB instance
    """
    try:
        client = get_mongo_client()
        databases = client.list_database_names()
        return json.dumps({
            "databases": databases,
            "count": len(databases)
        }, indent=2)
    except PyMongoError as e:
        return f"Error listing databases: {str(e)}"


@mcp.tool()
async def list_collections(database_name: str) -> str:
    """
    List all collections in a specific database
    """
    try:
        client = get_mongo_client()
        db = client[database_name]
        collections = db.list_collection_names()
        return json.dumps({
            "database": database_name,
            "collections": collections,
            "count": len(collections)
        }, indent=2)
    except PyMongoError as e:
        return f"Error listing collections: {str(e)}"


@mcp.tool()
async def find_documents(
    database_name: str,
    collection_name: str,
    filter_query: Optional[str] = None,
    limit: int = 10
) -> str:
    """
    Find documents in a collection
    """
    try:
        client = get_mongo_client()
        db = client[database_name]
        collection = db[collection_name]
        
        # Parse filter query if provided
        query = {}
        if filter_query:
            try:
                query = json.loads(filter_query)
            except json.JSONDecodeError:
                return "Error: Invalid filter query JSON"
        
        # Find documents
        documents = list(collection.find(query).limit(limit))
        serialized_docs = [serialize_document(doc) for doc in documents]
        
        return json.dumps({
            "database": database_name,
            "collection": collection_name,
            "filter": query,
            "count": len(serialized_docs),
            "documents": serialized_docs
        }, indent=2)
    except PyMongoError as e:
        return f"Error finding documents: {str(e)}"


@mcp.tool()
async def insert_document(
    database_name: str,
    collection_name: str,
    document: str
) -> str:
    """
    Insert a new document into a collection
    """
    try:
        client = get_mongo_client()
        db = client[database_name]
        collection = db[collection_name]
        
        # Parse document
        try:
            doc = json.loads(document)
        except json.JSONDecodeError:
            return "Error: Invalid document JSON"
        
        # Insert document
        result = collection.insert_one(doc)
        
        return json.dumps({
            "database": database_name,
            "collection": collection_name,
            "inserted_id": str(result.inserted_id),
            "acknowledged": result.acknowledged
        }, indent=2)
    except PyMongoError as e:
        return f"Error inserting document: {str(e)}"


@mcp.tool()
async def insert_many_documents(
    database_name: str,
    collection_name: str,
    documents: str
) -> str:
    """
    Insert multiple documents into a collection
    """
    try:
        client = get_mongo_client()
        db = client[database_name]
        collection = db[collection_name]
        
        # Parse documents
        try:
            docs = json.loads(documents)
            if not isinstance(docs, list):
                return "Error: Documents must be a JSON array"
        except json.JSONDecodeError:
            return "Error: Invalid documents JSON"
        
        # Insert documents
        result = collection.insert_many(docs)
        
        return json.dumps({
            "database": database_name,
            "collection": collection_name,
            "inserted_ids": [str(id) for id in result.inserted_ids],
            "count": len(result.inserted_ids),
            "acknowledged": result.acknowledged
        }, indent=2)
    except PyMongoError as e:
        return f"Error inserting documents: {str(e)}"


@mcp.tool()
async def update_document(
    database_name: str,
    collection_name: str,
    filter_query: str,
    update_data: str,
    upsert: bool = False
) -> str:
    """
    Update a single document in a collection
    """
    try:
        client = get_mongo_client()
        db = client[database_name]
        collection = db[collection_name]
        
        # Parse filter and update data
        try:
            filter_dict = json.loads(filter_query)
            update_dict = json.loads(update_data)
        except json.JSONDecodeError:
            return "Error: Invalid JSON in filter or update data"
        
        # Update document
        result = collection.update_one(filter_dict, update_dict, upsert=upsert)
        
        return json.dumps({
            "database": database_name,
            "collection": collection_name,
            "matched_count": result.matched_count,
            "modified_count": result.modified_count,
            "upserted_id": str(result.upserted_id) if result.upserted_id else None,
            "acknowledged": result.acknowledged
        }, indent=2)
    except PyMongoError as e:
        return f"Error updating document: {str(e)}"


@mcp.tool()
async def update_many_documents(
    database_name: str,
    collection_name: str,
    filter_query: str,
    update_data: str
) -> str:
    """
    Update multiple documents in a collection
    """
    try:
        client = get_mongo_client()
        db = client[database_name]
        collection = db[collection_name]
        
        # Parse filter and update data
        try:
            filter_dict = json.loads(filter_query)
            update_dict = json.loads(update_data)
        except json.JSONDecodeError:
            return "Error: Invalid JSON in filter or update data"
        
        # Update documents
        result = collection.update_many(filter_dict, update_dict)
        
        return json.dumps({
            "database": database_name,
            "collection": collection_name,
            "matched_count": result.matched_count,
            "modified_count": result.modified_count,
            "acknowledged": result.acknowledged
        }, indent=2)
    except PyMongoError as e:
        return f"Error updating documents: {str(e)}"


@mcp.tool()
async def delete_document(
    database_name: str,
    collection_name: str,
    filter_query: str
) -> str:
    """
    Delete a single document from a collection
    """
    try:
        client = get_mongo_client()
        db = client[database_name]
        collection = db[collection_name]
        
        # Parse filter
        try:
            filter_dict = json.loads(filter_query)
        except json.JSONDecodeError:
            return "Error: Invalid filter query JSON"
        
        # Delete document
        result = collection.delete_one(filter_dict)
        
        return json.dumps({
            "database": database_name,
            "collection": collection_name,
            "deleted_count": result.deleted_count,
            "acknowledged": result.acknowledged
        }, indent=2)
    except PyMongoError as e:
        return f"Error deleting document: {str(e)}"


@mcp.tool()
async def delete_many_documents(
    database_name: str,
    collection_name: str,
    filter_query: str
) -> str:
    """
    Delete multiple documents from a collection
    """
    try:
        client = get_mongo_client()
        db = client[database_name]
        collection = db[collection_name]
        
        # Parse filter
        try:
            filter_dict = json.loads(filter_query)
        except json.JSONDecodeError:
            return "Error: Invalid filter query JSON"
        
        # Delete documents
        result = collection.delete_many(filter_dict)
        
        return json.dumps({
            "database": database_name,
            "collection": collection_name,
            "deleted_count": result.deleted_count,
            "acknowledged": result.acknowledged
        }, indent=2)
    except PyMongoError as e:
        return f"Error deleting documents: {str(e)}"


@mcp.tool()
async def count_documents(
    database_name: str,
    collection_name: str,
    filter_query: Optional[str] = None
) -> str:
    """
    Count documents in a collection
    """
    try:
        client = get_mongo_client()
        db = client[database_name]
        collection = db[collection_name]
        
        # Parse filter query if provided
        query = {}
        if filter_query:
            try:
                query = json.loads(filter_query)
            except json.JSONDecodeError:
                return "Error: Invalid filter query JSON"
        
        # Count documents
        count = collection.count_documents(query)
        
        return json.dumps({
            "database": database_name,
            "collection": collection_name,
            "filter": query,
            "count": count
        }, indent=2)
    except PyMongoError as e:
        return f"Error counting documents: {str(e)}"


@mcp.tool()
async def create_collection(
    database_name: str,
    collection_name: str
) -> str:
    """
    Create a new collection in a database
    """
    try:
        client = get_mongo_client()
        db = client[database_name]
        db.create_collection(collection_name)
        
        return json.dumps({
            "database": database_name,
            "collection": collection_name,
            "status": "created"
        }, indent=2)
    except PyMongoError as e:
        return f"Error creating collection: {str(e)}"


@mcp.tool()
async def drop_collection(
    database_name: str,
    collection_name: str
) -> str:
    """
    Drop (delete) a collection from a database
    """
    try:
        client = get_mongo_client()
        db = client[database_name]
        db.drop_collection(collection_name)
        
        return json.dumps({
            "database": database_name,
            "collection": collection_name,
            "status": "dropped"
        }, indent=2)
    except PyMongoError as e:
        return f"Error dropping collection: {str(e)}"


if __name__ == "__main__":
    mcp.run(transport="stdio")