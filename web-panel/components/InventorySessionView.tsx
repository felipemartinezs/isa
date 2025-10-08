import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Download, Package, ScanLine, Clock, FileSpreadsheet } from 'lucide-react';
import { scanAPI } from '@/lib/api';
import { format } from 'date-fns';

interface InventorySummary {
  session: {
    id: number;
    mode: string;
    category: string;
    started_at: string;
    ended_at: string | null;
    is_active: boolean;
  };
  summary: {
    total_unique_items: number;
    total_scans: number;
    total_quantity: number;
  };
  items: Array<{
    sap_article: string;
    part_number: string | null;
    description: string | null;
    detected_category: string | null;
    total_quantity: number;
    scan_count: number;
    first_scan: string;
    last_scan: string;
  }>;
}

interface Props {
    sessionId: number;
    refreshTrigger?: number;
    onClose?: () => void;
  }

  export default function InventorySessionView({ sessionId, refreshTrigger, onClose }: Props) {
  const [summary, setSummary] = useState<InventorySummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [exporting, setExporting] = useState(false);

  useEffect(() => {
    console.log('📦 InventorySessionView: Loading summary (sessionId:', sessionId, 'trigger:', refreshTrigger, ')');
    loadSummary();
  }, [sessionId, refreshTrigger]);

  const loadSummary = async () => {
    setLoading(true);
    try {
      const response = await scanAPI.getInventorySummary(sessionId);
      setSummary(response.data);
    } catch (error) {
      console.error('Failed to load inventory summary:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleExport = async () => {
    setExporting(true);
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/reports/session/${sessionId}/inventory-export`,
        {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        }
      );
      
      if (!response.ok) throw new Error('Export failed');
      
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `inventory_count_${sessionId}.xlsx`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (error) {
      console.error('Export failed:', error);
      alert('Failed to export inventory');
    } finally {
      setExporting(false);
    }
  };

  if (loading) {
    return (
      <Card>
        <CardContent className="pt-6">
          <div className="text-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto" />
            <p className="mt-3 text-muted-foreground">Loading inventory...</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!summary) {
    return (
      <Card>
        <CardContent className="pt-6">
          <div className="text-center py-12 text-muted-foreground">
            <FileSpreadsheet className="h-12 w-12 mx-auto mb-2 opacity-50" />
            <p>No inventory data available</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  const duration = summary.session.ended_at
    ? (new Date(summary.session.ended_at).getTime() - new Date(summary.session.started_at).getTime()) / 60000
    : (new Date().getTime() - new Date(summary.session.started_at).getTime()) / 60000;

  return (
    <div className="space-y-4">
      {/* Header Card */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <Package className="h-5 w-5" />
                Inventory Count - Session #{sessionId}
              </CardTitle>
              <CardDescription>
                {summary.session.category} • {format(new Date(summary.session.started_at), 'PPpp')}
              </CardDescription>
            </div>
            <div className="flex gap-2">
              <Button onClick={handleExport} disabled={exporting}>
                <Download className="h-4 w-4 mr-2" />
                {exporting ? 'Exporting...' : 'Export Excel'}
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {/* Stats Grid */}
          <div className="grid grid-cols-4 gap-4">
            <div className="p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
              <div className="flex items-center gap-2 mb-1">
                <Package className="h-4 w-4 text-blue-600" />
                <p className="text-xs font-medium text-blue-700 dark:text-blue-400">
                  Unique Items
                </p>
              </div>
              <p className="text-2xl font-bold text-blue-600 dark:text-blue-400">
                {summary.summary.total_unique_items}
              </p>
            </div>

            <div className="p-4 bg-green-50 dark:bg-green-900/20 rounded-lg">
              <div className="flex items-center gap-2 mb-1">
                <ScanLine className="h-4 w-4 text-green-600" />
                <p className="text-xs font-medium text-green-700 dark:text-green-400">
                  Total Scans
                </p>
              </div>
              <p className="text-2xl font-bold text-green-600 dark:text-green-400">
                {summary.summary.total_scans}
              </p>
            </div>

            <div className="p-4 bg-purple-50 dark:bg-purple-900/20 rounded-lg">
              <div className="flex items-center gap-2 mb-1">
                <FileSpreadsheet className="h-4 w-4 text-purple-600" />
                <p className="text-xs font-medium text-purple-700 dark:text-purple-400">
                  Total Quantity
                </p>
              </div>
              <p className="text-2xl font-bold text-purple-600 dark:text-purple-400">
                {summary.summary.total_quantity}
              </p>
            </div>

            <div className="p-4 bg-orange-50 dark:bg-orange-900/20 rounded-lg">
              <div className="flex items-center gap-2 mb-1">
                <Clock className="h-4 w-4 text-orange-600" />
                <p className="text-xs font-medium text-orange-700 dark:text-orange-400">
                  Duration
                </p>
              </div>
              <p className="text-2xl font-bold text-orange-600 dark:text-orange-400">
                {Math.round(duration)}m
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Items List */}
      <Card>
        <CardHeader>
          <CardTitle>Scanned Items</CardTitle>
          <CardDescription>
            {summary.summary.total_unique_items} unique items • {summary.summary.total_scans} total scans
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-2 max-h-[500px] overflow-y-auto">
            {summary.items.map((item, index) => (
              <div
                key={index}
                className="p-4 border rounded-lg hover:bg-muted/50 transition-colors"
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                    <span className="font-mono font-bold text-lg">
                        {item.sap_article}
                        </span>
                        {item.detected_category && (
                        <span className="text-xs px-2 py-0.5 bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-400 rounded-full font-medium">
                            {item.detected_category}
                        </span>
                        )}
                      {item.scan_count > 1 && (
                        <span className="text-xs px-2 py-0.5 bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400 rounded-full">
                          {item.scan_count} scans
                        </span>
                      )}
                    </div>
                    {item.part_number && (
                      <p className="text-sm text-muted-foreground">
                        PN: {item.part_number}
                      </p>
                    )}
                    {item.description && (
                      <p className="text-sm mt-1">{item.description}</p>
                    )}
                    <p className="text-xs text-muted-foreground mt-2">
                      First scan: {format(new Date(item.first_scan), 'HH:mm:ss')}
                      {item.scan_count > 1 && ` • Last: ${format(new Date(item.last_scan), 'HH:mm:ss')}`}
                    </p>
                  </div>
                  <div className="ml-4 text-right">
                    <div className="text-3xl font-bold text-primary">
                      {item.total_quantity}
                    </div>
                    <p className="text-xs text-muted-foreground">units</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}