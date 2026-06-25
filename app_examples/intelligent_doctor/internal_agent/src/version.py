# -*- coding: utf-8 -*-
"""
Version information module

Automatic version information file injected during build.
"""

__version__ = "eb183af"
__git_commit__ = "eb183af"
__build_date__ = "2026-06-24T11:06:35Z"
VERSION_STRING = f"{__version__}+{__git_commit__}"

VERSION_INFO = {
    "version": __version__,
    "git_commit": __git_commit__,
    "build_date": __build_date__,
    "version_string": VERSION_STRING,
}

def get_version() -> str:
    """Get version number"""
    return __version__

def get_version_info() -> dict:
    """Get complete version information"""
    return VERSION_INFO.copy()

def get_version_string() -> str:
    """Get complete version string"""
    return VERSION_STRING
