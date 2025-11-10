# 🤖 MCP Server Security Framework - MCP-Sec

## OAuth 2.0:

Google OAuth 2.0 is used as an auth layer for MCP server

## OPA Policies:

Added a policy.rego file for restricted roles, admin privileges
(for testing: ```C:\opa\opa.exe run --server --addr=:8181 policy.rego```)

## Custom MCP Tools available:

MongoDB tools, auth_tools for OAuth

## AI Agents working:

auth_agent (v1.0), mcp_agent(v1.0)

## Architecture layers:

1. OAuth 2.0 Layer - Google Authentication
2. OPA layer - Role based access
3. Prompt injection - Preventing critical database attacks
4. Security integrated sandboxed environment for AI agents.

## Future work:

1. HTTPS/TLS along with restricted permissions in docker
2. Rate Limiting, Caching, Load Balancing for OPA

## Docker Commands:

1. ```docker compose build --no-cache```
2. ```docker compose run --rm mcp-framework```




