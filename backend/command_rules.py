"""Deterministic command evidence rules; no command execution or model loading."""
import re
from typing import Dict, List, Any

class CMDDetector:
    """Pattern matching engine for malicious command detection"""

    def __init__(self):
        self.patterns = {}
        self._initialize_patterns()

    def _initialize_patterns(self):
        """Initialize 47 regex patterns organized by severity"""

        # CRITICAL patterns (95%+ confidence)
        self.patterns['CRITICAL'] = [
            (r'cmd\s+/c\s+.*(?:powershell|pwsh).*-enc', 'Encoded PowerShell execution'),
            (r'powershell\s+(?:-e[nc]|-En|-Enc)', 'PowerShell encoded command'),
            (r'cmd\s+/c\s+powershell\s+-e[nc]', 'CMD PowerShell encoding'),
            (r'(?:certutil|bitsadmin|curl|wget).*(?:\.exe|\.dll|\.ps1|http)', 'Malware download attempt'),
            (r'certutil\s+(?:-download|-urlcache)', 'CertUtil download'),
            (r'bitsadmin\s+/transfer', 'BITS download'),
            (r'curl\s+(?:http|ftp).*\|.*(?:powershell|cmd)', 'Piped download'),
            (r'(?:mimikatz|rubeus|laZagne|procdump)', 'Credential stealing tool'),
            (r'cmd\s+/c\s+.*(?:lsass|ntds\.dit|sam)', 'Credential database access'),
            (r'dump.*(?:lsass|process|memory)', 'Memory dump attempt'),
            (r'reg\s+(?:add|import).*(?:SAM|SECURITY|SYSTEM|LSA)', 'Registry persistence'),
            (r'reg\s+(?:save|export).*(?:SAM|SECURITY|SYSTEM)', 'Registry dump'),
            (r'regedit\s+(?:/s|/c).*reg', 'Registry import'),
            (r'wmic\s+(?:process|service)\s+(?:delete|call\s+create)', 'WMIC deletion'),
            (r'taskkill\s+/f\s+/im\s+svchost', 'Force kill system process'),
            (r'sc\s+delete\s+\w+', 'Service deletion'),
            (r'(?:takeown|icacls)\s+.*\/grant', 'Privilege escalation'),
            (r'sc\s+(?:create|start)\s+\w+\s+binPath', 'Service creation for privilege'),
            (r'netsh\s+advfirewall\s+(?:set\s+allprofiles|firewall)\s+state\s+off', 'Firewall disable'),
            (r'netsh\s+firewall\s+set\s+opmode\s+disable', 'Firewall disable (old)'),
            (r'schtasks\s+/create.*\/tr', 'Scheduled task creation'),
            (r'at\s+\d+:\d+\s+(?:run|exec)', 'AT scheduler usage'),
        ]

        # HIGH patterns (70%+ confidence)
        self.patterns['HIGH'] = [
            (r'cmd\s+/c\s+.*(?:nc\.exe|ncat|netcat).*-e\s+(?:cmd|powershell)', 'Reverse shell'),
            (r'bash\s+-i\s+>.*&\s+1', 'Bash reverse shell'),
            (r'del\s+/s\s+/q\s+(?:[A-Z]:|\\)', 'Mass file deletion'),
            (r'cipher\s+/w:\s*', 'SSD wipe attempt'),
            (r'format\s+(?:[A-Z]:|\\)', 'Disk format'),
            (r'(?:ipconfig|netstat|arp)\s+.*>\s*\w+\.txt', 'Network recon to file'),
            (r'route\s+print.*>\s*', 'Routing recon'),
            (r'netsh\s+(?:advfirewall|firewall).*rule\s+', 'Firewall rule modification'),
            (r'net\s+user\s+\w+\s+\w+\s+/add', 'User account creation'),
            (r'net\s+localgroup\s+(?:administrators|admin)', 'Group privilege grant'),
            (r'psexec\s+-s', 'PsExec system execution'),
        ]

        # MEDIUM patterns (50%+ confidence)
        self.patterns['MEDIUM'] = [
            (r'powershell.*DownloadString', 'PowerShell download'),
            (r'powershell.*IEX', 'PowerShell invoke expression'),
            (r'powershell.*-NoProfile', 'PowerShell no profile'),
            (r'pspasswd\s+', 'PsPasswd usage'),
            (r'rar\s+(?:a|x).*-hp', 'RAR with hidden password'),
            (r'cmd\s+/c\s+(?:start|call).*>>.*&', 'CMD output redirection'),
            (r'powershell.*-WindowStyle\s+Hidden', 'Hidden PowerShell window'),
            (r'powershell.*-nop', 'PowerShell no profile (nop)'),
            (r'powershell.*-w\s+hidden', 'PowerShell hidden window'),
            (r'iex\s+', 'Invoke-Expression shorthand'),
        ]

        # LOW patterns (30% confidence)
        self.patterns['LOW'] = [
            (r'python\s+-c\s+', 'Python command execution'),
            (r'perl\s+-e\s+', 'Perl command execution'),
            (r'cscript\s+\w+\.vbs', 'VBScript execution'),
            (r'wscript\s+\w+\.vbs', 'Windows script host'),
        ]

    def detect(self, command: str) -> Dict[str, Any]:
        """Detect malicious patterns in a command"""
        command_lower = command.lower()

        for severity in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']:
            for pattern, description in self.patterns.get(severity, []):
                if re.search(pattern, command_lower, re.IGNORECASE):
                    return {
                        'is_malicious': True,
                        'severity': severity.lower(),
                        'confidence': self._get_confidence(severity),
                        'reason': f"{severity}: {description}",
                        'pattern': pattern,
                        'matched_pattern': description,
                        'method': 'regex'
                    }

        return {
            'is_malicious': False,
            'severity': 'unknown',
            'confidence': 0.0,
            'reason': 'No malicious patterns detected',
            'pattern': None,
            'matched_pattern': None,
            'method': 'regex'
        }

    def detect_batch(self, commands: List[str]) -> List[Dict[str, Any]]:
        """Detect malicious patterns in multiple commands"""
        return [self.detect(cmd) for cmd in commands]

    def _get_confidence(self, severity: str) -> float:
        """Get confidence score based on severity"""
        confidence_map = {
            'CRITICAL': 0.95,
            'HIGH': 0.75,
            'MEDIUM': 0.60,
            'LOW': 0.30
        }
        return confidence_map.get(severity, 0.0)

    def get_pattern_count(self) -> Dict[str, int]:
        """Get pattern statistics"""
        return {
            severity: len(patterns)
            for severity, patterns in self.patterns.items()
        }
