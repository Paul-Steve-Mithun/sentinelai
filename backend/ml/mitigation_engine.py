"""
Mitigation strategy engine
Generates actionable mitigation recommendations based on detected anomalies
"""
from typing import List, Dict


class MitigationEngine:
    """
    Generates mitigation strategies for detected threats
    """
    
    def __init__(self):
        # Define mitigation templates by anomaly type
        self.mitigation_templates = {
            'unusual_login_time': [
                {
                    'priority': 1,
                    'category': 'immediate',
                    'action': 'Verify employee activity',
                    'description': 'Contact employee to confirm the login was legitimate'
                },
                {
                    'priority': 2,
                    'category': 'immediate',
                    'action': 'Review access logs',
                    'description': 'Check all activities performed during the unusual login session'
                },
                {
                    'priority': 3,
                    'category': 'short_term',
                    'action': 'Enable MFA alerts',
                    'description': 'Configure alerts for logins outside normal hours'
                }
            ],
            'location_variance': [
                {
                    'priority': 1,
                    'category': 'immediate',
                    'action': 'Verify location',
                    'description': 'Confirm employee is traveling or working from new location'
                },
                {
                    'priority': 2,
                    'category': 'immediate',
                    'action': 'Check for VPN usage',
                    'description': 'Verify if location change is due to VPN or proxy'
                },
                {
                    'priority': 3,
                    'category': 'short_term',
                    'action': 'Implement geo-fencing',
                    'description': 'Set up alerts for logins from unexpected geographic locations'
                }
            ],
            'unusual_port': [
                {
                    'priority': 1,
                    'category': 'immediate',
                    'action': 'Block suspicious port',
                    'description': 'Temporarily block the unusual port pending investigation'
                },
                {
                    'priority': 2,
                    'category': 'immediate',
                    'action': 'Analyze network traffic',
                    'description': 'Review all traffic on the unusual port for malicious activity'
                },
                {
                    'priority': 3,
                    'category': 'short_term',
                    'action': 'Update firewall rules',
                    'description': 'Restrict port access to authorized users only'
                }
            ],
            'sensitive_file_access': [
                {
                    'priority': 1,
                    'category': 'immediate',
                    'action': 'Review file access',
                    'description': 'Audit which sensitive files were accessed and why'
                },
                {
                    'priority': 1,
                    'category': 'immediate',
                    'action': 'Check for data exfiltration',
                    'description': 'Monitor for unusual data transfers or downloads'
                },
                {
                    'priority': 2,
                    'category': 'short_term',
                    'action': 'Restrict file permissions',
                    'description': 'Review and tighten access controls on sensitive files'
                },
                {
                    'priority': 3,
                    'category': 'long_term',
                    'action': 'Implement DLP',
                    'description': 'Deploy Data Loss Prevention tools to monitor sensitive data'
                }
            ],
            'privilege_escalation': [
                {
                    'priority': 1,
                    'category': 'immediate',
                    'action': 'Suspend elevated privileges',
                    'description': 'Temporarily revoke sudo/admin access pending investigation'
                },
                {
                    'priority': 1,
                    'category': 'immediate',
                    'action': 'Review privilege usage',
                    'description': 'Audit all commands executed with elevated privileges'
                },
                {
                    'priority': 2,
                    'category': 'short_term',
                    'action': 'Implement privilege monitoring',
                    'description': 'Set up real-time alerts for privilege escalation attempts'
                },
                {
                    'priority': 3,
                    'category': 'long_term',
                    'action': 'Apply least privilege principle',
                    'description': 'Review and minimize privilege assignments across organization'
                }
            ],
            'firewall_change': [
                {
                    'priority': 1,
                    'category': 'immediate',
                    'action': 'Revert firewall changes',
                    'description': 'Roll back unauthorized firewall rule modifications'
                },
                {
                    'priority': 1,
                    'category': 'immediate',
                    'action': 'Investigate change reason',
                    'description': 'Determine why firewall rules were modified'
                },
                {
                    'priority': 2,
                    'category': 'short_term',
                    'action': 'Restrict firewall access',
                    'description': 'Limit firewall configuration access to security team only'
                },
                {
                    'priority': 3,
                    'category': 'long_term',
                    'action': 'Implement change management',
                    'description': 'Require approval workflow for all firewall changes'
                }
            ],
            'failed_login': [
                {
                    'priority': 1,
                    'category': 'immediate',
                    'action': 'Lock account temporarily',
                    'description': 'Prevent further login attempts to protect account'
                },
                {
                    'priority': 2,
                    'category': 'immediate',
                    'action': 'Contact employee',
                    'description': 'Verify if employee is having login issues or if account is compromised'
                },
                {
                    'priority': 2,
                    'category': 'short_term',
                    'action': 'Force password reset',
                    'description': 'Require employee to reset password with strong requirements'
                },
                {
                    'priority': 3,
                    'category': 'short_term',
                    'action': 'Enable account monitoring',
                    'description': 'Set up enhanced monitoring for this account'
                }
            ],
            'network_activity': [
                {
                    'priority': 1,
                    'category': 'immediate',
                    'action': 'Analyze traffic patterns',
                    'description': 'Review network logs for signs of data exfiltration'
                },
                {
                    'priority': 2,
                    'category': 'immediate',
                    'action': 'Check for malware',
                    'description': 'Scan employee workstation for malware or backdoors'
                },
                {
                    'priority': 3,
                    'category': 'short_term',
                    'action': 'Implement bandwidth limits',
                    'description': 'Set reasonable bandwidth limits for user accounts'
                }
            ],
            'night_activity': [
                {
                    'priority': 1,
                    'category': 'immediate',
                    'action': 'Verify employee activity',
                    'description': 'Confirm if employee was working late or if account is compromised'
                },
                {
                    'priority': 2,
                    'category': 'short_term',
                    'action': 'Review activities performed',
                    'description': 'Audit all actions taken during off-hours'
                },
                {
                    'priority': 3,
                    'category': 'short_term',
                    'action': 'Set up off-hours alerts',
                    'description': 'Configure notifications for activity outside business hours'
                }
            ],
            'high_cpu_usage': [
                {
                    'priority': 1,
                    'category': 'immediate',
                    'action': 'Investigate running processes',
                    'description': 'Identify processes consuming high CPU (potential crypto miner)'
                },
                {
                    'priority': 2,
                    'category': 'immediate',
                    'action': 'Scan for malware',
                    'description': 'Run deep system scan for resource hijacking malware'
                },
                {
                    'priority': 3,
                    'category': 'short_term',
                    'action': 'Kill suspicious process',
                    'description': 'Terminate any unauthorized high-resource processes'
                }
            ],
            'high_memory_usage': [
                {
                    'priority': 1,
                    'category': 'immediate',
                    'action': 'Check for memory leaks/bloat',
                    'description': 'Identify applications using excessive memory'
                },
                {
                    'priority': 2,
                    'category': 'immediate',
                    'action': 'Scan for memory-resident malware',
                    'description': 'Check for malware injecting into legitimate processes'
                }
            ]
        }
        
        # Default mitigation for unknown anomaly types
        self.default_mitigations = [
            {
                'priority': 1,
                'category': 'immediate',
                'action': 'Investigate anomaly',
                'description': 'Review the detected anomaly and gather more context'
            },
            {
                'priority': 2,
                'category': 'immediate',
                'action': 'Contact employee',
                'description': 'Verify the unusual behavior with the employee'
            },
            {
                'priority': 3,
                'category': 'short_term',
                'action': 'Monitor account',
                'description': 'Enable enhanced monitoring for this employee account'
            }
        ]
    
    def generate_strategies(
        self,
        anomaly_type: str,
        risk_level: str,
        mitre_techniques: List[Dict] = None
    ) -> List[Dict]:
        """
        Generate mitigation strategies for an anomaly
        
        Args:
            anomaly_type: Type of anomaly detected
            risk_level: Risk level (low, medium, high, critical)
            mitre_techniques: List of mapped MITRE techniques
            
        Returns:
            List of mitigation strategies
        """
        # Get base strategies for anomaly type
        strategies = self.mitigation_templates.get(anomaly_type, self.default_mitigations.copy())
        
        # Make a copy to avoid modifying templates
        strategies = [s.copy() for s in strategies]
        
        # Adjust priorities based on risk level
        if risk_level == 'critical':
            # Add urgent response for critical threats
            strategies.insert(0, {
                'priority': 1,
                'category': 'immediate',
                'action': 'Escalate to security team',
                'description': 'CRITICAL: Immediately notify security operations center'
            })
        elif risk_level == 'high':
            strategies.insert(0, {
                'priority': 1,
                'category': 'immediate',
                'action': 'Alert security team',
                'description': 'HIGH RISK: Notify security team for immediate review'
            })
        
        # Add MITRE-specific mitigations if available
        if mitre_techniques:
            for technique in mitre_techniques[:2]:  # Top 2 techniques
                mitre_strategy = self._get_mitre_mitigation(technique)
                if mitre_strategy:
                    strategies.append(mitre_strategy)
        
        # Re-sort by priority
        strategies.sort(key=lambda x: x['priority'])
        
        return strategies
    
    def _get_mitre_mitigation(self, technique: Dict) -> Dict:
        """
        Get mitigation strategy specific to MITRE technique
        
        Args:
            technique: MITRE technique dictionary
            
        Returns:
            Mitigation strategy or None
        """
        technique_id = technique.get('technique_id')
        
        mitre_mitigations = {
            'T1078': {
                'priority': 2,
                'category': 'short_term',
                'action': 'Implement MFA',
                'description': 'Enable multi-factor authentication to prevent credential abuse'
            },
            'T1021': {
                'priority': 2,
                'category': 'short_term',
                'action': 'Restrict remote access',
                'description': 'Limit remote service access to authorized users and IPs'
            },
            'T1068': {
                'priority': 1,
                'category': 'immediate',
                'action': 'Patch vulnerabilities',
                'description': 'Apply security patches to prevent privilege escalation exploits'
            },
            'T1048': {
                'priority': 1,
                'category': 'immediate',
                'action': 'Monitor data transfers',
                'description': 'Implement network monitoring to detect data exfiltration'
            },
            'T1562': {
                'priority': 1,
                'category': 'immediate',
                'action': 'Restore security controls',
                'description': 'Re-enable any disabled security mechanisms'
            },
            'T1530': {
                'priority': 2,
                'category': 'short_term',
                'action': 'Audit cloud access',
                'description': 'Review and restrict cloud storage access permissions'
            },
            'T1496': {
                'priority': 1,
                'category': 'immediate',
                'action': 'Isolate and Clean',
                'description': 'Disconnect from network and remove crypto-mining malware'
            }
        }
        
        return mitre_mitigations.get(technique_id)
    
    def get_compliance_recommendations(self, anomaly_type: str) -> List[str]:
        """
        Get compliance-related recommendations
        
        Args:
            anomaly_type: Type of anomaly
            
        Returns:
            List of compliance recommendations
        """
        compliance_map = {
            'sensitive_file_access': [
                'Document incident per GDPR Article 33 (breach notification)',
                'Review compliance with SOC 2 access controls',
                'Ensure HIPAA audit trail requirements are met'
            ],
            'privilege_escalation': [
                'Review against PCI DSS requirement 7 (access control)',
                'Document for SOC 2 CC6.1 (logical access controls)',
                'Verify compliance with ISO 27001 A.9.2.3'
            ],
            'failed_login': [
                'Check NIST 800-53 AC-7 (unsuccessful login attempts)',
                'Review against CIS Controls 16.11',
                'Document per SOC 2 CC6.1'
            ]
        }
        
        return compliance_map.get(anomaly_type, [
            'Document incident in security log',
            'Review against organizational security policies'
        ])
