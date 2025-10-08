'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Upload, CheckCircle, AlertCircle, Trash2, FileSpreadsheet } from 'lucide-react';
import { bomsAPI } from '@/lib/api';

const CATEGORIES = ['CCTV', 'CX', 'FIRE & BURG ALARM'];

export default function BOMUpload() {
  const [selectedCategory, setSelectedCategory] = useState('CCTV');
  const [boms, setBoms] = useState<any[]>([]);
  const [file, setFile] = useState<File | null>(null);
  const [bomName, setBomName] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  useEffect(() => {
    loadBOMs();
  }, [selectedCategory]);

  const loadBOMs = async () => {
    try {
      const response = await bomsAPI.getAll(selectedCategory);
      setBoms(response.data);
    } catch (error) {
      console.error('Failed to load BOMs:', error);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      setError('');
      setSuccess('');
    }
  };

  const handleUpload = async () => {
    if (!file || !bomName.trim()) {
      setError('Please provide both BOM name and file');
      return;
    }

    setLoading(true);
    setError('');
    setSuccess('');

    try {
      await bomsAPI.upload(bomName, selectedCategory, file);
      setSuccess(`BOM "${bomName}" uploaded successfully`);
      setFile(null);
      setBomName('');
      loadBOMs();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to upload BOM');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm('Are you sure you want to delete this BOM?')) return;

    try {
      await bomsAPI.delete(id);
      loadBOMs();
    } catch (error) {
      console.error('Failed to delete BOM:', error);
    }
  };

  return (
    <div className="space-y-6">
      {/* Upload Section */}
      <Card>
        <CardHeader>
          <CardTitle>Upload BOM File</CardTitle>
          <CardDescription>
            Upload Bill of Materials for verification. Required columns: SAP Article, Part Number, Description, Quantity
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <Tabs value={selectedCategory} onValueChange={setSelectedCategory}>
            <TabsList className="grid w-full grid-cols-3">
              {CATEGORIES.map((cat) => (
                <TabsTrigger key={cat} value={cat}>
                  {cat}
                </TabsTrigger>
              ))}
            </TabsList>
          </Tabs>

          <div className="space-y-2">
            <Label htmlFor="bom-name">BOM Name</Label>
            <Input
              id="bom-name"
              placeholder="e.g., Project Alpha - December 2024"
              value={bomName}
              onChange={(e) => setBomName(e.target.value)}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="bom-file">Excel File (.xlsx, .xls, .xlsm)</Label>
            <Input
              id="bom-file"
              type="file"
              accept=".xlsx,.xls,.xlsm"
              onChange={handleFileChange}
            />
          </div>

          {file && (
            <div className="flex items-center justify-between p-4 bg-muted rounded-md">
              <div>
                <p className="text-sm font-medium">{file.name}</p>
                <p className="text-xs text-muted-foreground">
                  Category: {selectedCategory} • {(file.size / 1024).toFixed(2)} KB
                </p>
              </div>
              <Button onClick={handleUpload} disabled={loading || !bomName.trim()}>
                <Upload className="h-4 w-4 mr-2" />
                {loading ? 'Uploading...' : 'Upload'}
              </Button>
            </div>
          )}

          {error && (
            <div className="flex items-start space-x-2 p-4 bg-destructive/10 text-destructive rounded-md">
              <AlertCircle className="h-5 w-5 mt-0.5" />
              <p>{error}</p>
            </div>
          )}

          {success && (
            <div className="flex items-start space-x-2 p-4 bg-green-50 dark:bg-green-900/20 text-green-700 dark:text-green-400 rounded-md">
              <CheckCircle className="h-5 w-5 mt-0.5" />
              <p>{success}</p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Existing BOMs */}
      <Card>
        <CardHeader>
          <CardTitle>Existing BOMs - {selectedCategory}</CardTitle>
          <CardDescription>
            Manage uploaded Bill of Materials
          </CardDescription>
        </CardHeader>
        <CardContent>
          {boms.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              <FileSpreadsheet className="h-12 w-12 mx-auto mb-2 opacity-50" />
              <p>No BOMs uploaded for this category yet</p>
            </div>
          ) : (
            <div className="space-y-4">
              {boms.map((bom) => (
                <div
                  key={bom.id}
                  className="border rounded-md overflow-hidden"
                >
                  <div className="flex items-center justify-between p-4 bg-muted/30">
                    <div className="flex-1">
                      <p className="font-medium">{bom.name}</p>
                      <p className="text-sm text-muted-foreground">
                        {bom.items?.length || 0} items • Uploaded {new Date(bom.uploaded_at).toLocaleDateString()}
                      </p>
                    </div>
                    <Button
                      variant="destructive"
                      size="sm"
                      onClick={() => handleDelete(bom.id)}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                  
                  {/* Preview first 5 items */}
                  {bom.items && bom.items.length > 0 && (
                    <div className="p-4 bg-background">
                      <p className="text-xs font-medium text-muted-foreground mb-2">Preview (first 5 items):</p>
                      <div className="space-y-1">
                        {bom.items.slice(0, 5).map((item: any, idx: number) => (
                          <div key={idx} className="text-xs font-mono text-muted-foreground">
                            {item.sap_article} - {item.part_number} - {item.description} (Qty: {item.quantity})
                          </div>
                        ))}
                        {bom.items.length > 5 && (
                          <p className="text-xs text-muted-foreground italic">
                            ... and {bom.items.length - 5} more items
                          </p>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
