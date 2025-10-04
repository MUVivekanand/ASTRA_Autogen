# runners.py
from autogen_agentchat.agents import AssistantAgent
from autogen_core import CancellationToken
from autogen_agentchat.ui import Console
from utils import is_authenticated


async def run_auth_agent(auth_agent: AssistantAgent) -> bool:
    """Run authentication agent until successful authentication"""
    print("\n=== AUTHENTICATION REQUIRED ===")
    print("Please authenticate using Google OAuth.\n")
    
    print("Available Tools:")
    for tool in auth_agent._tools:
        desc = getattr(tool, "description", "No description")
        print(f"- {tool.name}: {desc}")
    print("\nType 'auth' to start authentication process.\n")

    while not is_authenticated():
        user_input = input("Auth> ").strip()
        if not user_input:
            continue
        
        if user_input.lower() in {"exit", "quit"}:
            print("Authentication cancelled. Exiting...")
            return False

        await Console(
            auth_agent.run_stream(
                task=user_input,
                cancellation_token=CancellationToken(),
            )
        )
        
        # Check authentication status after each interaction
        if is_authenticated():
            print("\n✓ Authentication successful!")
            return True
        else:
            print("\nAuthentication not yet complete. Please continue...")
    
    return True


async def run_mcp_agent(mcp_agent: AssistantAgent):
    """Run main MCP agent with all tools enabled"""
    print("\n=== MCP AGENT ACTIVE ===")
    print("\nAvailable Tools:")
    for tool in mcp_agent._tools:
        desc = getattr(tool, "description", "No description")
        print(f"- {tool.name}: {desc}")
    print("\nType 'exit' to quit.\n")

    while True:
        user_input = input("Task> ").strip()
        if not user_input:
            continue
        if user_input.lower() in {"exit", "quit"}:
            print("Agent stopped!")
            break

        await Console(
            mcp_agent.run_stream(
                task=user_input,
                cancellation_token=CancellationToken(),
            )
        )