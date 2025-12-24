"""
Module Manager - Gestion des modules contextuels
"""
import importlib
import os
from typing import Dict, List, Optional

class ModuleManager:
    """Gestionnaire de modules"""
    
    def __init__(self, modules_dir='modules'):
        self.modules_dir = modules_dir
        self.loaded_modules: Dict[str, any] = {}
        self.active_modules: List[str] = []
    
    def discover_modules(self) -> List[str]:
        """Découvre les modules disponibles"""
        if not os.path.exists(self.modules_dir):
            return []
        
        modules = []
        for file in os.listdir(self.modules_dir):
            if file.endswith('_module.py') and file != 'base_module.py':
                module_name = file[:-3]  # Enlever .py
                modules.append(module_name)
        
        return modules
    
    def load_module(self, module_name: str) -> bool:
        """Charge un module"""
        if module_name in self.loaded_modules:
            return True
        
        try:
            module_path = f'{self.modules_dir}.{module_name}'
            module = importlib.import_module(module_path)
            
            # Chercher la classe Module
            class_name = ''.join(word.capitalize() for word in module_name.split('_'))
            module_class = getattr(module, class_name, None)
            
            if module_class:
                instance = module_class()
                self.loaded_modules[module_name] = instance
                return True
        
        except Exception as e:
            print(f"Erreur chargement {module_name}: {e}")
        
        return False
    
    def activate_module(self, module_name: str):
        """Active un module"""
        if module_name not in self.loaded_modules:
            if not self.load_module(module_name):
                return
        
        if module_name not in self.active_modules:
            self.active_modules.append(module_name)
    
    def deactivate_module(self, module_name: str):
        """Désactive un module"""
        if module_name in self.active_modules:
            self.active_modules.remove(module_name)
    
    def get_active_modules(self) -> List[str]:
        """Retourne les modules actifs"""
        return self.active_modules.copy()
    
    def get_suggestions(self, context_type: str) -> List[str]:
        """Retourne les suggestions pour un contexte"""
        suggestions = []
        
        for module_name in self.active_modules:
            module = self.loaded_modules.get(module_name)
            if module and hasattr(module, 'get_suggestions'):
                suggestions.extend(module.get_suggestions(context_type))
        
        return suggestions
    
    def process_line(self, line: str, context_type: str) -> dict:
        """Traite une ligne avec les modules actifs"""
        results = {
            'hardware': {},
            'commands': [],
            'alerts': []
        }
        
        for module_name in self.active_modules:
            module = self.loaded_modules.get(module_name)
            if module and hasattr(module, 'process_line'):
                module_result = module.process_line(line, context_type)
                
                if module_result:
                    results['hardware'].update(module_result.get('hardware', {}))
                    results['commands'].extend(module_result.get('commands', []))
                    results['alerts'].extend(module_result.get('alerts', []))
        
        return results
