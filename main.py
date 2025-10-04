# main.py
import asyncio
from agents import create_auth_agent, create_mcp_agent
from runners import run_auth_agent, run_mcp_agent
from utils import is_authenticated


async def main() -> None:
    """Main execution flow with two-agent system"""
    
    # Check if already authenticated
    if is_authenticated():
        print("Already authenticated. Skipping to MCP Agent...")
        auth_successful = True
    else:
        # Phase 1: Authentication Agent
        auth_agent = await create_auth_agent()
        auth_successful = await run_auth_agent(auth_agent)
    
    if not auth_successful:
        print("Authentication failed or cancelled. Exiting.")
        return
    
    # Phase 2: MCP Agent (only runs after successful authentication)
    mcp_agent = await create_mcp_agent()
    await run_mcp_agent(mcp_agent)


if __name__ == "__main__":
    asyncio.run(main())