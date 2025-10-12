'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Card, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
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
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const loadUser = async () => {
    try {
      const response = await authAPI.getCurrentUser();
      setUser(response.data);
    } catch {
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
      {/* Header - Responsive */}
      <header className="border-b bg-white/80 dark:bg-gray-900/80 backdrop-blur-sm sticky top-0 z-50">
        <div className="container mx-auto px-3 sm:px-4 py-3 sm:py-4">
          <div className="flex items-center justify-between gap-2">
            {/* Logo & Title */}
            <div className="flex items-center space-x-2 sm:space-x-3">
              <div className="h-8 w-8 sm:h-10 sm:w-10 bg-primary rounded-lg flex items-center justify-center flex-shrink-0">
                <Activity className="h-5 w-5 sm:h-6 sm:w-6 text-white" />
              </div>
              <div>
                <h1 className="text-lg sm:text-2xl font-bold">ISA</h1>
                <p className="text-xs sm:text-sm text-muted-foreground hidden sm:block">
                  Management Panel
                </p>
              </div>
            </div>

            {/* User Info & Logout */}
            <div className="flex items-center gap-2 sm:gap-4">
              {/* User info - hidden on mobile */}
              {user && (
                <div className="text-right hidden md:block">
                  <p className="text-sm font-medium">{user.username}</p>
                  <p className="text-xs text-muted-foreground">{user.email}</p>
                </div>
              )}

              {/* Logout Button - Icon only on mobile */}
              <Button
                variant="outline"
                size="sm"
                onClick={handleLogout}
                className="flex items-center gap-2"
                aria-label="Logout"
              >
                <LogOut className="h-4 w-4" />
                <span className="hidden sm:inline">Logout</span>
              </Button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-3 sm:px-4 py-4 sm:py-8">
        {/* Stats Cards - Responsive Grid */}
        {stats && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-2 sm:gap-4 mb-4 sm:mb-8">
            <Card>
              <CardHeader className="pb-2 sm:pb-3 pt-3 sm:pt-6 px-3 sm:px-6">
                <CardDescription className="text-xs sm:text-sm">Total Articles</CardDescription>
                <CardTitle className="text-xl sm:text-3xl">{stats.total}</CardTitle>
              </CardHeader>
            </Card>
            <Card>
              <CardHeader className="pb-2 sm:pb-3 pt-3 sm:pt-6 px-3 sm:px-6">
                <CardDescription className="text-xs sm:text-sm">CCTV</CardDescription>
                <CardTitle className="text-xl sm:text-3xl">{stats.by_category?.CCTV || 0}</CardTitle>
              </CardHeader>
            </Card>
            <Card>
              <CardHeader className="pb-2 sm:pb-3 pt-3 sm:pt-6 px-3 sm:px-6">
                <CardDescription className="text-xs sm:text-sm">CX</CardDescription>
                <CardTitle className="text-xl sm:text-3xl">{stats.by_category?.CX || 0}</CardTitle>
              </CardHeader>
            </Card>
            <Card>
              <CardHeader className="pb-2 sm:pb-3 pt-3 sm:pt-6 px-3 sm:px-6">
                <CardDescription className="text-xs sm:text-sm">Fire & Alarm</CardDescription>
                <CardTitle className="text-xl sm:text-3xl">
                  {stats.by_category?.['FIRE & BURG ALARM'] || 0}
                </CardTitle>
              </CardHeader>
            </Card>
          </div>
        )}

        {/* Main Tabs - Scrollable on Mobile */}
        <Tabs defaultValue="debugger" className="space-y-4">
          {/* Tabs List - Horizontal scroll on mobile */}
          <div className="relative">
            <TabsList className="w-full inline-flex h-auto overflow-x-auto [-webkit-overflow-scrolling:touch] overflow-y-hidden flex-nowrap md:grid md:grid-cols-5 gap-1 p-1">
              <TabsTrigger
                value="debugger"
                className="h-10 flex-shrink-0 text-xs sm:text-sm px-2 sm:px-4"
              >
                <span className="hidden sm:inline">🐛 </span>
                <span>Debug</span>
              </TabsTrigger>
              <TabsTrigger
                value="feed"
                className="h-10 flex-shrink-0 text-xs sm:text-sm px-2 sm:px-4"
              >
                <Activity className="h-3 w-3 sm:h-4 sm:w-4 mr-1 sm:mr-2" />
                Feed
              </TabsTrigger>
              <TabsTrigger
                value="sessions"
                className="h-10 flex-shrink-0 text-xs sm:text-sm px-2 sm:px-4"
              >
                <FileSpreadsheet className="h-3 w-3 sm:h-4 sm:w-4 mr-1 sm:mr-2" />
                Sessions
              </TabsTrigger>
              <TabsTrigger
                value="articles"
                className="h-10 flex-shrink-0 text-xs sm:text-sm px-2 sm:px-4"
              >
                <Database className="h-3 w-3 sm:h-4 sm:w-4 mr-1 sm:mr-2" />
                Articles
              </TabsTrigger>
              <TabsTrigger
                value="boms"
                className="h-10 flex-shrink-0 text-xs sm:text-sm px-2 sm:px-4"
              >
                <FileSpreadsheet className="h-3 w-3 sm:h-4 sm:w-4 mr-1 sm:mr-2" />
                BOMs
              </TabsTrigger>
            </TabsList>
          </div>

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
