import re
import math
import base64
import time
import numpy as np
from scapy.all import DNS, DNSQR, UDP, Raw

class DNSAnalyzer:
    def __init__(self):
        self.dns_stats = {}
        self.domain_patterns = {}
        
    def extract_dns_features(self, packet):
        """Extract DNS-specific features for tunneling detection"""
        dns_layer = None
        query = None

        # Normal case: Scapy decoded DNS layers
        if DNS in packet and DNSQR in packet:
            dns_layer = packet[DNS]
            query = packet[DNSQR]
        else:
            # Fallback: UDP/53 but DNS not decoded (common on some Windows/Npcap setups)
            try:
                if UDP in packet and (int(packet[UDP].sport) == 53 or int(packet[UDP].dport) == 53):
                    # Raw payload may not be under Raw explicitly; bytes(payload) is safe
                    payload_bytes = bytes(packet[UDP].payload)
                    if payload_bytes:
                        parsed = DNS(payload_bytes)
                        if parsed is not None and getattr(parsed, 'qd', None) is not None:
                            dns_layer = parsed
                            query = parsed.qd
            except Exception:
                dns_layer = None
                query = None

        if dns_layer is None or query is None or getattr(query, 'qname', None) is None:
            return {}
        
        features = {}
        
        # Basic DNS features
        features['dns_query_length'] = len(query.qname.decode('utf-8', errors='ignore'))
        features['dns_query_type'] = query.qtype
        features['dns_response_code'] = int(getattr(dns_layer, 'rcode', 0) or 0)
        
        # Domain analysis
        domain = query.qname.decode('utf-8', errors='ignore').rstrip('.')
        features.update(self._analyze_domain_structure(domain))
        
        # Entropy analysis
        features.update(self._calculate_entropy_features(domain))
        
        # Encoding detection
        features.update(self._detect_encoding_patterns(domain))
        
        # Frequency analysis
        features.update(self._analyze_query_frequency(domain))
        
        # Subdomain analysis
        features.update(self._analyze_subdomains(domain))
        
        return features
    
    def _analyze_domain_structure(self, domain):
        """Analyze domain structure for tunneling patterns"""
        features = {}
        
        # Length characteristics
        features['domain_length'] = len(domain)
        features['subdomain_count'] = domain.count('.')
        features['max_subdomain_length'] = max(len(part) for part in domain.split('.')) if domain.split('.') else 0
        
        # Character distribution
        features['numeric_ratio'] = sum(c.isdigit() for c in domain) / len(domain) if domain else 0
        features['uppercase_ratio'] = sum(c.isupper() for c in domain) / len(domain) if domain else 0
        features['special_char_ratio'] = sum(not c.isalnum() and c != '.' for c in domain) / len(domain) if domain else 0
        
        return features
    
    def _calculate_entropy_features(self, domain):
        """Calculate entropy features - high entropy often indicates encoding"""
        features = {}
        
        # Shannon entropy
        char_counts = {}
        for char in domain:
            char_counts[char] = char_counts.get(char, 0) + 1
        
        entropy = 0
        for count in char_counts.values():
            prob = count / len(domain)
            entropy -= prob * math.log2(prob) if prob > 0 else 0
        
        features['domain_entropy'] = entropy
        
        # Subdomain entropy
        subdomains = domain.split('.')
        subdomain_entropies = []
        for subdomain in subdomains:
            if len(subdomain) > 3:  # Skip very short subdomains
                sub_counts = {}
                for char in subdomain:
                    sub_counts[char] = sub_counts.get(char, 0) + 1
                
                sub_entropy = 0
                for count in sub_counts.values():
                    prob = count / len(subdomain)
                    sub_entropy -= prob * math.log2(prob) if prob > 0 else 0
                
                subdomain_entropies.append(sub_entropy)
        
        features['avg_subdomain_entropy'] = np.mean(subdomain_entropies) if subdomain_entropies else 0
        features['max_subdomain_entropy'] = max(subdomain_entropies) if subdomain_entropies else 0
        
        return features
    
    def _detect_encoding_patterns(self, domain):
        """Detect common encoding patterns used in DNS tunneling"""
        features = {}
        
        # Base64 patterns
        try:
            # Try to decode subdomains as base64
            subdomains = domain.split('.')
            base64_count = 0
            for subdomain in subdomains:
                if len(subdomain) > 4 and len(subdomain) % 4 == 0:
                    try:
                        base64.b64decode(subdomain + '==')
                        base64_count += 1
                    except:
                        pass
            
            features['base64_subdomain_ratio'] = base64_count / len(subdomains) if subdomains else 0
        except:
            features['base64_subdomain_ratio'] = 0
        
        # Hex patterns
        hex_pattern = re.compile(r'^[0-9a-fA-F]+$')
        hex_subdomains = sum(1 for subdomain in domain.split('.') if hex_pattern.match(subdomain))
        features['hex_subdomain_ratio'] = hex_subdomains / len(domain.split('.')) if domain.split('.') else 0
        
        # Sequential patterns (a1b2c3, etc.)
        sequential_count = 0
        subdomains = domain.split('.')
        for subdomain in subdomains:
            if self._is_sequential_pattern(subdomain):
                sequential_count += 1
        
        features['sequential_subdomain_ratio'] = sequential_count / len(subdomains) if subdomains else 0
        
        return features
    
    def _is_sequential_pattern(self, text):
        """Check if text follows sequential patterns like a1b2c3"""
        if len(text) < 6:
            return False
        
        # Check for alternating letter-number pattern
        letter_number_pattern = re.compile(r'^([a-zA-Z][0-9])+$')
        if letter_number_pattern.match(text):
            return True
        
        # Check for consecutive characters
        consecutive_chars = 0
        for i in range(1, len(text)):
            if ord(text[i]) == ord(text[i-1]) + 1:
                consecutive_chars += 1
        
        return consecutive_chars >= len(text) * 0.7
    
    def _analyze_query_frequency(self, domain):
        """Analyze query frequency patterns"""
        features = {}
        
        # Get base domain (last two parts)
        parts = domain.split('.')
        if len(parts) >= 2:
            base_domain = '.'.join(parts[-2:])
            
            # Track query frequency
            current_time = time.time()
            if base_domain not in self.dns_stats:
                self.dns_stats[base_domain] = {'count': 0, 'timestamps': []}
            
            self.dns_stats[base_domain]['count'] += 1
            self.dns_stats[base_domain]['timestamps'].append(current_time)
            
            # Clean old timestamps (older than 60 seconds)
            self.dns_stats[base_domain]['timestamps'] = [
                ts for ts in self.dns_stats[base_domain]['timestamps'] 
                if current_time - ts < 60
            ]
            
            features['queries_per_minute'] = len(self.dns_stats[base_domain]['timestamps'])
            features['total_query_count'] = self.dns_stats[base_domain]['count']
        else:
            features['queries_per_minute'] = 0
            features['total_query_count'] = 0
        
        return features
    
    def _analyze_subdomains(self, domain):
        """Analyze subdomain patterns"""
        features = {}
        
        subdomains = domain.split('.')
        
        # Subdomain length statistics
        if subdomains:
            lengths = [len(sub) for sub in subdomains]
            features['avg_subdomain_length'] = np.mean(lengths)
            features['max_subdomain_length'] = max(lengths)
            features['min_subdomain_length'] = min(lengths)
            features['subdomain_length_std'] = np.std(lengths)
        else:
            features['avg_subdomain_length'] = 0
            features['max_subdomain_length'] = 0
            features['min_subdomain_length'] = 0
            features['subdomain_length_std'] = 0
        
        # Unique subdomain ratio
        features['unique_subdomain_ratio'] = len(set(subdomains)) / len(subdomains) if subdomains else 0
        
        return features
    
    def is_dns_tunneling(self, features):
        """Determine if DNS query looks like tunneling"""
        score = 0
        reasons = []
        
        # High entropy subdomains (lowered threshold)
        if features.get('max_subdomain_entropy', 0) > 3.5:
            score += 2
            reasons.append("High entropy subdomains")
        
        # Very long domain names (lowered threshold)
        if features.get('domain_length', 0) > 80:
            score += 2
            reasons.append("Very long domain name")
        
        # High query frequency (lowered threshold)
        if features.get('queries_per_minute', 0) > 20:
            score += 2
            reasons.append("High query frequency")
        
        # Base64 encoding detected (lowered threshold)
        if features.get('base64_subdomain_ratio', 0) > 0.2:
            score += 3
            reasons.append("Base64 encoding detected")
        
        # Hex encoding detected (lowered threshold)
        if features.get('hex_subdomain_ratio', 0) > 0.3:
            score += 2
            reasons.append("Hex encoding detected")
        
        # Many subdomains (lowered threshold)
        if features.get('subdomain_count', 0) > 3:
            score += 1
            reasons.append("Many subdomains")
        
        # Sequential patterns
        if features.get('sequential_subdomain_ratio', 0) > 0.2:
            score += 2
            reasons.append("Sequential patterns detected")
        
        # Long average subdomain length
        if features.get('avg_subdomain_length', 0) > 25:
            score += 1
            reasons.append("Long subdomains")
        
        return {
            'is_tunneling': score >= 3,  # Lowered threshold from 4 to 3
            'score': score,
            'confidence': min(score / 6.0, 1.0),  # Adjusted max score
            'reasons': reasons
        }
