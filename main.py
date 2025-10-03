import asyncio
from pathlib import Path
from autogen_ext.models.openai import AzureOpenAIChatCompletionClient
from autogen_ext.tools.mcp import StdioServerParams, mcp_server_tools
from autogen_agentchat.agents import AssistantAgent
from autogen_core import CancellationToken
from autogen_agentchat.ui import Console
from autogen_ext.tools.mcp import SseMcpToolAdapter, SseServerParams
import os
import json
from dotenv import load_dotenv

# Get environment variables
load_dotenv()
AZURE_API_KEY = os.getenv("AZURE_KEY")
AZURE_API_ENDPOINT = os.getenv("AZURE_ENDPOINT")
AZURE_DEPLOYMENT = os.getenv("AZURE_DEPLOYMENT")
APIFY_API_KEY = os.getenv("APIFY_API_KEY")

if not APIFY_API_KEY:
    raise ValueError("APIFY_API_KEY environment variable is not set.")

if not AZURE_API_KEY or not AZURE_API_ENDPOINT or not AZURE_DEPLOYMENT:
    raise ValueError("OPENAI_API_KEY environment variable is not set.")

TOKEN_FILE = Path(".token.json")

def is_authenticated() -> bool:
    if not TOKEN_FILE.exists():
        return False

    try:
        data = json.loads(TOKEN_FILE.read_text())
        if "token" in data:
            return True
    except Exception:
        return False

    return False

async def run_interactive(agent: AssistantAgent):
    """Interactive loop in terminal"""
    print("\n🔧 Available Tools:")
    for tool in agent._tools:
        desc = getattr(tool, "description", "No description")
        print(f"- {tool.name}: {desc}")
    print("\nType 'exit' to quit.\n")

    while True:
        user_input = input("📝 Task> ").strip()
        if not user_input:
            continue
        if user_input.lower() in {"exit", "quit"}:
            print("👋 Goodbye!")
            break

        await Console(
            agent.run_stream(
                task=user_input,
                cancellation_token=CancellationToken(),
            )
        )

async def main() -> None:
    # --- Load auth tools first ---
    auth_server = StdioServerParams(
        command="python", args=["auth_tools.py"]
    )
    auth_tools = await mcp_server_tools(auth_server)

    # Only provide auth_tools initially
    model_client = AzureOpenAIChatCompletionClient(
        api_key=AZURE_API_KEY,
        model="gpt-4o",
        azure_deployment=AZURE_DEPLOYMENT,
        azure_endpoint=AZURE_API_ENDPOINT,
        api_version="2023-03-15-preview"
    )

    agent = AssistantAgent(
        name="demo_agent",
        model_client=model_client,
        tools=auth_tools,  # start with auth only
        reflect_on_tool_use=True,
        system_message=(
            "You are an intelligent assistant. "
            "The user must authenticate with Google OAuth first using the `authenticate` "
            "and `complete_auth` tools. "
            "Only after successful authentication may you enable and use math tools "
            "and the Apify rag-web-browser adapter."
        ),
    )

    # --- Wait for authentication before enabling other tools ---
    async def gated_tool_setup():
        while True:
            # after complete_auth succeeds, load math + apify tools
            if is_authenticated():  # token saved by auth_tools
                math_server = StdioServerParams(
                    command="python", args=["math_server.py"]
                )
                math_tools = await mcp_server_tools(math_server)

                server_params = SseServerParams(
                    url="https://rag-web-browser.apify.actor/sse",
                    headers={"Authorization": f"Bearer {APIFY_API_KEY}"},
                    timeout=30,
                )
                adapter = await SseMcpToolAdapter.from_server_params(
                    server_params,
                    "rag-web-browser",
                )

                agent._tools.extend(math_tools + [adapter])
                print("✅ Authentication complete — Math + Apify tools now enabled!")
                break
            await asyncio.sleep(2)

    asyncio.create_task(gated_tool_setup())

    await run_interactive(agent)


    # await Console(
    #   agent.run_stream(
    #       task="Summarise the latest news of Iran and US negotiations in one small concise paragraph.",
    #       cancellation_token=CancellationToken(),
    #   )
    # )
    
    # await Console(
    #     agent.run_stream(
    #         task="what's (3 + 5) x 12?", cancellation_token=CancellationToken()
    #     )
    # )

if __name__ == "__main__":
    asyncio.run(main())

