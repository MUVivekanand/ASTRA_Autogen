import os
from autogen_ext.models.openai import AzureOpenAIChatCompletionClient
from autogen_ext.tools.mcp import StdioServerParams, mcp_server_tools
from autogen_agentchat.agents import AssistantAgent
from dotenv import load_dotenv

load_dotenv()

AZURE_API_KEY = os.getenv("AZURE_KEY")
AZURE_API_ENDPOINT = os.getenv("AZURE_ENDPOINT")
AZURE_DEPLOYMENT = os.getenv("AZURE_DEPLOYMENT")

if not AZURE_API_KEY or not AZURE_API_ENDPOINT or not AZURE_DEPLOYMENT:
    raise ValueError("Azure API credentials are not set.")


async def create_model_client():
    """Create Azure OpenAI model client"""
    return AzureOpenAIChatCompletionClient(
        api_key=AZURE_API_KEY,
        model="gpt-4o-2024-05-13",
        azure_deployment=AZURE_DEPLOYMENT,
        azure_endpoint=AZURE_API_ENDPOINT,
        api_version="2023-03-15-preview"
    )


async def create_auth_agent():
    """Create authentication agent with only auth tools"""
    print("Initializing Authentication Agent...")
    
    auth_server_path = os.path.join(os.path.dirname(__file__), "..", "mcp", "auth_tools.py")
    auth_server = StdioServerParams(
        command="python", args=[auth_server_path]
    )
    auth_tools = await mcp_server_tools(auth_server)
    
    model_client = await create_model_client()
    
    return AssistantAgent(
        name="auth_agent",
        model_client=model_client,
        tools=auth_tools,
        reflect_on_tool_use=True,
        system_message=(
            "You are an authentication assistant. "
            "Your only job is to help the user authenticate with Google OAuth. "
            "Use the `authenticate` tool to start the OAuth flow, "
            "then use the `complete_auth` tool with the authorization code "
            "provided by the user after they complete the OAuth flow in their browser. "
            "Once authentication is complete, inform the user they can now access other tools."
        ),
    )


async def create_mcp_agent():
    """Create MCP agent with math and mongodb tools"""
    print("Initializing MCP Agent with all tools...")
    
    # Load math tools
    math_server_path = os.path.join(os.path.dirname(__file__), "..", "mcp", "math_server.py")

    mongo_server_path = os.path.join(os.path.dirname(__file__), "..", "mcp", "mongo_db.py")

    math_server = StdioServerParams(
        command="python", args=[math_server_path]
    )

    mongo_server = StdioServerParams(
        command="python", args=[mongo_server_path]
    )

    math_tools = await mcp_server_tools(math_server)

    mongo_tools = await mcp_server_tools(mongo_server)
    
    # Load Apify tools
    # server_params = SseServerParams(
    #     url="https://rag-web-browser.apify.actor/sse",
    #     headers={"Authorization": f"Bearer {APIFY_API_KEY}"},
    #     timeout=30,
    # )
    # apify_adapter = await SseMcpToolAdapter.from_server_params(
    #     server_params,
    #     "rag-web-browser",
    # )
    
    model_client = await create_model_client()
    
    return AssistantAgent(
        name="mcp_agent",
        model_client=model_client,
        tools=mongo_tools + math_tools,
        reflect_on_tool_use=True,
        system_message=(
            "You are an intelligent assistant with access to mathematical computation tools "
            "and web browsing capabilities. "
            "You can modify/create/edit documents of mongodb collections with the mcp tool of mongo db"
            "Use the available tools to help users with calculations, data analysis, etc."
            "and information gathering from the web. "
            "Provide clear and helpful responses."
        ),
    )

async def create_tool_agent():
    """
    Create a lightweight AI agent to detect the tool from a natural language prompt.
    """
    print("Initializing Tool Detection Agent...")

    system_message = (
        "You are a tool detection assistant.\n"
        "Given a user's natural language instruction, identify the single most appropriate "
        "MongoDB tool that should be used and classify it as either 'read_only' or 'write'.\n\n"
        
        "Available READ-ONLY tools:\n"
        "- list_databases: List all available databases\n"
        "- list_collections: List all collections in a database\n"
        "- find_documents: Query and retrieve documents from a collection\n"
        "- count_documents: Count documents matching a query\n\n"
        
        "Available WRITE tools:\n"
        "- insert_document: Insert a single document into a collection\n"
        "- insert_many_documents: Insert multiple documents into a collection\n"
        "- update_document: Update a single document in a collection\n"
        "- update_many_documents: Update multiple documents in a collection\n"
        "- delete_document: Delete a single document from a collection\n"
        "- delete_many_documents: Delete multiple documents from a collection\n"
        "- create_collection: Create a new collection in a database\n"
        "- drop_collection: Drop/delete an entire collection\n\n"
        
        "Instructions:\n"
        "1. Analyze the user's instruction carefully\n"
        "2. Select exactly ONE tool from the lists above\n"
        "3. Set tool_type to 'read_only' if the tool is from the READ-ONLY list\n"
        "4. Set tool_type to 'write' if the tool is from the WRITE list\n"
        "5. If no tool matches, return {\"tool_name\": \"\", \"tool_type\": \"\"}\n"
        "6. Output MUST be valid JSON only - no explanations, no extra text\n\n"
        
        "Return your response as strict JSON only, exactly like this:\n"
        '{"tool_name": "<tool_name>", "tool_type": "read_only"}\n'
        "OR\n"
        '{"tool_name": "<tool_name>", "tool_type": "write"}\n\n'
        
        "Examples:\n"
        "User: 'Show me all databases' → {\"tool_name\": \"list_databases\", \"tool_type\": \"read_only\"}\n"
        "User: 'Add a new user to the users collection' → {\"tool_name\": \"insert_document\", \"tool_type\": \"write\"}\n"
        "User: 'How many products are there?' → {\"tool_name\": \"count_documents\", \"tool_type\": \"read_only\"}\n"
        "User: 'Delete all old records' → {\"tool_name\": \"delete_many_documents\", \"tool_type\": \"write\"}\n"
        "User: 'List all the documents' → {\"tool_name\": \"list_documents\", \"tool_type\": \"read_only\"}\n"
    )

    model_client = await create_model_client()

    return AssistantAgent(
        name="tool_detection_agent",
        model_client=model_client,
        system_message=system_message,
        reflect_on_tool_use=False
    )
