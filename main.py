import asyncio
import json
from agents.agents import create_auth_agent, create_mcp_agent, create_tool_agent
from utils.runners import run_auth_agent, run_mcp_agent, run_tool_agent
from utils.check import is_authenticated
from utils.opa import check_with_opa

async def main() -> None:
    """Main execution flow with three-phase system"""
    
    # --- Phase 1: Authentication ---
    if is_authenticated():
        print("Already authenticated. Skipping to tool detection phase...")
        auth_successful = True
    else:
        auth_agent = await create_auth_agent()
        auth_successful = await run_auth_agent(auth_agent)
    
    if not auth_successful:
        print("Authentication failed or cancelled. Exiting.")
        return
    
    # --- Phase 2: Tool Detection & OPA check ---
    print("\n=== TOOL DETECTION PHASE ===")
    print("Enter a natural language instruction for the MCP Agent:")
    user_input = input("Prompt> ").strip()
    if not user_input:
        print("No prompt entered. Exiting.")
        return
    
    # Create AI agent to detect the tool
    detect_tool_agent = await create_tool_agent()
    detected_tool_info = await run_tool_agent(detect_tool_agent)

    detected_tool_info_dict = dict(detected_tool_info)
    
    # Expecting detected_tool_info dict: { "tool_name": str, "tool_type": "read_only|write|all" }
    tool_name = detected_tool_info_dict.get("tool_name", "")
    tool_type = detected_tool_info_dict.get("tool_type", "")
    
    print(f"\nDetected Tool: {tool_name}")
    print(f"Tool Type: {tool_type}")
    
    # Check with OPA
    allowed = check_with_opa(tool=tool_name, prompt=user_input)
    if not allowed:
        print("Request blocked by OPA policy. Exiting.")
        return
    
    # --- Phase 3: Run MCP Agent ---
    print("\n=== MCP AGENT PHASE ===")
    mcp_agent = await create_mcp_agent()
    
    # Run the tool on the agent
    await run_mcp_agent(mcp_agent)

if __name__ == "__main__":
    asyncio.run(main())