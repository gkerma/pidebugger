"""
Context Detector - Détection avancée du contexte système
"""
import re
from enum import Enum
from dataclasses import dataclass
from typing import Optional, List

class ContextType(Enum):
    """Types de contexte"""
    UNKNOWN = "unknown"
    BOOTROM = "bootrom"
    WTMI = "wtmi"
    ATF_BL1 = "atf_bl1"
    ATF_BL2 = "atf_bl2"
    ATF_BL31 = "atf_bl31"
    ATF_BL33 = "atf_bl33"
    UBOOT_SPL = "uboot_spl"
    UBOOT_MAIN = "uboot_main"
    LINUX_KERNEL = "linux_kernel"
    LINUX_INIT = "linux_init"
    LINUX_SHELL = "linux_shell"

@dataclass
class ContextInfo:
    """Informations de contexte"""
    type: ContextType
    prompt: Optional[str] = None
    version: Optional[str] = None
    hardware: dict = None
    
    def __post_init__(self):
        if self.hardware is None:
            self.hardware = {}

class ContextDetector:
    """Détecteur de contexte système"""
    
    # Patterns de détection par contexte
    PATTERNS = {
        ContextType.BOOTROM: [
            (r'BootROM', 1.0),
            (r'UART enabled', 0.9),
            (r'TIM-1\.0', 0.8),
        ],
        ContextType.WTMI: [
            (r'WTMI', 1.0),
            (r'wtmi_', 0.9),
            (r'WTP-01', 0.8),
        ],
        ContextType.ATF_BL1: [
            (r'NOTICE:\s+BL1:', 1.0),
            (r'Booting BL2', 0.9),
        ],
        ContextType.ATF_BL2: [
            (r'NOTICE:\s+BL2:', 1.0),
            (r'Booting BL31', 0.9),
        ],
        ContextType.ATF_BL31: [
            (r'NOTICE:\s+BL31:', 1.0),
            (r'BL31 runtime', 0.9),
            (r'BL31:', 0.7),
        ],
        ContextType.UBOOT_SPL: [
            (r'U-Boot SPL', 1.0),
            (r'spl_', 0.8),
        ],
        ContextType.UBOOT_MAIN: [
            (r'U-Boot 20\d\d', 1.0),
            (r'Marvell>>', 1.0),
            (r'=>', 0.6),
            (r'Hit any key', 0.7),
        ],
        ContextType.LINUX_KERNEL: [
            (r'Linux version', 1.0),
            (r'Booting Linux', 0.9),
            (r'Starting kernel', 0.9),
        ],
        ContextType.LINUX_INIT: [
            (r'systemd.*version', 0.9),
            (r'init:', 0.8),
            (r'rcS', 0.7),
        ],
        ContextType.LINUX_SHELL: [
            (r'login:', 1.0),
            (r'root@\w+.*[#\$]', 1.0),
            (r'[#\$]\s*$', 0.5),
        ],
    }
    
    # Patterns pour prompts
    PROMPT_PATTERNS = {
        ContextType.BOOTROM: r'(BootROM>)',
        ContextType.WTMI: r'(wtmi>)',
        ContextType.ATF_BL31: r'(BL31>)',
        ContextType.UBOOT_MAIN: r'(=>|Marvell>>)',
        ContextType.LINUX_SHELL: r'([\w-]+[@:][\w/~]+[#\$])',
    }
    
    def __init__(self):
        self.current_context = ContextInfo(type=ContextType.UNKNOWN)
        self.history: List[ContextInfo] = []
    
    def detect(self, line: str) -> Optional[ContextType]:
        """Détecte le contexte d'une ligne"""
        scores = {}
        
        for context_type, patterns in self.PATTERNS.items():
            score = 0.0
            for pattern, weight in patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    score += weight
            
            if score > 0:
                scores[context_type] = score
        
        if scores:
            return max(scores.items(), key=lambda x: x[1])[0]
        
        return None
    
    def update(self, line: str) -> bool:
        """Met à jour le contexte depuis une ligne"""
        detected = self.detect(line)
        
        if detected and detected != self.current_context.type:
            # Nouveau contexte
            new_context = ContextInfo(type=detected)
            
            # Extraire prompt
            prompt_pattern = self.PROMPT_PATTERNS.get(detected)
            if prompt_pattern:
                match = re.search(prompt_pattern, line)
                if match:
                    new_context.prompt = match.group(1)
            
            # Extraire version
            if detected == ContextType.UBOOT_MAIN:
                match = re.search(r'U-Boot ([\d.]+)', line)
                if match:
                    new_context.version = match.group(1)
            elif detected == ContextType.LINUX_KERNEL:
                match = re.search(r'Linux version ([\d.-]+)', line)
                if match:
                    new_context.version = match.group(1)
            
            self.history.append(self.current_context)
            self.current_context = new_context
            
            return True
        
        return False
    
    def get_context(self) -> ContextInfo:
        """Retourne le contexte actuel"""
        return self.current_context
    
    def get_history(self) -> List[ContextInfo]:
        """Retourne l'historique"""
        return self.history
