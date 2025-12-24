"""
U-Boot Module - Commandes et détection U-Boot
"""
import re
from .base_module import BaseModule

class UbootModule(BaseModule):
    """Module U-Boot"""
    
    def __init__(self):
        super().__init__(
            name='uboot_commands',
            context_types=['uboot_spl', 'uboot_main']
        )
        
        self.commands = {
            'basic': ['help', 'version', 'bdinfo', 'coninfo'],
            'env': ['printenv', 'setenv', 'saveenv'],
            'memory': ['md', 'mm', 'mw', 'cp', 'cmp'],
            'boot': ['boot', 'bootm', 'bootp', 'bootelf'],
            'network': ['dhcp', 'ping', 'tftpboot'],
            'storage': ['mmc', 'usb', 'fatload', 'ext4load'],
        }
    
    def get_suggestions(self, context_type: str) -> list:
        """Suggestions U-Boot"""
        if not self.is_compatible(context_type):
            return []
        
        suggestions = []
        suggestions.extend(self.commands['basic'])
        suggestions.extend(self.commands['env'][:3])
        suggestions.extend(self.commands['boot'][:2])
        
        return suggestions
    
    def process_line(self, line: str, context_type: str) -> dict:
        """Traite une ligne U-Boot"""
        result = {
            'hardware': {},
            'commands': [],
            'alerts': []
        }
        
        # Version U-Boot
        match = re.search(r'U-Boot ([\d.]+)', line)
        if match:
            result['hardware']['uboot_version'] = match.group(1)
        
        # Board info
        match = re.search(r'Board: (.*?)$', line)
        if match:
            result['hardware']['board'] = match.group(1).strip()
        
        # SoC
        match = re.search(r'(Armada \d+|A[37]\d+)', line)
        if match:
            result['hardware']['soc'] = match.group(1)
        
        return result if result['hardware'] else None
