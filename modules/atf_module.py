"""
ATF Module - ARM Trusted Firmware
"""
import re
from .base_module import BaseModule

class AtfModule(BaseModule):
    """Module ATF"""
    
    def __init__(self):
        super().__init__(
            name='atf_firmware',
            context_types=['atf_bl1', 'atf_bl2', 'atf_bl31', 'atf_bl33']
        )
    
    def get_suggestions(self, context_type: str) -> list:
        """Suggestions ATF (limitées)"""
        return []
    
    def process_line(self, line: str, context_type: str) -> dict:
        """Traite une ligne ATF"""
        result = {
            'hardware': {},
            'commands': [],
            'alerts': []
        }
        
        # Version ATF
        match = re.search(r'BL31: v([\d.]+)', line)
        if match:
            result['hardware']['atf_version'] = match.group(1)
        
        # Platform
        match = re.search(r'Platform: (.*?)$', line)
        if match:
            result['hardware']['platform'] = match.group(1).strip()
        
        return result if result['hardware'] else None
