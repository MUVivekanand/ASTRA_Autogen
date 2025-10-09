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


async def run_mcp_agent(mcp_agent: AssistantAgent, tool_detection_agent: AssistantAgent):
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

        detected_tool_info = await run_tool_agent(tool_detection_agent)
        tool_name = detected_tool_info.get("tool_name", "")
        tool_type = detected_tool_info.get("tool_type", "")

        if not tool_name:
            print("Could not detect an appropriate tool")
            continue

        print(f"\nDetected Tool: {tool_name} (Type: {tool_type})")

        if not check_with_opa(tool=tool_name):
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
    
    response_text = str(response_text.messages[0].content).strip()

    try:
        match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if match:
            return json.loads(match.group(0))
    except json.JSONDecodeError:
        print("JSON extraction failed. Raw output:\n", response_text)

    return {"tool_name": "", "tool_type": ""}