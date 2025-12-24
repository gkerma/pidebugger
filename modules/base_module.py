"""
Base Module - Classe de base pour tous les modules
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Optional

class BaseModule(ABC):
    """Classe de base pour modules"""
    
    def __init__(self, name: str, context_types: List[str]):
        self.name = name
        self.context_types = context_types
        self.enabled = True
    
    @abstractmethod
    def get_suggestions(self, context_type: str) -> List[str]:
        """Retourne les suggestions pour un contexte"""
        pass
    
    @abstractmethod
    def process_line(self, line: str, context_type: str) -> Optional[Dict]:
        """Traite une ligne et extrait des infos"""
        pass
    
    def is_compatible(self, context_type: str) -> bool:
        """Vérifie si le module est compatible avec le contexte"""
        return context_type in self.context_types
