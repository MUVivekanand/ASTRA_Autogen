from autogen_agentchat.agents import AssistantAgent
from autogen_core import CancellationToken
from autogen_agentchat.ui import Console
from utils.check import is_authenticated
from utils.opa import check_with_opa

import json,re

async def run_auth_agent(auth_agent: AssistantAgent) -> bool:
    """Run authentication agent until successful authentication"""
    print("\n=== AUTHENTICATION REQUIRED ===")
    print("Please authenticate using Google OAuth.\n")
    
    print("Available Tools:")
    for tool in auth_agent._tools:
        desc = getattr(tool, "description", "No description")
        print(f"- {tool.name}: {desc}")
    print("\nType 'authenticate' to start authentication process.\n")

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
        
        if is_authenticated():
            print("\nAuthentication successful!")
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

        if not check_with_opa(user_input):
            print("Request blocked by OPA policy")
            continue

        await Console(
            mcp_agent.run_stream(
                task=user_input,
                cancellation_token=CancellationToken(),
            )
        )


async def run_tool_agent(tool_detection_agent: AssistantAgent) -> dict:
    response_text = await Console(tool_detection_agent.run_stream(
        cancellation_token=CancellationToken()
    ))
    
    # Convert to string and strip whitespace
    response_text = str(response_text.messages[0].content).strip()
    print("\nTool Detection Agent Response:\n", response_text) 
    """Extract first JSON object from a string and parse it."""
    try:
        # Match curly braces content
        match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if match:
            return json.loads(match.group(0))
    except json.JSONDecodeError:
        print("⚠ JSON extraction failed. Raw output:\n", response_text)
    return {"tool_name": "", "tool_type": ""}