#!/usr/bin/env python3
"""
Real-time Dashboard for the Hybrid AI-IDS
"""

import streamlit as st
import pandas as pd
import time

# --- Page Config ---
st.set_page_config(page_title="Hybrid AI-IDS Dashboard", layout="wide")

# --- Title ---
st.title("Hybrid AI-IDS Real-time Dashboard")

# --- Placeholders ---
placeholder = st.empty()

# --- Simulated Data Feed ---
# In a real application, this would connect to a message queue (like Kafka or RabbitMQ)
# or a database where alerts are stored by the real-time monitors.
def get_alerts():
    """Simulates receiving real-time alerts."""
    # This is a placeholder. Replace with actual alert fetching logic.
    alerts = [
        {'timestamp': pd.Timestamp.now(), 'attack_type': 'DDoS', 'confidence': 0.98, 'source_ip': '192.168.1.101'},
        {'timestamp': pd.Timestamp.now(), 'attack_type': 'Benign', 'confidence': 0.85, 'source_ip': '192.168.1.150'},
    ]
    time.sleep(2)
    return alerts

# --- Dashboard Loop ---
alerts_df = pd.DataFrame(columns=['timestamp', 'attack_type', 'confidence', 'source_ip'])

while True:
    new_alerts = get_alerts()
    new_alerts_df = pd.DataFrame(new_alerts)
    
    alerts_df = pd.concat([new_alerts_df, alerts_df], ignore_index=True)
    alerts_df = alerts_df.head(20) # Keep only the last 20 alerts

    with placeholder.container():
        st.header("Live Alerts")
        st.dataframe(alerts_df)

        st.header("Attack Type Distribution")
        attack_counts = alerts_df[alerts_df['attack_type'] != 'Benign']['attack_type'].value_counts()
        if not attack_counts.empty:
            st.bar_chart(attack_counts)
        else:
            st.write("No attacks detected yet.")

        st.header("Confidence Over Time")
        st.line_chart(alerts_df.set_index('timestamp')['confidence'])

        time.sleep(1)
