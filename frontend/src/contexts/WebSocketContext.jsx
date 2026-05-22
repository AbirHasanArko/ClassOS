import { createContext, useContext, useEffect, useState, useRef } from 'react';
import { useAuth } from './AuthContext';

const WebSocketContext = createContext();

export const useWebSocket = () => useContext(WebSocketContext);

export const WebSocketProvider = ({ children }) => {
  const { token } = useAuth();
  const [socket, setSocket] = useState(null);
  const [messages, setMessages] = useState([]);
  const [isConnected, setIsConnected] = useState(false);
  const activeSessionIdRef = useRef(null);
  
  const connect = (sessionId) => {
    if (!token) return;
    
    // Disconnect existing if changing sessions
    if (socket && activeSessionIdRef.current !== sessionId) {
      socket.close();
    }
    
    activeSessionIdRef.current = sessionId;
    
    // Construct WS URL
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host;
    // Vite proxy handles /ws
    const wsUrl = `${protocol}//${host}/ws/attendance/${sessionId}?token=${token}`;
    
    const newSocket = new WebSocket(wsUrl);
    
    newSocket.onopen = () => {
      console.log('WebSocket connected to session', sessionId);
      setIsConnected(true);
    };
    
    newSocket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        setMessages((prev) => [...prev, data]);
      } catch (e) {
        console.error("Failed to parse WS message", e);
      }
    };
    
    newSocket.onclose = () => {
      console.log('WebSocket disconnected');
      setIsConnected(false);
      setSocket(null);
    };
    
    setSocket(newSocket);
  };
  
  const disconnect = () => {
    if (socket) {
      socket.close();
    }
    activeSessionIdRef.current = null;
    setMessages([]);
  };

  const clearMessages = () => setMessages([]);

  return (
    <WebSocketContext.Provider value={{ socket, isConnected, messages, connect, disconnect, clearMessages }}>
      {children}
    </WebSocketContext.Provider>
  );
};
