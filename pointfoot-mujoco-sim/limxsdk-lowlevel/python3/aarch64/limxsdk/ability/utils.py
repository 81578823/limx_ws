"""Utility functions for dynamic module loading"""
import importlib.util
import os
from typing import List

def load_modules_from_paths(paths: List[str]) -> None:
    """
    Dynamically load Python modules from specified paths.
    
    Args:
        paths (List[str]): List of directories containing Python modules
    """
    for path in paths:
        if not os.path.isdir(path):
            continue
        
        # Load all .py files in the directory
        for filename in os.listdir(path):
            if filename.endswith(".py") and not filename.startswith("__"):
                module_name = filename[:-3]
                file_path = os.path.join(path, filename)
                
                try:
                    # Import module dynamically
                    spec = importlib.util.spec_from_file_location(module_name, file_path)
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                except Exception as e:
                    print(f"Failed to load module {module_name} from {file_path}: {e}")