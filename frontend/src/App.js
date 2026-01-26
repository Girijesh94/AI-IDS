import React, { useState, useEffect } from 'react';
import io from 'socket.io-client';

const SOCKET_URL = 'http://localhost:5000';

function App() {
  const [packets, setPackets] = useState([]);
  const [alerts, setAlerts] = useState([]);

  useEffect(() => {
    const socket = io(SOCKET_URL);

    socket.on('connect', () => {
      console.log('Connected to WebSocket server');
    });

    socket.on('new_packet', (packet) => {
      setPackets(prevPackets => [packet, ...prevPackets].slice(0, 50)); // Keep last 50 packets
    });

    socket.on('new_alert', (alert) => {
      setAlerts(prevAlerts => [alert, ...prevAlerts].slice(0, 20)); // Keep last 20 alerts
    });

    return () => {
      socket.disconnect();
    };
  }, []);

  return (
    <div className="bg-gray-900 text-white min-h-screen font-mono">
      <header className="bg-gray-800 p-4 text-center">
        <h1 className="text-2xl font-bold">Hybrid AI-IDS Dashboard</h1>
      </header>
      <main className="flex p-4 space-x-4">
        {/* Live Packet Feed */}
        <div className="w-3/4 bg-gray-800 p-4 rounded-lg">
          <h2 className="text-xl font-semibold mb-4 border-b border-gray-700 pb-2">Live Network Traffic</h2>
          <div className="overflow-y-auto h-[80vh]">
            <table className="w-full text-sm text-left">
              <thead className="text-xs text-gray-400 uppercase bg-gray-700">
                <tr>
                  <th scope="col" className="px-6 py-3">Timestamp</th>
                  <th scope="col" className="px-6 py-3">Source</th>
                  <th scope="col" className="px-6 py-3">Destination</th>
                  <th scope="col" className="px-6 py-3">Protocol</th>
                  <th scope="col" className="px-6 py-3">Length</th>
                </tr>
              </thead>
              <tbody>
                {packets.map((p, i) => (
                  <tr key={i} className="bg-gray-800 border-b border-gray-700 hover:bg-gray-600">
                    <td className="px-6 py-4">{new Date(p.timestamp).toLocaleTimeString()}</td>
                    <td className="px-6 py-4">{p.src}</td>
                    <td className="px-6 py-4">{p.dst}</td>
                    <td className="px-6 py-4">{p.protocol}</td>
                    <td className="px-6 py-4">{p.length}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Alerts Sidebar */}
        <div className="w-1/4 bg-gray-800 p-4 rounded-lg">
          <h2 className="text-xl font-semibold mb-4 border-b border-gray-700 pb-2">Real-time Alerts</h2>
          <div className="overflow-y-auto h-[80vh]">
            {alerts.map((a, i) => (
              <div key={i} className={`p-3 mb-2 rounded-lg ${a.prediction === 1 ? 'bg-red-800' : 'bg-yellow-800'}`}>
                <p className="font-bold">Attack Detected!</p>
                <p>Type: {a.prediction}</p>
                <p>Confidence: {a.confidence.toFixed(2)}</p>
                <p className="text-xs mt-1">Source Port: {a.dst_port}</p>
              </div>
            ))}
          </div>
        </div>
      </main>
    </div>
  );
}

export default App;

