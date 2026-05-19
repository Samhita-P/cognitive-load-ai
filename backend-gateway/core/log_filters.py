import logging
import re

class SensitiveDataFilter(logging.Filter):
    """
    A logging filter that aggressively sanitizes known sensitive patterns
    such as JWTs, tickets, and passwords from logs before emission.
    """
    
    # Regex patterns to detect sensitive data
    # Matches typical JWT eyJ... format
    JWT_PATTERN = re.compile(r"eyJ[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+")
    # Matches Authorization: Bearer <token>
    BEARER_PATTERN = re.compile(r"(Authorization:\s*Bearer\s+)[^\s]+")
    # Matches ?ticket=... or ticket=...
    TICKET_PATTERN = re.compile(r"(ticket=)[^\s&]+")
    # Matches password fields in JSON or dicts
    PASSWORD_PATTERN = re.compile(r"('password'\s*:\s*')([^']+)('|\")|(\"password\"\s*:\s*\")([^\"]+)(\"|')")

    def filter(self, record):
        if isinstance(record.msg, str):
            record.msg = self.mask_sensitive_data(record.msg)
        
        # If args is a string or tuple, sanitize them too
        if isinstance(record.args, tuple):
            sanitized_args = []
            for arg in record.args:
                if isinstance(arg, str):
                    sanitized_args.append(self.mask_sensitive_data(arg))
                else:
                    sanitized_args.append(arg)
            record.args = tuple(sanitized_args)
            
        return True

    def mask_sensitive_data(self, text: str) -> str:
        text = self.JWT_PATTERN.sub("[REDACTED_JWT]", text)
        text = self.BEARER_PATTERN.sub(r"\1[REDACTED_TOKEN]", text)
        text = self.TICKET_PATTERN.sub(r"\1[REDACTED_TICKET]", text)
        # Handle password masking
        text = self.PASSWORD_PATTERN.sub(r"\g<1>[REDACTED_PASSWORD]\g<3>", text)
        text = self.PASSWORD_PATTERN.sub(r"\g<4>[REDACTED_PASSWORD]\g<6>", text)
        return text
