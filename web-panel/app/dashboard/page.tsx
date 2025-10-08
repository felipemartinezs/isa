'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { LogOut, Database, FileSpreadsheet, Activity } from 'lucide-react';
import ArticleUpload from '@/components/ArticleUpload';
import BOMUpload from '@/components/BOMUpload';
import RealtimeFeed from '@/components/RealtimeFeed';
import SessionsView from '@/components/SessionsView';
import SSEDebugger from '@/components/SSEDebugger';
import { authAPI, articlesAPI } from '@/lib/api';

export default function DashboardPage() {
  const router = useRouter();
  const [user, setUser] = useState<any>(null);
  const [stats, setStats] = useState<any>(null);

  useEffect(() => {
    loadUser();
    loadStats();
  }, []);

  const loadUser = async () => {
    try {
      const response = await authAPI.getCurrentUser();
      setUser(response.data);
    } catch (error) {
      router.push('/login');
    }
  };

  const loadStats = async () => {
    try {
      const response = await articlesAPI.getStats();
      setStats(response.data);
    } catch (error) {
      console.error('Failed to load stats:', error);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    router.push('/login');
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 dark:from-gray-900 dark:to-gray-800">
      {/* Header */}
      <header className="border-b bg-white/80 dark:bg-gray-900/80 backdrop-blur-sm sticky top-0 z-50">
        <div className="container mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="h-10 w-10 bg-primary rounded-lg flex items-center justify-center">
              <Activity className="h-6 w-6 text-white" />
            </div>
            <div>
              <h1 className="text-2xl font-bold">ISA</h1>
              <p className="text-sm text-muted-foreground">Management Panel</p>
            </div>
          </div>
          <div className="flex items-center space-x-4">
            {user && (
              <div className="text-right">
                <p className="text-sm font-medium">{user.username}</p>
                <p className="text-xs text-muted-foreground">{user.email}</p>
              </div>
            )}
            <Button variant="outline" onClick={handleLogout}>
              <LogOut className="h-4 w-4 mr-2" />
              Logout
            </Button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-8">
        {/* Stats Cards */}
        {stats && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
            <Card>
              <CardHeader className="pb-3">
                <CardDescription>Total Articles</CardDescription>
                <CardTitle className="text-3xl">{stats.total}</CardTitle>
              </CardHeader>
            </Card>
            <Card>
              <CardHeader className="pb-3">
                <CardDescription>CCTV Articles</CardDescription>
                <CardTitle className="text-3xl">{stats.by_category?.CCTV || 0}</CardTitle>
              </CardHeader>
            </Card>
            <Card>
              <CardHeader className="pb-3">
                <CardDescription>CX Articles</CardDescription>
                <CardTitle className="text-3xl">{stats.by_category?.CX || 0}</CardTitle>
              </CardHeader>
            </Card>
            <Card>
              <CardHeader className="pb-3">
                <CardDescription>Fire & Burg Alarm</CardDescription>
                <CardTitle className="text-3xl">
                  {stats.by_category?.['FIRE & BURG ALARM'] || 0}
                </CardTitle>
              </CardHeader>
            </Card>
          </div>
        )}

        {/* Main Tabs */}
        <Tabs defaultValue="debugger" className="space-y-4">
          <TabsList className="grid w-full grid-cols-5">
            <TabsTrigger value="debugger">
              🐛 SSE Debug
            </TabsTrigger>
            <TabsTrigger value="feed">
              <Activity className="h-4 w-4 mr-2" />
              Real-time Feed
            </TabsTrigger>
            <TabsTrigger value="sessions">
              <FileSpreadsheet className="h-4 w-4 mr-2" />
              Sessions
            </TabsTrigger>
            <TabsTrigger value="articles">
              <Database className="h-4 w-4 mr-2" />
              Article Database
            </TabsTrigger>
            <TabsTrigger value="boms">
              <FileSpreadsheet className="h-4 w-4 mr-2" />
              BOM Management
            </TabsTrigger>
          </TabsList>

          <TabsContent value="debugger">
            <SSEDebugger />
          </TabsContent>

          <TabsContent value="feed">
            <RealtimeFeed />
          </TabsContent>

          <TabsContent value="sessions">
            <SessionsView />
          </TabsContent>

          <TabsContent value="articles">
            <ArticleUpload onUploadSuccess={loadStats} />
          </TabsContent>

          <TabsContent value="boms">
            <BOMUpload />
          </TabsContent>
        </Tabs>
      </main>
    </div>
  );
}
