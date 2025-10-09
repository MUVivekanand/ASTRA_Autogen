package mcp_tools

import rego.v1

import future.keywords.if
import future.keywords.in

# Default deny
default allow := false

# Tool classifications (these should match your Python config)
read_only := [
    "list_databases",
    "list_collections",
    "find_documents",
    "count_documents"
]

write_tools := [
    "insert_document",
    "insert_many_documents",
    "update_document",
    "update_many_documents",
    "delete_document",
    "delete_many_documents",
    "create_collection",
    "drop_collection"
]

all_tools := array.concat(read_only, write_tools)

# Admin: can use all tools
allow if {
    input.is_authenticated == true
    input.role == "admin"
    input.tool in all_tools
}

# Developer: can only use read-only tools
allow if {
    input.is_authenticated == true
    input.role == "developer"
    input.tool in read_only
}

# Viewer: cannot use any tools (denied by default)
# No allow rule for viewer means they're denied

# Provide detailed denial reasons
deny_reason := "User is not authenticated" if {
    not input.is_authenticated
}

deny_reason := "User role 'viewer' has no tool access permissions" if {
    input.is_authenticated == true
    input.role == "viewer"
}

deny_reason := sprintf("Tool '%s' not found in available tools", [input.tool]) if {
    input.is_authenticated == true
    not input.tool in all_tools
}

deny_reason := sprintf("Role '%s' is not authorized to use tool '%s'", [input.role, input.tool]) if {
    input.is_authenticated == true
    input.role == "developer"
    input.tool in write_tools
}

deny_reason := sprintf("Role '%s' is not recognized", [input.role]) if {
    input.is_authenticated == true
    not input.role in ["admin", "developer", "viewer"]
}