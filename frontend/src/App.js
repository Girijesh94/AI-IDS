import React, { useState, useEffect } from 'react';
import io from 'socket.io-client';

const SOCKET_URL = 'http://localhost:5000';

function App() {
  const [packets, setPackets] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [logs, setLogs] = useState([]);
  const [isRunning, setIsRunning] = useState(true);
  const [stats, setStats] = useState({
    totalPackets: 0,
    suspiciousPackets: 0,
    maliciousPackets: 0,
    activeConnections: 0,
    alerts: 0,
    bandwidth: 0
  });

  useEffect(() => {
    const socket = io(SOCKET_URL);

    socket.on('connect', () => {
      console.log('Connected to WebSocket server');
      // Add initial log when connected
      setLogs(prev => [{
        id: Math.random().toString(36).substr(2, 9),
        timestamp: new Date().toISOString(),
        level: 'INFO',
        message: 'WebSocket connection established'
      }, ...prev]);
    });

    socket.on('new_packet', (packet) => {
      const newPacket = {
        ...packet,
        id: Math.random().toString(36).substr(2, 9),
        packet_id: packet.packet_id,
        destination_port: packet.destination_port,
        status: packet.status,
        size: parseInt(packet.length) || 1024,
        timestamp: new Date().toISOString()
      };
      
      setPackets(prevPackets => [newPacket, ...prevPackets].slice(0, 100));
      
      setStats(prev => ({
        totalPackets: prev.totalPackets + 1,
        suspiciousPackets: prev.suspiciousPackets,
        maliciousPackets: prev.maliciousPackets,
        activeConnections: Math.max(10, prev.activeConnections + (Math.random() > 0.5 ? 1 : -1)),
        alerts: prev.alerts,
        bandwidth: prev.bandwidth + (newPacket.size / 1024 / 1024)
      }));
    });

    socket.on('classification', (cls) => {
      const status = cls.status || 'normal';
      const packetId = cls.packet_id;

      // Update packet row if we can correlate
      if (packetId) {
        setPackets(prev => prev.map(p => {
          if (p.packet_id && p.packet_id === packetId) {
            return {
              ...p,
              status,
              confidence: cls.confidence,
              prediction: cls.prediction,
              destination_port: cls.destination_port ?? p.destination_port,
            };
          }
          return p;
        }));
      }

      // Update counters + alerts
      if (status === 'suspicious' || status === 'malicious') {
        setStats(prev => ({
          ...prev,
          suspiciousPackets: prev.suspiciousPackets + (status === 'suspicious' ? 1 : 0),
          maliciousPackets: prev.maliciousPackets + (status === 'malicious' ? 1 : 0),
          alerts: prev.alerts + 1,
        }));

        setAlerts(prev => {
          const alert = {
            id: packetId || Math.random().toString(36).substr(2, 9),
            timestamp: new Date().toISOString(),
            message: `${status.toUpperCase()} traffic detected from ${cls.src || 'unknown'} (port ${cls.destination_port ?? 'unknown'})`,
            severity: status === 'malicious' ? 'high' : 'medium',
            confidence: cls.confidence,
            packet_id: packetId,
          };
          return [alert, ...prev].slice(0, 50);
        });
      }
    });

    socket.on('system_log', (log) => {
      const newLog = {
        ...log,
        id: Math.random().toString(36).substr(2, 9)
      };
      setLogs(prevLogs => [newLog, ...prevLogs].slice(0, 50));
    });

    return () => {
      socket.disconnect();
    };
  }, []);

  const dismissAlert = (id) => {
    setAlerts(prev => prev.filter(alert => alert.id !== id));
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 shadow-sm">
        <div className="max-w-[1920px] mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="bg-gradient-to-br from-blue-600 to-cyan-600 p-2 rounded-lg">
                <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                </svg>
              </div>
              <div>
                <h1 className="text-2xl font-bold text-gray-900">
                  Intrusion Detection System
                </h1>
                <p className="text-sm text-gray-500">
                  Real-time network monitoring and threat detection
                </p>
              </div>
            </div>
            <button
              onClick={() => setIsRunning(!isRunning)}
              className={`flex items-center space-x-2 px-4 py-2 rounded-lg font-semibold transition-all ${
                isRunning
                  ? 'bg-red-500 hover:bg-red-600 text-white'
                  : 'bg-green-500 hover:bg-green-600 text-white'
              }`}
            >
              {isRunning ? (
                <>
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 9v6m4-6v6m7-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <span>Pause</span>
                </>
              ) : (
                <>
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <span>Resume</span>
                </>
              )}
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-[1920px] mx-auto px-6 py-6">
        {/* Statistics Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-6">
          <div className="bg-white rounded-xl shadow-sm p-6 border border-gray-200">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Total Packets</p>
                <p className="text-2xl font-bold text-gray-900">{stats.totalPackets.toLocaleString()}</p>
              </div>
              <div className="bg-blue-100 p-3 rounded-lg">
                <svg className="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                </svg>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-xl shadow-sm p-6 border border-gray-200">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Suspicious</p>
                <p className="text-2xl font-bold text-yellow-600">{stats.suspiciousPackets.toLocaleString()}</p>
              </div>
              <div className="bg-yellow-100 p-3 rounded-lg">
                <svg className="w-6 h-6 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
                </svg>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-xl shadow-sm p-6 border border-gray-200">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Malicious</p>
                <p className="text-2xl font-bold text-red-600">{stats.maliciousPackets.toLocaleString()}</p>
              </div>
              <div className="bg-red-100 p-3 rounded-lg">
                <svg className="w-6 h-6 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-xl shadow-sm p-6 border border-gray-200">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Active Alerts</p>
                <p className="text-2xl font-bold text-purple-600">{alerts.length}</p>
              </div>
              <div className="bg-purple-100 p-3 rounded-lg">
                <svg className="w-6 h-6 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
                </svg>
              </div>
            </div>
          </div>
        </div>

        {/* Main Content Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Network Traffic */}
          <div className="lg:col-span-2">
            <div className="bg-white rounded-xl shadow-sm border border-gray-200">
              <div className="px-6 py-4 border-b border-gray-200">
                <h2 className="text-lg font-semibold text-gray-900">Network Traffic</h2>
              </div>
              <div className="p-6">
                <div className="overflow-x-auto">
                  <table className="min-w-full">
                    <thead>
                      <tr className="text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        <th className="pb-3">Source</th>
                        <th className="pb-3">Destination</th>
                        <th className="pb-3">Protocol</th>
                        <th className="pb-3">Size</th>
                        <th className="pb-3">Status</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-200">
                      {packets.slice(0, 10).map((packet) => (
                        <tr key={packet.id} className="hover:bg-gray-50">
                          <td className="py-3 text-sm text-gray-900">{packet.src}</td>
                          <td className="py-3 text-sm text-gray-900">{packet.dst}</td>
                          <td className="py-3 text-sm text-gray-900">{packet.protocol}</td>
                          <td className="py-3 text-sm text-gray-900">{packet.size}B</td>
                          <td className="py-3">
                            <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                              packet.status === 'normal' || !packet.status ? 'bg-green-100 text-green-800' :
                              packet.status === 'suspicious' ? 'bg-yellow-100 text-yellow-800' :
                              'bg-red-100 text-red-800'
                            }`}>
                              {packet.status || 'normal'}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          </div>

          {/* System Logs */}
          <div className="lg:col-span-1">
            <div className="bg-white rounded-xl shadow-sm border border-gray-200">
              <div className="px-6 py-4 border-b border-gray-200">
                <h2 className="text-lg font-semibold text-gray-900">System Logs</h2>
              </div>
              <div className="p-6">
                <div className="space-y-3">
                  {logs.length === 0 ? (
                    <div className="flex items-start space-x-3">
                      <div className="w-2 h-2 bg-gray-400 rounded-full mt-2"></div>
                      <div className="flex-1">
                        <p className="text-sm text-gray-900">Waiting for system events...</p>
                        <p className="text-xs text-gray-500">Just now</p>
                      </div>
                    </div>
                  ) : (
                    logs.slice(0, 10).map((log) => (
                      <div key={log.id} className="flex items-start space-x-3">
                        <div className={`w-2 h-2 rounded-full mt-2 ${
                          log.level === 'INFO' ? 'bg-green-400' :
                          log.level === 'WARNING' ? 'bg-yellow-400' :
                          log.level === 'ERROR' ? 'bg-red-400' :
                          'bg-blue-400'
                        }`}></div>
                        <div className="flex-1">
                          <p className="text-sm text-gray-900">{log.message}</p>
                          <p className="text-xs text-gray-500">
                            {new Date(log.timestamp).toLocaleTimeString()}
                          </p>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>
      </main>

      {/* Alerts Panel */}
      {alerts.length > 0 && (
        <div className="fixed bottom-6 right-6 max-w-md">
          <div className="bg-white rounded-xl shadow-lg border border-gray-200 p-4">
            <div className="flex items-center justify-between mb-3">
              <h3 className="font-semibold text-gray-900">Security Alerts</h3>
              <span className="bg-red-100 text-red-800 text-xs font-semibold px-2 py-1 rounded-full">
                {alerts.length}
              </span>
            </div>
            <div className="space-y-2 max-h-64 overflow-y-auto">
              {alerts.slice(0, 3).map((alert) => (
                <div key={alert.id} className="border-l-4 border-red-400 bg-red-50 p-3">
                  <div className="flex justify-between items-start">
                    <div>
                      <p className="text-sm font-medium text-red-800">{alert.message}</p>
                      <p className="text-xs text-red-600 mt-1">
                        {new Date(alert.timestamp).toLocaleTimeString()}
                      </p>
                    </div>
                    <button
                      onClick={() => dismissAlert(alert.id)}
                      className="text-red-400 hover:text-red-600"
                    >
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                      </svg>
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;

