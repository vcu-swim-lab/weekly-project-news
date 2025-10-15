# prompts/__init__.py
from .prompts import (
    individual_instructions,
    general_instructions,
    pull_request_instructions,
)

# discussion prompt can be a function or a constant in discussion_prompt.py 
try:
    # if a function exists, re-export it
    from .discussion.prompt import discussion_instructions
except Exception:
    # otherwise wrap the constant as s function
    from .discussion_prompt import DISCUSSION_INSTRUCTIONS as _DISCUSSION_INSTRUCTIONS
    
    def discussion_instructions():
        return _DISCUSSION_INSTRUCTIONS
    
__all__ = [
    "individual_instructions",
    "general_instructions",
    "pull_request_instructions",
    "discussion_instructions",
]
