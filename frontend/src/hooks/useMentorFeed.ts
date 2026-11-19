import { useState, useEffect, useRef, useCallback } from 'react';
import { IoriAlert } from '@/types';

export function useMentorFeed(mentorId?: string) {
  const [alerts, setAlerts] = useState<IoriAlert[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [connectionError, setConnectionError] = useState<string | null>(null);
  const socketRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<number | null>(null);
  const reconnectAttempts = useRef(0);
  const maxReconnectAttempts = 5;

  const clearAlerts = useCallback(() => {
    setAlerts([]);
  }, []);

  useEffect(() => {
    if (!mentorId) return;

    let isMounted = true;
    const wsBaseUrl = import.meta.env.VITE_WS_URL || 'ws://localhost:8000/ws/mentor';
    const wsUrl = `${wsBaseUrl}/${mentorId}`;

    const connect = () => {
      try {
        const socket = new WebSocket(wsUrl);
        socketRef.current = socket;

        socket.onopen = () => {
          if (!isMounted) return;
          setIsConnected(true);
          setConnectionError(null);
          reconnectAttempts.current = 0;
        };

        socket.onmessage = (event) => {
          if (!isMounted) return;
          try {
            const data = JSON.parse(event.data);
            // Verify structure of IoriAlert
            if (data && data.student_id && data.iori !== undefined) {
              const newAlert: IoriAlert = {
                student_id: data.student_id,
                student_name: data.student_name || 'Anonymous Student',
                iori: Number(data.iori),
                risk_zone: data.risk_zone || (data.iori >= 0.6 ? 'red' : data.iori >= 0.3 ? 'yellow' : 'green'),
                timestamp: data.timestamp || new Date().toISOString(),
                dominant_state: data.dominant_state,
              };

              setAlerts((prev) => [newAlert, ...prev].slice(0, 50));
            }
          } catch (err) {
            console.error('Failed to parse mentor WebSocket message:', err);
          }
        };

        socket.onerror = () => {
          if (!isMounted) return;
          setConnectionError('WebSocket connection encountered an error.');
        };

        socket.onclose = () => {
          if (!isMounted) return;
          setIsConnected(false);
          socketRef.current = null;

          // Attempt reconnection with exponential backoff if below threshold
          if (reconnectAttempts.current < maxReconnectAttempts) {
            const delay = Math.min(1000 * Math.pow(2, reconnectAttempts.current), 15000);
            reconnectAttempts.current += 1;
            reconnectTimeoutRef.current = window.setTimeout(() => {
              if (isMounted) connect();
            }, delay);
          }
        };
      } catch (err) {
        if (!isMounted) return;
        setIsConnected(false);
        setConnectionError('Failed to establish WebSocket connection.');
      }
    };

    connect();

    return () => {
      isMounted = false;
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (socketRef.current) {
        socketRef.current.close();
        socketRef.current = null;
      }
    };
  }, [mentorId]);

  return { alerts, isConnected, connectionError, clearAlerts };
}

export default useMentorFeed;
