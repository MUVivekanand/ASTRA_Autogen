package prompt

# Default: deny everything unless explicitly allowed
default allow = false

allow if {
    lower(input.prompt) == "authenticate"
}

allow if {
    startswith(lower(input.prompt), "complete_auth")
}

# Allow if the user is authenticated
allow if {
    input.is_authenticated == true
    not blocked_prompt
}

# Block prompts that contain sensitive keywords
blocked_prompt if {
    lower(input.prompt) == "shutdown"
}

blocked_prompt if {
    contains(lower(input.prompt), "delete database")
}