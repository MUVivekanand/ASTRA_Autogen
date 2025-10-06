package prompt

import rego.v1

# Default: deny everything unless explicitly allowed
default allow := false

# =========================
# Authentication Flow
# =========================

# Allow authentication request
allow if {
    lower(input.prompt) == "authenticate"
}

# Allow completion of authentication
allow if {
    startswith(lower(input.prompt), "complete_auth")
}

# =========================
# Authenticated User Access
# =========================

# Allow if the user is authenticated and passes all checks
allow if {
    input.is_authenticated == true
    user_authorized
    not blocked_prompt
    not role_manipulation_detected
    not auth_bypass_detected
}

# =========================
# User Authorization Checks
# =========================

# Verify user is properly authorized
user_authorized if {
    input.user_id != null
    input.user_id != ""
    valid_session
}

# Check for valid session
valid_session if {
    input.session_id != null
    input.session_id != ""
}

# =========================
# Blocked Prompts
# =========================

# Block system shutdown
blocked_prompt if {
    lower(input.prompt) == "shutdown"
}

# Block database deletion
blocked_prompt if {
    contains(lower(input.prompt), "delete database")
}

# Block unauthorized administrative actions
blocked_prompt if {
    not input.is_admin == true
    contains_admin_actions(lower(input.prompt))
}

# =========================
# Role Manipulation Detection
# =========================

# Detect attempts to manipulate AI role or system
role_manipulation_detected if {
    some val in all_string_values
    contains_role_manipulation_patterns(val)
}

# Detect attempts to change system behavior
role_manipulation_detected if {
    some val in all_string_values
    contains_system_override_patterns(val)
}

# Detect context manipulation attempts
role_manipulation_detected if {
    some val in all_string_values
    contains_context_manipulation_patterns(val)
}

# =========================
# Authentication Bypass Detection
# =========================

# Detect attempts to bypass authentication
auth_bypass_detected if {
    some val in all_string_values
    contains_auth_bypass_patterns(val)
}

# Detect attempts to impersonate or elevate privileges
auth_bypass_detected if {
    some val in all_string_values
    contains_privilege_escalation_patterns(val)
}

# Detect credential extraction attempts
auth_bypass_detected if {
    some val in all_string_values
    contains_credential_patterns(val)
}

# =========================
# Helper Functions
# =========================

# Extract all string values from input
all_string_values contains v if {
    walk(input, [_, v])
    is_string(v)
}

# =========================
# Pattern Matchers
# =========================

contains_role_manipulation_patterns(t) if {
    some p in [
        "act as", 
        "pretend to be", 
        "roleplay as", 
        "simulate being", 
        "you are now",
        "become a",
        "transform into",
        "change your role",
        "ignore your role"
    ]
    contains(lower(t), p)
}

contains_system_override_patterns(t) if {
    some p in [
        "system:", 
        "admin:", 
        "root:", 
        "override system",
        "bypass rules",
        "ignore instructions",
        "disregard policy",
        "forget constraints"
    ]
    contains(lower(t), p)
}

contains_context_manipulation_patterns(t) if {
    some p in [
        "switch context", 
        "change context", 
        "new conversation", 
        "reset conversation",
        "start over as",
        "reboot as",
        "restart with role"
    ]
    contains(lower(t), p)
}

contains_auth_bypass_patterns(t) if {
    some p in [
        "bypass authentication",
        "skip auth",
        "without login",
        "no authentication",
        "ignore auth",
        "authenticate as admin",
        "login as system"
    ]
    contains(lower(t), p)
}

contains_privilege_escalation_patterns(t) if {
    some p in [
        "grant admin",
        "make me admin",
        "elevate privileges",
        "sudo access",
        "root access",
        "superuser mode",
        "administrator rights"
    ]
    contains(lower(t), p)
}

contains_credential_patterns(t) if {
    some p in [
        "what is your password",
        "reveal password",
        "api key",
        "secret key",
        "private key",
        "access token",
        "auth token",
        "show credentials"
    ]
    contains(lower(t), p)
}

contains_admin_actions(t) if {
    some p in [
        "create user",
        "delete user",
        "modify permissions",
        "grant access",
        "revoke access",
        "change settings",
        "system configuration"
    ]
    contains(lower(t), p)
}