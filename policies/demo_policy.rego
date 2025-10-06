package prompt

import rego.v1

default allow := false

allow if {
    input.is_authenticated == true
    input.is_admin == true
}
