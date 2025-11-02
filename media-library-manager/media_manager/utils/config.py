"""Configuration management for Media Library Manager."""

import os
import yaml
from pathlib import Path
from typing import Any, Dict


class Config:
    """Configuration manager that loads and provides access to configuration."""
    
    def __init__(self, config_path: str = None):
        """
        Initialize configuration manager.
        
        Args:
            config_path: Path to configuration file (defaults to default_config.yaml)
        """
        # Get project root directory
        self.project_root = Path(__file__).parent.parent.parent
        self.config_dir = self.project_root / "config"
        
        # Determine which config file to use
        if config_path is None:
            local_config = self.config_dir / "local_config.yaml"
            default_config = self.config_dir / "default_config.yaml"
            
            if local_config.exists():
                config_path = str(local_config)
            else:
                config_path = str(default_config)
        
        self.config_path = Path(config_path)
        self.config = self._load_config()
        self.rules = self._load_rules()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")
        
        with open(self.config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f) or {}
        
        return config
    
    def _load_rules(self) -> Dict[str, Any]:
        """Load rules from rules.yaml."""
        rules_path = self.config_dir / "rules.yaml"
        
        if not rules_path.exists():
            return {}
        
        with open(rules_path, 'r', encoding='utf-8') as f:
            rules = yaml.safe_load(f) or {}
        
        return rules
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value by key (supports dot notation).
        
        Args:
            key: Configuration key (e.g., 'media_library.movie_paths')
            default: Default value if key not found
        
        Returns:
            Configuration value or default
        """
        keys = key.split('.')
        value = self.config
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def get_media_paths(self) -> Dict[str, list]:
        """Get all media library paths."""
        return {
            'movies': self.get('media_library.movie_paths', []),
            'tv_shows': self.get('media_library.tv_show_paths', []),
            'music': self.get('media_library.music_paths', []),
            'photos': self.get('media_library.photo_paths', [])
        }
    
    def get_all_extensions(self) -> list:
        """Get all supported file extensions."""
        extensions = []
        extensions.extend(self.get('advanced.video_extensions', []))
        extensions.extend(self.get('advanced.audio_extensions', []))
        extensions.extend(self.get('advanced.photo_extensions', []))
        return extensions
    
    def is_extension_supported(self, extension: str) -> bool:
        """Check if file extension is supported."""
        return extension.lower() in [e.lower() for e in self.get_all_extensions()]
    
    def __getitem__(self, key: str) -> Any:
        """Allow dictionary-style access."""
        return self.get(key)
    
    def __contains__(self, key: str) -> bool:
        """Check if key exists in config."""
        return self.get(key) is not None
