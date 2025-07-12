"""Ability registry module - supports dynamic loading from script paths"""
import importlib.util
import os
from typing import Dict, Type, Optional
from .base_ability import BaseAbility

_ABILITY_REGISTRY: Dict[str, Type[BaseAbility]] = {}
_LOADED_MODULES: Dict[str, bool] = {}

def register_ability(name: str):
    """Decorator to register an ability class"""
    def decorator(cls):
        if not issubclass(cls, BaseAbility):
            raise TypeError(f"Class {cls.__name__} is not a BaseAbility")
        _ABILITY_REGISTRY[name] = cls
        return cls
    return decorator

def get_ability_class(name: str) -> Optional[Type[BaseAbility]]:
    """Retrieve ability class by registered name"""
    return _ABILITY_REGISTRY.get(name, None)

def load_ability_from_script(script_path: str) -> None:
    """
    Load an ability module from a Python script file.
    
    Args:
        script_path (str): Path to the Python script (relative or absolute)
    """
    # Resolve absolute path
    if not os.path.isabs(script_path):
        script_path = os.path.abspath(script_path)
    
    # Check if already loaded
    if script_path in _LOADED_MODULES:
        return
    
    # Validate file existence
    if not os.path.isfile(script_path):
        raise FileNotFoundError(f"Ability script not found: {script_path}")
    
    # Load module dynamically
    try:
        module_name = os.path.splitext(os.path.basename(script_path))[0]
        spec = importlib.util.spec_from_file_location(module_name, script_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        _LOADED_MODULES[script_path] = True
    except Exception as e:
        raise RuntimeError(f"Failed to load ability script {script_path}: {e}")