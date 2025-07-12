"""Configuration management module"""
import yaml
import logging
from typing import Dict

_CONFIG: Dict = {}

def load_config(config_file: str) -> None:
    """Load configuration from YAML file"""
    global _CONFIG
    try:
        with open(config_file, 'r') as f:
            _CONFIG = yaml.safe_load(f)
        logging.info(f"Config loaded from {config_file}")
        return True
    except Exception as e:
        logging.error(f"Failed to load config: {str(e)}")
    return False

def get_config() -> Dict:
    """Get current configuration"""
    return _CONFIG