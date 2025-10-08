'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Upload, CheckCircle, AlertCircle, Database, Trash2 } from 'lucide-react';
import { articlesAPI } from '@/lib/api';

interface ArticleUploadProps {
  onUploadSuccess?: () => void;
}

export default function ArticleUpload({ onUploadSuccess }: ArticleUploadProps) {
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState('');
  const [dbStats, setDbStats] = useState<any>(null);
  const [loadingStats, setLoadingStats] = useState(true);

  useEffect(() => {
    loadDatabaseStats();
  }, []);

  const loadDatabaseStats = async () => {
    setLoadingStats(true);
    try {
      const response = await articlesAPI.getStats();
      setDbStats(response.data);
    } catch (err) {
      console.error('Failed to load stats:', err);
    } finally {
      setLoadingStats(false);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      setResult(null);
      setError('');
    }
  };

  const handleUpload = async () => {
    if (!file) return;

    setLoading(true);
    setError('');
    setResult(null);

    try {
      const response = await articlesAPI.upload(file);
      setResult(response.data);
      setFile(null);
      await loadDatabaseStats(); // Refresh stats
      if (onUploadSuccess) onUploadSuccess();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to upload file');
    } finally {
      setLoading(false);
    }
  };

  const handleClearDatabase = async () => {
    if (!confirm('Are you sure you want to delete ALL articles from the database? This action cannot be undone.')) {
      return;
    }

    setLoading(true);
    try {
      await articlesAPI.clearAll();
      await loadDatabaseStats();
      setResult({ message: 'Database cleared successfully' });
      if (onUploadSuccess) onUploadSuccess();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to clear database');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Article Database Upload</CardTitle>
        <CardDescription>
          Upload Excel file with article database. Required columns: SAP Article, Part Number, Description, Category
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Current Database Status */}
        {!loadingStats && dbStats && dbStats.total > 0 && (
          <div className="p-4 border rounded-lg bg-blue-50 dark:bg-blue-900/20">
            <div className="flex items-start justify-between mb-3">
              <div className="flex items-center gap-2">
                <Database className="h-5 w-5 text-blue-600 dark:text-blue-400" />
                <div>
                  <p className="font-semibold text-blue-900 dark:text-blue-100">
                    Database Loaded
                  </p>
                  <p className="text-sm text-blue-700 dark:text-blue-300">
                    {dbStats.total} articles in database
                  </p>
                </div>
              </div>
              <Button
                variant="destructive"
                size="sm"
                onClick={handleClearDatabase}
                disabled={loading}
              >
                <Trash2 className="h-4 w-4 mr-2" />
                Clear All
              </Button>
            </div>
            
            {/* Category Breakdown */}
            <div className="grid grid-cols-3 gap-2 mt-3">
              {dbStats.by_category && Object.entries(dbStats.by_category).map(([category, count]: [string, any]) => (
                <div key={category} className="bg-white/50 dark:bg-gray-800/50 p-2 rounded text-center">
                  <p className="text-xs text-muted-foreground">{category}</p>
                  <p className="text-lg font-bold">{count}</p>
                </div>
              ))}
            </div>
          </div>
        )}

        {!loadingStats && (!dbStats || dbStats.total === 0) && (
          <div className="p-4 border rounded-lg bg-yellow-50 dark:bg-yellow-900/20">
            <div className="flex items-center gap-2">
              <AlertCircle className="h-5 w-5 text-yellow-600 dark:text-yellow-400" />
              <div>
                <p className="font-semibold text-yellow-900 dark:text-yellow-100">
                  No Database Loaded
                </p>
                <p className="text-sm text-yellow-700 dark:text-yellow-300">
                  Upload an Excel file to populate the article database
                </p>
              </div>
            </div>
          </div>
        )}

        <div className="space-y-2">
          <Label htmlFor="article-file">Excel File (.xlsx, .xls)</Label>
          <Input
            id="article-file"
            type="file"
            accept=".xlsx,.xls"
            onChange={handleFileChange}
          />
        </div>

        {file && (
          <div className="flex items-center justify-between p-4 bg-muted rounded-md">
            <div>
              <p className="text-sm font-medium">{file.name}</p>
              <p className="text-xs text-muted-foreground">
                {(file.size / 1024).toFixed(2)} KB
              </p>
            </div>
            <Button onClick={handleUpload} disabled={loading}>
              <Upload className="h-4 w-4 mr-2" />
              {loading ? 'Uploading...' : 'Upload'}
            </Button>
          </div>
        )}

        {error && (
          <div className="flex items-start space-x-2 p-4 bg-destructive/10 text-destructive rounded-md">
            <AlertCircle className="h-5 w-5 mt-0.5" />
            <div>
              <p className="font-medium">Upload Failed</p>
              <p className="text-sm">{error}</p>
            </div>
          </div>
        )}

        {result && (
          <div className="flex items-start space-x-2 p-4 bg-green-50 dark:bg-green-900/20 text-green-700 dark:text-green-400 rounded-md">
            <CheckCircle className="h-5 w-5 mt-0.5" />
            <div className="flex-1">
              <p className="font-medium">{result.message}</p>
              {result.items && result.items.length > 0 && (
                <div className="mt-2 text-sm">
                  <p className="font-medium">Preview (first {result.items.length} items):</p>
                  <div className="mt-1 space-y-1">
                    {result.items.map((item: any, idx: number) => (
                      <div key={idx} className="text-xs">
                        {item.sap_article} - {item.part_number} - {item.description} ({item.category})
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        <div className="pt-4 border-t">
          <p className="text-sm font-medium mb-2">File Format Example:</p>
          <div className="bg-muted p-3 rounded-md text-xs font-mono">
            <div className="grid grid-cols-4 gap-2 font-bold mb-1">
              <div>SAP Article</div>
              <div>Part Number</div>
              <div>Description</div>
              <div>Category</div>
            </div>
            <div className="grid grid-cols-4 gap-2">
              <div>87654321</div>
              <div>PN-12345</div>
              <div>Sample Item</div>
              <div>CCTV</div>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
