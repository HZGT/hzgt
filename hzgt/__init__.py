# 版本
from .__version import __version__

version = __version__

# core
from .core import (pic, restrop,
                   bitconv, getfsize, ensure_file, ensure_suffix, truncate_fname,
                   gettime, vargs, dual_support,
                   set_log,
                   getip, get_server_urls, AddressFamily,
                   ConditionalDefault, AutoConfig,
                   is_admin, run_cmd
                   )

__all__ = [
    "version",
    "pic", "restrop",
    "bitconv", "getfsize", "ensure_file", "ensure_suffix", "truncate_fname",
    "gettime", "vargs", "dual_support",
    "set_log",
    "getip", "get_server_urls", "AddressFamily",
    "ConditionalDefault", "AutoConfig",
    "is_admin", "run_cmd",
]
