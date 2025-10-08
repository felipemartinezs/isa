'use client';

import { useState, useEffect } from 'react';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Download, FileText, FileSpreadsheet, AlertCircle, CheckCircle2, Clock } from 'lucide-react';
import { reportsAPI, scanAPI } from '@/lib/api';

interface SessionFinalizationModalProps {
  sessionId: number;
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
}

export default function SessionFinalizationModal({
  sessionId,
  isOpen,
  onClose,
  onConfirm
}: SessionFinalizationModalProps) {
  const [preview, setPreview] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [downloading, setDownloading] = useState(false);

  useEffect(() => {
    if (isOpen) {
      loadPreview();
    }
  }, [isOpen, sessionId]);

  const loadPreview = async () => {
    setLoading(true);
    try {
      const response = await reportsAPI.getPreview(sessionId);
      setPreview(response.data);
    } catch (error) {
      console.error('Failed to load preview:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = async (format: 'pdf' | 'excel') => {
    setDownloading(true);
    try {
      const blob = await reportsAPI.downloadReport(sessionId, format);
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `inventory_report_session_${sessionId}.${format === 'pdf' ? 'pdf' : 'xlsx'}`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Failed to download report:', error);
      alert('Failed to download report');
    } finally {
      setDownloading(false);
    }
  };

  const handleConfirmEnd = async () => {
    try {
      await scanAPI.endSession(sessionId);
      onConfirm();
      onClose();
    } catch (error) {
      console.error('Failed to end session:', error);
      alert('Failed to end session');
    }
  };

  const formatDuration = (minutes: number) => {
    const hours = Math.floor(minutes / 60);
    const mins = Math.floor(minutes % 60);
    return hours > 0 ? `${hours}h ${mins}m` : `${mins}m`;
  };

  if (loading) {
    return (
      <Dialog open={isOpen} onOpenChange={onClose}>
        <DialogContent className="max-w-3xl">
          <div className="text-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto" />
            <p className="mt-3 text-muted-foreground">Loading session data...</p>
          </div>
        </DialogContent>
      </Dialog>
    );
  }

  if (!preview) return null;

  const completionPercentage = preview.statistics.completion_pct;
  const isComplete = preview.is_complete;
  const hasDiscrepancies = preview.has_discrepancies;

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="text-2xl">Review & Finalize Session</DialogTitle>
          <DialogDescription>
            Review the inventory results before closing Session #{sessionId}
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6">
          {/* Session Info Card */}
          <Card>
            <CardContent className="pt-6">
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <p className="text-muted-foreground">Session ID</p>
                  <p className="font-semibold">#{preview.session.id}</p>
                </div>
                <div>
                  <p className="text-muted-foreground">Category</p>
                  <p className="font-semibold">{preview.session.category}</p>
                </div>
                <div>
                  <p className="text-muted-foreground">BOM</p>
                  <p className="font-semibold">{preview.session.bom_name || 'N/A'}</p>
                </div>
                <div>
                  <p className="text-muted-foreground">Duration</p>
                  <p className="font-semibold flex items-center gap-1">
                    <Clock className="h-4 w-4" />
                    {formatDuration(preview.session.duration_minutes)}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Completion Status */}
          <Card className={isComplete ? 'border-green-200 bg-green-50/50 dark:bg-green-900/20' : 'border-orange-200 bg-orange-50/50 dark:bg-orange-900/20'}>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-semibold text-lg flex items-center gap-2">
                  {isComplete ? (
                    <>
                      <CheckCircle2 className="h-5 w-5 text-green-600" />
                      <span className="text-green-700 dark:text-green-400">Complete</span>
                    </>
                  ) : (
                    <>
                      <AlertCircle className="h-5 w-5 text-orange-600" />
                      <span className="text-orange-700 dark:text-orange-400">Incomplete</span>
                    </>
                  )}
                </h3>
                <span className={`text-2xl font-bold ${isComplete ? 'text-green-600 dark:text-green-400' : 'text-orange-600 dark:text-orange-400'}`}>
                  {completionPercentage.toFixed(1)}%
                </span>
              </div>
              
              {/* Progress Bar */}
              <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-3 mb-4">
                <div
                  className={`h-3 rounded-full transition-all ${
                    isComplete ? 'bg-green-600' : 'bg-orange-500'
                  }`}
                  style={{ width: `${Math.min(completionPercentage, 100)}%` }}
                />
              </div>

              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <p className="text-muted-foreground">Expected Items</p>
                  <p className="font-semibold text-lg">{preview.statistics.bom_items_count}</p>
                </div>
                <div>
                  <p className="text-muted-foreground">Scanned Items</p>
                  <p className="font-semibold text-lg">{preview.statistics.total_records}</p>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Statistics */}
          <div className="grid grid-cols-3 gap-3">
            <Card className="border-green-200 bg-green-50 dark:bg-green-900/20">
              <CardContent className="pt-6 text-center">
                <CheckCircle2 className="h-8 w-8 text-green-600 dark:text-green-400 mx-auto mb-2" />
                <p className="text-sm text-green-700 dark:text-green-400 font-medium">MATCH</p>
                <p className="text-3xl font-bold text-green-600 dark:text-green-400">{preview.statistics.match_count}</p>
                <p className="text-xs text-green-600 dark:text-green-400 mt-1">
                  {preview.statistics.total_records > 0 ? ((preview.statistics.match_count / preview.statistics.total_records) * 100).toFixed(1) : '0.0'}%
                </p>
              </CardContent>
            </Card>

            <Card className="border-orange-200 bg-orange-50 dark:bg-orange-900/20">
              <CardContent className="pt-6 text-center">
                <AlertCircle className="h-8 w-8 text-orange-600 dark:text-orange-400 mx-auto mb-2" />
                <p className="text-sm text-orange-700 dark:text-orange-400 font-medium">OVER</p>
                <p className="text-3xl font-bold text-orange-600 dark:text-orange-400">{preview.statistics.over_count}</p>
                <p className="text-xs text-orange-600 dark:text-orange-400 mt-1">
                  {preview.statistics.total_records > 0 ? ((preview.statistics.over_count / preview.statistics.total_records) * 100).toFixed(1) : '0.0'}%
                </p>
              </CardContent>
            </Card>

            <Card className="border-red-200 bg-red-50 dark:bg-red-900/20">
              <CardContent className="pt-6 text-center">
                <AlertCircle className="h-8 w-8 text-red-600 dark:text-red-400 mx-auto mb-2" />
                <p className="text-sm text-red-700 dark:text-red-400 font-medium">UNDER</p>
                <p className="text-3xl font-bold text-red-600 dark:text-red-400">{preview.statistics.under_count}</p>
                <p className="text-xs text-red-600 dark:text-red-400 mt-1">
                  {preview.statistics.total_records > 0 ? ((preview.statistics.under_count / preview.statistics.total_records) * 100).toFixed(1) : '0.0'}%
                </p>
              </CardContent>
            </Card>
          </div>

          {/* Discrepancies Alert */}
          {hasDiscrepancies && (
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>
                <strong>{preview.discrepancies.length} discrepancies found.</strong> Review items below before finalizing.
              </AlertDescription>
            </Alert>
          )}

          {/* Discrepancies List */}
          {preview.discrepancies.length > 0 && (
            <Card>
              <CardContent className="pt-6">
                <h3 className="font-semibold mb-4 flex items-center gap-2">
                  <AlertCircle className="h-5 w-5 text-orange-600" />
                  Discrepancies ({preview.discrepancies.length} items)
                </h3>
                <div className="space-y-2 max-h-64 overflow-y-auto">
                  {preview.discrepancies.map((disc: any, idx: number) => (
                    <div
                      key={idx}
                      className={`p-3 rounded-lg border ${
                        disc.status === 'UNDER' 
                          ? 'bg-red-50 border-red-200 dark:bg-red-900/20 dark:border-red-800' 
                          : 'bg-orange-50 border-orange-200 dark:bg-orange-900/20 dark:border-orange-800'
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex-1">
                          <p className="font-medium">{disc.sap_article}</p>
                          {disc.description && (
                            <p className="text-sm text-muted-foreground">{disc.description}</p>
                          )}
                        </div>
                        <div className="text-right ml-4">
                          <p className="text-sm text-muted-foreground">
                            Expected: <span className="font-semibold">{disc.expected_quantity}</span>
                          </p>
                          <p className="text-sm text-muted-foreground">
                            Scanned: <span className="font-semibold">{disc.scanned_quantity}</span>
                          </p>
                          <p className={`text-sm font-bold ${
                            disc.difference > 0 ? 'text-orange-600 dark:text-orange-400' : 'text-red-600 dark:text-red-400'
                          }`}>
                            {disc.difference > 0 ? '+' : ''}{disc.difference}
                          </p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Download Report Section */}
          <Card>
            <CardContent className="pt-6">
              <h3 className="font-semibold mb-4">Generate Report</h3>
              <div className="flex gap-3">
                <Button
                  variant="outline"
                  className="flex-1"
                  onClick={() => handleDownload('pdf')}
                  disabled={downloading}
                >
                  <FileText className="mr-2 h-4 w-4" />
                  Download PDF
                </Button>
                <Button
                  variant="outline"
                  className="flex-1"
                  onClick={() => handleDownload('excel')}
                  disabled={downloading}
                >
                  <FileSpreadsheet className="mr-2 h-4 w-4" />
                  Download Excel
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Actions */}
          <div className="flex gap-3 pt-4">
            <Button
              variant="outline"
              onClick={onClose}
              className="flex-1"
            >
              Cancel
            </Button>
            <Button
              onClick={handleConfirmEnd}
              className="flex-1 bg-blue-600 hover:bg-blue-700"
            >
              <CheckCircle2 className="mr-2 h-4 w-4" />
              Confirm & Close Session
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}