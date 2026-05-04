from slowapi import Limiter
from slowapi.util import get_remote_address
from .config import get_settings

limiter = Limiter(key_func=get_remote_address, enabled=get_settings().rate_limit_enabled)
