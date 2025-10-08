'use client';

import { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

export default function SSEDebugger() {
  const [events, setEvents] = useState<any[]>([]);
  const [status, setStatus] = useState('Disconnected');

  useEffect(() => {
    const token = localStorage.getItem('token');
    const url = `http://localhost:8000/events/stream?token=${token}`;
    
    console.log('🔌 Connecting to SSE:', url);
    const eventSource = new EventSource(url);

    eventSource.onopen = () => {
      console.log('✅ SSE OPEN');
      setStatus('Connected');
    };

    eventSource.onmessage = (event) => {
      console.log('📡 RAW onmessage:', event);
      console.log('📡 RAW event.data:', event.data);
      setEvents(prev => [...prev, {
        type: 'onmessage',
        data: event.data,
        time: new Date().toISOString()
      }]);
    };

    eventSource.addEventListener('scan', (event: any) => {
      console.log('📡 RAW scan event:', event);
      console.log('📡 RAW scan event.data:', event.data);
      setEvents(prev => [...prev, {
        type: 'scan',
        data: event.data,
        time: new Date().toISOString()
      }]);
    });

    eventSource.addEventListener('record_updated', (event: any) => {
      console.log('📡 RAW record_updated event:', event);
      setEvents(prev => [...prev, {
        type: 'record_updated',
        data: event.data,
        time: new Date().toISOString()
      }]);
    });

    eventSource.addEventListener('record_deleted', (event: any) => {
      console.log('📡 RAW record_deleted event:', event);
      setEvents(prev => [...prev, {
        type: 'record_deleted',
        data: event.data,
        time: new Date().toISOString()
      }]);
    });

    eventSource.addEventListener('ping', (event: any) => {
      console.log('📡 PING');
      setEvents(prev => [...prev, {
        type: 'ping',
        data: 'keepalive',
        time: new Date().toISOString()
      }]);
    });

    eventSource.onerror = (error) => {
      console.error('❌ SSE ERROR:', error);
      setStatus('Error');
    };

    return () => {
      console.log('🔌 Closing SSE');
      eventSource.close();
      setStatus('Disconnected');
    };
  }, []);

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <span>SSE Debugger</span>
          <span className={`text-sm px-3 py-1 rounded-full ${
            status === 'Connected' 
              ? 'bg-green-100 text-green-700' 
              : 'bg-red-100 text-red-700'
          }`}>
            {status}
          </span>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-2 max-h-96 overflow-y-auto">
          {events.length === 0 ? (
            <p className="text-muted-foreground">Waiting for events...</p>
          ) : (
            events.map((event, idx) => (
              <div key={idx} className="p-3 border rounded text-xs">
                <div className="flex justify-between mb-1">
                  <span className="font-bold">{event.type}</span>
                  <span className="text-muted-foreground">{new Date(event.time).toLocaleTimeString()}</span>
                </div>
                <pre className="bg-muted p-2 rounded overflow-x-auto">
                  {typeof event.data === 'string' ? event.data : JSON.stringify(event.data, null, 2)}
                </pre>
              </div>
            ))
          )}
        </div>
      </CardContent>
    </Card>
  );
}
