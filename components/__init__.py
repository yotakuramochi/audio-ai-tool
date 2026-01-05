"""
UI Components Package
"""
from components.sidebar import render_sidebar
from components.home import render_home
from components.script import render_script
from components.transcriptions import render_transcriptions
from components.history import render_script_history
from components.settings import render_settings

__all__ = [
    'render_sidebar',
    'render_home',
    'render_script',
    'render_transcriptions',
    'render_script_history',
    'render_settings'
]
