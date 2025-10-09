import asyncio
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
    
    # --- Phase 2: MCP Agent with integrated tool detection & OPA ---
    mcp_agent = await create_mcp_agent()
    tool_detection_agent = await create_tool_agent()

    await run_mcp_agent(mcp_agent, tool_detection_agent)

if __name__ == "__main__":
    asyncio.run(main())