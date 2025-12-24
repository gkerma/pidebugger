"""
Linux Module - Commandes et détection Linux
"""
import re
from .base_module import BaseModule

class LinuxModule(BaseModule):
    """Module Linux"""
    
    def __init__(self):
        super().__init__(
            name='linux_commands',
            context_types=['linux_kernel', 'linux_init', 'linux_shell']
        )
        
        self.commands = {
            'system': ['uname -a', 'uptime', 'hostname', 'date'],
            'process': ['ps aux', 'top', 'htop', 'pstree'],
            'network': ['ifconfig', 'ip addr', 'netstat -an', 'ss -tulpn'],
            'storage': ['df -h', 'mount', 'lsblk', 'fdisk -l'],
            'cpu': ['lscpu', 'cat /proc/cpuinfo'],
            'memory': ['free -h', 'cat /proc/meminfo', 'vmstat'],
            'packages': ['opkg list', 'opkg update'],
        }
    
    def get_suggestions(self, context_type: str) -> list:
        """Suggestions Linux"""
        if not self.is_compatible(context_type):
            return []
        
        suggestions = []
        suggestions.extend(self.commands['system'])
        suggestions.extend(self.commands['network'][:2])
        suggestions.extend(self.commands['storage'][:2])
        
        return suggestions
    
    def process_line(self, line: str, context_type: str) -> dict:
        """Traite une ligne Linux"""
        result = {
            'hardware': {},
            'commands': [],
            'alerts': []
        }
        
        # Version kernel
        match = re.search(r'Linux version ([\d.-]+)', line)
        if match:
            result['hardware']['kernel_version'] = match.group(1)
        
        # Architecture
        match = re.search(r'(aarch64|armv7|x86_64)', line, re.I)
        if match:
            result['hardware']['arch'] = match.group(1)
        
        return result if result['hardware'] else None
