'use client';

import { useState, useEffect, useRef } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Activity, CheckCircle, AlertTriangle, TrendingUp } from 'lucide-react';
import { connectToSSE } from '@/lib/api';
import { format } from 'date-fns';

interface ScanRecord {
  id: number;
  sap_article: string;
  part_number?: string;
  description?: string;
  po_number?: string;
  quantity: number;
  scanned_at: string;
  manual_entry: boolean;
  expected_quantity?: number;
  status?: 'MATCH' | 'OVER' | 'UNDER' | 'PENDING';
}

export default function RealtimeFeed() {
  const [records, setRecords] = useState<ScanRecord[]>([]);
  const [connected, setConnected] = useState(false);
  const eventSourceRef = useRef<EventSource | null>(null);

  useEffect(() => {
    // Connect to SSE
    eventSourceRef.current = connectToSSE((data) => {
      if (data.type === 'scan') {
        setRecords((prev) => [data.record, ...prev].slice(0, 50)); // Keep last 50
      }
    });

    setConnected(true);

    // Cleanup
    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }
    };
  }, []);

  const getStatusColor = (status?: string) => {
    switch (status) {
      case 'MATCH':
        return 'text-green-600 dark:text-green-400 bg-green-50 dark:bg-green-900/20';
      case 'OVER':
        return 'text-orange-600 dark:text-orange-400 bg-orange-50 dark:bg-orange-900/20';
      case 'UNDER':
        return 'text-orange-600 dark:text-orange-400 bg-orange-50 dark:bg-orange-900/20';
      default:
        return 'text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-blue-900/20';
    }
  };

  const getStatusIcon = (status?: string) => {
    switch (status) {
      case 'MATCH':
        return <CheckCircle className="h-5 w-5" />;
      case 'OVER':
      case 'UNDER':
        return <AlertTriangle className="h-5 w-5" />;
      default:
        return <TrendingUp className="h-5 w-5" />;
    }
  };

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center space-x-2">
              <Activity className="h-5 w-5" />
              <span>Real-time Scanning Feed</span>
            </CardTitle>
            <CardDescription>
              Live updates from mobile scanners
            </CardDescription>
          </div>
          <div className="flex items-center space-x-2">
            <div
              className={`h-3 w-3 rounded-full ${
                connected ? 'bg-green-500 animate-pulse' : 'bg-gray-400'
              }`}
            />
            <span className="text-sm text-muted-foreground">
              {connected ? 'Connected' : 'Disconnected'}
            </span>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        {records.length === 0 ? (
          <div className="text-center py-12 text-muted-foreground">
            <Activity className="h-12 w-12 mx-auto mb-3 opacity-50" />
            <p className="text-lg font-medium">Waiting for scans...</p>
            <p className="text-sm">Scanned items will appear here in real-time</p>
          </div>
        ) : (
          <div className="space-y-3 max-h-[600px] overflow-y-auto">
            {records.map((record, index) => (
              <div
                key={`${record.id}-${index}`}
                className="flex items-start space-x-3 p-4 border rounded-lg hover:bg-muted/50 transition-all animate-in slide-in-from-top-2"
              >
                <div className={`p-2 rounded-lg ${getStatusColor(record.status)}`}>
                  {getStatusIcon(record.status)}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <p className="font-semibold text-lg">
                        {record.sap_article}
                      </p>
                      {record.part_number && (
                        <p className="text-sm text-muted-foreground">
                          PN: {record.part_number}
                        </p>
                      )}
                      {record.description && (
                        <p className="text-sm mt-1">{record.description}</p>
                      )}
                      {record.po_number && (
                        <p className="text-xs text-muted-foreground mt-1">
                          PO: {record.po_number}
                        </p>
                      )}
                    </div>
                    <div className="text-right ml-4">
                      <p className="text-2xl font-bold">{record.quantity}</p>
                      {record.expected_quantity !== undefined && (
                        <p className="text-xs text-muted-foreground">
                          Expected: {record.expected_quantity}
                        </p>
                      )}
                    </div>
                  </div>
                  <div className="flex items-center justify-between mt-2">
                    <div className="flex items-center space-x-2">
                      {record.status && (
                        <span
                          className={`text-xs font-medium px-2 py-1 rounded-full ${getStatusColor(
                            record.status
                          )}`}
                        >
                          {record.status}
                        </span>
                      )}
                      {record.manual_entry && (
                        <span className="text-xs px-2 py-1 rounded-full bg-purple-100 dark:bg-purple-900/20 text-purple-700 dark:text-purple-400">
                          Manual Entry
                        </span>
                      )}
                    </div>
                    <p className="text-xs text-muted-foreground">
                      {format(new Date(record.scanned_at), 'HH:mm:ss')}
                    </p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
