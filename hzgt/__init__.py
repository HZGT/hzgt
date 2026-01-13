# 版本
from .__version import __version__

version = __version__

# core
from .core import (pic, restrop,
                   bitconv, getfsize, ensure_file, generate_filename,
                   gettime, vargs, dual_support,
                   set_log,
                   getip, validate_ip,
                   AutoConfig,
                   is_admin, require_admin, execute_command, run_as_admin, check_admin_and_prompt
                   )

__all__ = [
    "version",
    "pic", "restrop",
    "bitconv", "getfsize", "ensure_file", "generate_filename",
    "gettime", "vargs", "dual_support",
    "set_log",
    "getip", "validate_ip",
    "AutoConfig",
    "is_admin", "require_admin", "execute_command", "run_as_admin", "check_admin_and_prompt",
]
