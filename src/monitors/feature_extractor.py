#!/usr/bin/env python3
"""
Feature Extractor for Hybrid AI-IDS
"""

import time
import numpy as np
import time
from collections import defaultdict
from scapy.all import IP, TCP, UDP
from dns_analyzer import DNSAnalyzer

class FlowFeatureExtractor:
    def __init__(self, flow_timeout=60):
        self.flows = defaultdict(dict)
        self.flow_timeout = flow_timeout
        self.dns_analyzer = DNSAnalyzer()
        
    def _get_flow_key(self, packet):
        """Generate bidirectional flow key"""
        if IP in packet:
            src, dst = packet[IP].src, packet[IP].dst
            proto = packet[IP].proto
            
            if TCP in packet:
                sport, dport = packet[TCP].sport, packet[TCP].dport
            elif UDP in packet:
                sport, dport = packet[UDP].sport, packet[UDP].dport
            else:
                sport, dport = 0, 0
            
            # Bidirectional key
            if (src, sport) < (dst, dport):
                return (src, dst, sport, dport, proto)
            else:
                return (dst, src, dport, sport, proto)
        return None

    def extract_features(self, packet):
        """Extract features from packet and return flow features"""
        flow_key = self._get_flow_key(packet)
        if not flow_key:
            return None
            
        current_time = time.time()
        
        # Initialize flow if new
        if 'start_time' not in self.flows[flow_key]:
            self.flows[flow_key] = {
                'start_time': current_time,
                'fwd_packets': [], 'bwd_packets': [],
                'fwd_bytes': 0, 'bwd_bytes': 0,
                'packet_lengths': [], 'iat_times': [],
                'flags': {'fin':0, 'syn':0, 'rst':0, 'psh':0, 'ack':0, 'urg':0, 'cwe':0, 'ece':0}
            }
        
        flow = self.flows[flow_key]
        
        # Determine direction
        if TCP in packet:
            is_forward = packet[TCP].sport == flow_key[2]
        elif UDP in packet:
            is_forward = packet[UDP].sport == flow_key[2]
        else:
            is_forward = True
            
        # Extract packet info
        packet_len = len(packet)
        flow['packet_lengths'].append(packet_len)
        
        # Update inter-arrival time
        if 'last_time' in flow:
            iat = current_time - flow['last_time']
            flow['iat_times'].append(iat)
        flow['last_time'] = current_time
        
        # Update direction-specific data
        if is_forward:
            flow['fwd_packets'].append(current_time)
            flow['fwd_bytes'] += packet_len
        else:
            flow['bwd_packets'].append(current_time)
            flow['bwd_bytes'] += packet_len
            
        # Update flags
        if TCP in packet:
            flags = packet[TCP].flags
            if flags & 0x01: flow['flags']['fin'] += 1
            if flags & 0x02: flow['flags']['syn'] += 1
            if flags & 0x04: flow['flags']['rst'] += 1
            if flags & 0x08: flow['flags']['psh'] += 1
            if flags & 0x10: flow['flags']['ack'] += 1
            if flags & 0x20: flow['flags']['urg'] += 1
            if flags & 0x40: flow['flags']['cwe'] += 1
            if flags & 0x80: flow['flags']['ece'] += 1
        
        # Calculate features
        return self._calculate_features(flow_key, packet)

    def _calculate_features(self, flow_key, packet):
        """Calculate all 78 features for the flow"""
        flow = self.flows[flow_key]
        current_time = time.time()
        
        # Basic features
        features = {}
        features['destination_port'] = flow_key[3] if flow_key[2] < flow_key[3] else flow_key[2]
        
        # Calculate all features
        features = {}
        
        # Basic flow features (existing)
        flow_duration = current_time - flow['start_time']
        features['flow_duration'] = flow_duration
        features['total_fwd_packets'] = len(flow['fwd_packets'])
        features['total_bwd_packets'] = len(flow['bwd_packets'])
        features['total_length_of_fwd_packets'] = flow['fwd_bytes']
        features['total_length_of_bwd_packets'] = flow['bwd_bytes']
        
        # DNS-specific features (NEW)
        dns_features = self.dns_analyzer.extract_dns_features(packet)
        features.update(dns_features)
        
        # DNS tunneling detection (NEW)
        if dns_features:
            tunneling_result = self.dns_analyzer.is_dns_tunneling(dns_features)
            features['dns_tunneling_score'] = tunneling_result['score']
            features['dns_tunneling_confidence'] = tunneling_result['confidence']
            features['is_dns_tunneling'] = tunneling_result['is_tunneling']
        else:
            features['dns_tunneling_score'] = 0
            features['dns_tunneling_confidence'] = 0
            features['is_dns_tunneling'] = False
        
        # Packet length statistics
        fwd_lengths = [packet_len for packet_len in flow['packet_lengths'] if flow['fwd_packets']] if flow['fwd_packets'] else [0]
        bwd_lengths = [packet_len for packet_len in flow['packet_lengths'] if flow['bwd_packets']] if flow['bwd_packets'] else [0]
        all_lengths = flow['packet_lengths'] if flow['packet_lengths'] else [0]
        
        features['fwd_packet_length_max'] = max(fwd_lengths) if fwd_lengths else 0
        features['fwd_packet_length_min'] = min(fwd_lengths) if fwd_lengths else 0
        features['fwd_packet_length_mean'] = np.mean(fwd_lengths) if fwd_lengths else 0
        features['fwd_packet_length_std'] = np.std(fwd_lengths) if len(fwd_lengths) > 1 else 0
        
        features['bwd_packet_length_max'] = max(bwd_lengths) if bwd_lengths else 0
        features['bwd_packet_length_min'] = min(bwd_lengths) if bwd_lengths else 0
        features['bwd_packet_length_mean'] = np.mean(bwd_lengths) if bwd_lengths else 0
        features['bwd_packet_length_std'] = np.std(bwd_lengths) if len(bwd_lengths) > 1 else 0
        
        # Flow rates
        if flow_duration > 0:
            features['flow_bytes/s'] = (flow['fwd_bytes'] + flow['bwd_bytes']) / flow_duration
            features['flow_packets/s'] = (features['total_fwd_packets'] + features['total_bwd_packets']) / flow_duration
        else:
            features['flow_bytes/s'] = 0
            features['flow_packets/s'] = 0
        
        # Inter-arrival times
        if flow['iat_times']:
            features['flow_iat_mean'] = np.mean(flow['iat_times'])
            features['flow_iat_std'] = np.std(flow['iat_times']) if len(flow['iat_times']) > 1 else 0
            features['flow_iat_max'] = max(flow['iat_times'])
            features['flow_iat_min'] = min(flow['iat_times'])
        else:
            features['flow_iat_mean'] = features['flow_iat_std'] = features['flow_iat_max'] = features['flow_iat_min'] = 0
        
        # Forward IAT
        fwd_iat = []
        if len(flow['fwd_packets']) > 1:
            fwd_iat = [flow['fwd_packets'][i] - flow['fwd_packets'][i-1] for i in range(1, len(flow['fwd_packets']))]
        
        features['fwd_iat_total'] = sum(fwd_iat)
        features['fwd_iat_mean'] = np.mean(fwd_iat) if fwd_iat else 0
        features['fwd_iat_std'] = np.std(fwd_iat) if len(fwd_iat) > 1 else 0
        features['fwd_iat_max'] = max(fwd_iat) if fwd_iat else 0
        features['fwd_iat_min'] = min(fwd_iat) if fwd_iat else 0
        
        # Backward IAT
        bwd_iat = []
        if len(flow['bwd_packets']) > 1:
            bwd_iat = [flow['bwd_packets'][i] - flow['bwd_packets'][i-1] for i in range(1, len(flow['bwd_packets']))]
        
        features['bwd_iat_total'] = sum(bwd_iat)
        features['bwd_iat_mean'] = np.mean(bwd_iat) if bwd_iat else 0
        features['bwd_iat_std'] = np.std(bwd_iat) if len(bwd_iat) > 1 else 0
        features['bwd_iat_max'] = max(bwd_iat) if bwd_iat else 0
        features['bwd_iat_min'] = min(bwd_iat) if bwd_iat else 0
        
        # Flags
        features['fwd_psh_flags'] = flow['flags']['psh']
        features['bwd_psh_flags'] = flow['flags']['psh']
        features['fwd_urg_flags'] = flow['flags']['urg']
        features['bwd_urg_flags'] = flow['flags']['urg']
        
        # Header lengths (approximate)
        features['fwd_header_length'] = features['total_fwd_packets'] * 40  # IP+TCP
        features['bwd_header_length'] = features['total_bwd_packets'] * 40
        
        # Packet rates
        if flow_duration > 0:
            features['fwd_packets/s'] = features['total_fwd_packets'] / flow_duration
            features['bwd_packets/s'] = features['total_bwd_packets'] / flow_duration
        else:
            features['fwd_packets/s'] = features['bwd_packets/s'] = 0
        
        # Packet length stats
        features['min_packet_length'] = min(all_lengths) if all_lengths else 0
        features['max_packet_length'] = max(all_lengths) if all_lengths else 0
        features['packet_length_mean'] = np.mean(all_lengths) if all_lengths else 0
        features['packet_length_std'] = np.std(all_lengths) if len(all_lengths) > 1 else 0
        features['packet_length_variance'] = features['packet_length_std'] ** 2
        
        # TCP flags
        features['fin_flag_count'] = flow['flags']['fin']
        features['syn_flag_count'] = flow['flags']['syn']
        features['rst_flag_count'] = flow['flags']['rst']
        features['psh_flag_count'] = flow['flags']['psh']
        features['ack_flag_count'] = flow['flags']['ack']
        features['urg_flag_count'] = flow['flags']['urg']
        features['cwe_flag_count'] = flow['flags']['cwe']
        features['ece_flag_count'] = flow['flags']['ece']
        
        # Ratios
        if features['total_length_of_bwd_packets'] > 0 and features['total_length_of_fwd_packets'] > 0:
            features['down/up_ratio'] = features['total_length_of_bwd_packets'] / features['total_length_of_fwd_packets']
        else:
            features['down/up_ratio'] = 0
            
        total_packets = features['total_fwd_packets'] + features['total_bwd_packets']
        features['average_packet_size'] = (flow['fwd_bytes'] + flow['bwd_bytes']) / total_packets if total_packets > 0 else 0
        features['avg_fwd_segment_size'] = features['total_length_of_fwd_packets'] / features['total_fwd_packets'] if features['total_fwd_packets'] > 0 else 0
        features['avg_bwd_segment_size'] = features['total_length_of_bwd_packets'] / features['total_bwd_packets'] if features['total_bwd_packets'] > 0 else 0
        
        # Additional features (set to 0 for simplicity)
        for f in ['fwd_header_length.1', 'fwd_avg_bytes/bulk', 'fwd_avg_packets/bulk', 'fwd_avg_bulk_rate',
                  'bwd_avg_bytes/bulk', 'bwd_avg_packets/bulk', 'bwd_avg_bulk_rate', 'subflow_fwd_packets',
                  'subflow_fwd_bytes', 'subflow_bwd_packets', 'subflow_bwd_bytes', 'init_win_bytes_forward',
                  'init_win_bytes_backward', 'act_data_pkt_fwd', 'min_seg_size_forward', 'active_mean',
                  'active_std', 'active_max', 'active_min', 'idle_mean', 'idle_std', 'idle_max', 'idle_min']:
            features[f] = 0
        
        return features

    def cleanup_old_flows(self):
        """Remove flows that have timed out"""
        current_time = time.time()
        expired_flows = []
        
        for flow_key, flow in self.flows.items():
            if current_time - flow.get('last_time', 0) > self.flow_timeout:
                expired_flows.append(flow_key)
        
        for flow_key in expired_flows:
            del self.flows[flow_key]
