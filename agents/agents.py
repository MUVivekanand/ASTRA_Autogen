import os
from autogen_ext.models.openai import AzureOpenAIChatCompletionClient
from autogen_ext.tools.mcp import StdioServerParams, mcp_server_tools, SseMcpToolAdapter, SseServerParams
from autogen_agentchat.agents import AssistantAgent
from dotenv import load_dotenv

load_dotenv()

AZURE_API_KEY = os.getenv("AZURE_KEY")
AZURE_API_ENDPOINT = os.getenv("AZURE_ENDPOINT")
AZURE_DEPLOYMENT = os.getenv("AZURE_DEPLOYMENT")
APIFY_API_KEY = os.getenv("APIFY_API_KEY")

if not APIFY_API_KEY:
    raise ValueError("APIFY_API_KEY environment variable is not set.")

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
    """Create MCP agent with math and Apify tools"""
    print("Initializing MCP Agent with all tools...")
    
    # Load math tools
    math_server_path = os.path.join(os.path.dirname(__file__), "..", "mcp", "math_server.py")
    math_server = StdioServerParams(
        command="python", args=[math_server_path]
    )
    math_tools = await mcp_server_tools(math_server)
    
    # Load Apify tools
    server_params = SseServerParams(
        url="https://rag-web-browser.apify.actor/sse",
        headers={"Authorization": f"Bearer {APIFY_API_KEY}"},
        timeout=30,
    )
    apify_adapter = await SseMcpToolAdapter.from_server_params(
        server_params,
        "rag-web-browser",
    )
    
    model_client = await create_model_client()
    
    return AssistantAgent(
        name="mcp_agent",
        model_client=model_client,
        tools=math_tools + [apify_adapter],
        reflect_on_tool_use=True,
        system_message=(
            "You are an intelligent assistant with access to mathematical computation tools "
            "and web browsing capabilities. "
            "Use the available tools to help users with calculations, data analysis, "
            "and information gathering from the web. "
            "Provide clear and helpful responses."
        ),
    )