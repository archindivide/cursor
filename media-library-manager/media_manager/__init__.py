"""Media Library Manager - A comprehensive media file management system."""

__version__ = "0.1.0"
__author__ = "Media Library Manager Team"

from .utils.config import Config
from .utils.logger import setup_logger

__all__ = ['Config', 'setup_logger']
