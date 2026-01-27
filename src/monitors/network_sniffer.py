#!/usr/bin/env python3
"""
Real-time Network Sniffer for Hybrid AI-IDS
"""

import pyshark
import pyshark
import aiohttp
import socketio
import time
import asyncio
import sys

API_URL = 'http://127.0.0.1:5000/predict'
SIO_URL = 'http://127.0.0.1:5000'

# --- Async Socket.IO Client ---
sio = socketio.AsyncClient()

@sio.event
async def connect():
    print('Connected to server')

@sio.event
async def disconnect():
    print('Disconnected from server')

def packet_to_features(packet):
    """Converts a pyshark packet to a feature dictionary and a summary."""
    try:
        # Simplified feature extraction for prediction
        features = {
            'dst_port': int(packet.tcp.dstport),
            'protocol': 6, # TCP
            # Add other features required by the model
        }

        # Summarized data for dashboard display
        summary = {
            'timestamp': packet.sniff_time.isoformat(),
            'src': packet.ip.src,
            'dst': packet.ip.dst,
            'protocol': packet.transport_layer,
            'length': int(packet.length),
        }
        return features, summary
    except AttributeError:
        return None, None

async def async_sniffer(main_loop, session):
    """This function runs in a separate thread with its own event loop."""
    # Set the event loop policy for this new thread
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    # pyshark will now find this loop when it's initialized
    capture = pyshark.LiveCapture(interface='Ethernet')
    try:
        for packet in capture.sniff_continuously():
            features, summary = packet_to_features(packet)
            if summary:
                # Schedule the async emit on the main event loop
                asyncio.run_coroutine_threadsafe(sio.emit('stream_packet', summary), main_loop)
            if features:
                # Schedule the async post on the main event loop
                # Note: We can't pass the aiohttp session object directly.
                # Instead, we'll pass the URL and let the main loop handle the request.
                # For simplicity, we'll just print for now.
                print(f"Captured features for prediction: {features}")
                # In a real scenario, you'd set up a queue or another thread-safe communication.
    except Exception as e:
        print(f"An error occurred in the sniffer thread: {e}")

def run_sniffer_in_thread(main_loop):
    """Starts the new event loop and runs the sniffer coroutine in it."""
    # Manually create and set the event loop for this thread
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        loop.run_until_complete(async_sniffer(main_loop, None))
    finally:
        loop.close()

async def main():
    """Sets up the async environment and runs the sniffer in a separate thread."""
    print("Starting real-time network sniffer...")
    main_loop = asyncio.get_running_loop()

    try:
        await sio.connect(SIO_URL)
    except socketio.exceptions.ConnectionError as e:
        print(f"Could not connect to WebSocket server: {e}")
        return

    # Start the sniffer in its own thread with its own event loop
    import threading
    sniffer_thread = threading.Thread(target=run_sniffer_in_thread, args=(main_loop,))
    sniffer_thread.start()

    try:
        # Keep the main loop running to handle WebSocket events
        while sniffer_thread.is_alive():
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping sniffer...")
    finally:
        if sio.connected:
            await sio.disconnect()
        # Note: The sniffer thread will be stopped abruptly on exit.
        # A graceful shutdown would require a more complex signaling mechanism.

if __name__ == '__main__':
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
