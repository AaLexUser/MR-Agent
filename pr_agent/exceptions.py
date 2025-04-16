class OutputParserException(ValueError):
    """Exception that output parsers should raise to signify a parsing error."""
    
class ContextWindowExceededError(Exception):
    """Exception raised when the context window is exceeded."""
    
    def __init__(self, message: str, max_tokens: int, current_tokens: int):
        self.message = message
        self.max_tokens = max_tokens
        self.current_tokens = current_tokens