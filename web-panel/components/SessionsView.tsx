import { useState, useEffect, useRef } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Input } from '@/components/ui/input';
import { FileSpreadsheet, Eye, Trash2, Edit2, Save, X, ChevronDown, ChevronRight, CheckCircle, Clock, AlertCircle, Package, ClipboardList, CheckCircle2 } from 'lucide-react';
import { scanAPI } from '@/lib/api';
import { format } from 'date-fns';
import SessionFinalizationModal from './SessionFinalizationModal';
import InventorySessionView from './InventorySessionView';
const CATEGORIES = ['CCTV', 'CX', 'FIRE & BURG ALARM'];

interface CategoryOverview {
  category: string;
  status: 'not_started' | 'in_progress' | 'completed';
  bom: {
    id: number;
    name: string;
    items_count: number;
    uploaded_at: string;
  } | null;
  active_sessions: Array<{  // ⭐ Cambiar a array
    id: number;
    mode: string;
    started_at: string;
    bom_name: string | null;
    scanned_items: number;
    expected_items: number | null;
    match_count: number;
    over_count: number;
    under_count: number;
  }>;
  last_session: {  // ⭐ AGREGAR ESTA PROPIEDAD QUE FALTABA
    id: number;
    mode: string;
    started_at: string;
    ended_at: string | null;
    is_active: boolean;
  } | null;
  progress: {
    scanned_items: number;
    expected_items: number | null;
    match_count: number;
    over_count: number;
    under_count: number;
  } | null;
}

// ⭐ NUEVA INTERFAZ para INVENTORY
interface InventoryOverview {
  status: 'not_started' | 'in_progress' | 'completed';
  active_sessions: Array<{
    id: number;
    mode: string;
    started_at: string;
    scanned_items: number;
    expected_items: number | null;
    match_count: number;
    over_count: number;
    under_count: number;
  }>;
  last_session: {
    id: number;
    mode: string;
    started_at: string;
    ended_at: string | null;
    is_active: boolean;
  } | null;
}

export default function SessionsView() {
  const [overview, setOverview] = useState<CategoryOverview[]>([]);
  const [inventoryOverview, setInventoryOverview] = useState<InventoryOverview | null>(null);
  const [expandedCategory, setExpandedCategory] = useState<string | null>(null);
  const [selectedSession, setSelectedSession] = useState<any>(null);
  const [summary, setSummary] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [editingRecord, setEditingRecord] = useState<number | null>(null);
  const [editQuantity, setEditQuantity] = useState<string>('');
  const [sseConnected, setSseConnected] = useState(false);
  const [isFinalizationModalOpen, setIsFinalizationModalOpen] = useState(false);
  const [sessionToFinalize, setSessionToFinalize] = useState<number | null>(null);
  const [selectedSessionMode, setSelectedSessionMode] = useState<string | null>(null);
  const [inventoryRefreshTrigger, setInventoryRefreshTrigger] = useState(0);
  const selectedSessionRef = useRef<number | null>(null);
  const selectedSessionModeRef = useRef<string | null>(null);
  const eventSourceRef = useRef<EventSource | null>(null);

  
  useEffect(() => {
    console.log('🔄 SessionsView: Iniciando polling...');
    let pollCount = 0;
    
    loadOverview();
    
    // Polling cada 3 segundos
    const intervalId = setInterval(() => {
      pollCount++;
      console.log(`🔄 Polling #${pollCount} - Ejecutando...`);
      
      loadOverview().catch(err => {
        console.error('❌ Error en loadOverview durante polling:', err);
      });
      
      // Si hay una sesión seleccionada, refrescar su summary
      if (selectedSessionRef.current) {
        if (selectedSessionModeRef.current === 'INVENTORY') {
          setInventoryRefreshTrigger(prev => prev + 1);
        } else {
          viewSessionSummary(selectedSessionRef.current, selectedSessionModeRef.current || undefined)
            .catch(err => {
              console.error('❌ Error en viewSessionSummary durante polling:', err);
            });
        }
      }
    }, 3000); // 3 segundos
    
    setSseConnected(true); // Mantener el indicador activo
    console.log(`✅ Polling iniciado con interval ID: ${intervalId}`);
    
    return () => {
      console.log(`🛑 Limpiando polling (interval ID: ${intervalId})`);
      clearInterval(intervalId);
      setSseConnected(false);
    };
  }, []);
    
  // Keep selectedSessionRef in sync with selectedSession state
    // Keep selectedSessionRef in sync with selectedSession state
    useEffect(() => {
      selectedSessionRef.current = selectedSession;
      selectedSessionModeRef.current = selectedSessionMode;  // ⭐ NUEVO
    }, [selectedSession, selectedSessionMode]);  // ⭐ Agregar selectedSessionMode a deps

  const loadOverview = async () => {
    try {
      const response = await scanAPI.getOverview();
      setOverview(response.data.categories);
      setInventoryOverview(response.data.inventory);
    } catch (error) {
      console.error('Failed to load overview:', error);
    }
  };

  const viewSessionSummary = async (sessionId: number, mode?: string) => {
    setLoading(true);
    setSelectedSession(sessionId);
    setSelectedSessionMode(mode || null);
    
    // For INVENTORY mode, don't load BOM summary
    if (mode === 'INVENTORY') {
      setLoading(false);
      return;
    }
    
    try {
      const response = await scanAPI.getSummary(sessionId);
      setSummary(response.data);
    } catch (error) {
      console.error('Failed to load summary:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteRecord = async (recordId: number) => {
    if (!confirm('Are you sure you want to delete this record?')) return;
    
    try {
      await scanAPI.deleteRecord(recordId);
      if (selectedSession) {
        await viewSessionSummary(selectedSession);
      }
    } catch (error) {
      console.error('Failed to delete record:', error);
      alert('Failed to delete record');
    }
  };

  const handleEditRecord = (recordId: number, currentQuantity: number) => {
    setEditingRecord(recordId);
    setEditQuantity(currentQuantity.toString());
  };

  const handleSaveEdit = async (recordId: number) => {
    const quantity = parseFloat(editQuantity);
    if (isNaN(quantity) || quantity <= 0) {
      alert('Invalid quantity');
      return;
    }

    try {
      await scanAPI.updateRecord(recordId, quantity);
      setEditingRecord(null);
      setEditQuantity('');
      if (selectedSession) {
        await viewSessionSummary(selectedSession);
      }
    } catch (error) {
      console.error('Failed to update record:', error);
      alert('Failed to update record');
    }
  };

  const handleCancelEdit = () => {
    setEditingRecord(null);
    setEditQuantity('');
  };

  const handleEndSession = (sessionId: number) => {
    setSessionToFinalize(sessionId);
    setIsFinalizationModalOpen(true);
  };

  const handleConfirmFinalization = async () => {
    await loadOverview();
    if (selectedSession === sessionToFinalize) {
      setSelectedSession(null);
      setSummary(null);
    }
    setSessionToFinalize(null);
    setIsFinalizationModalOpen(false);
  };

  const handleDeleteSession = async (sessionId: number) => {
    if (!confirm('Are you sure you want to delete this session? This will delete all associated records.')) return;
    
    try {
      await scanAPI.deleteSession(sessionId);
      await loadOverview();
      if (selectedSession === sessionId) {
        setSelectedSession(null);
        setSummary(null);
      }
    } catch (error) {
      console.error('Failed to delete session:', error);
      alert('Failed to delete session');
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="h-5 w-5 text-green-600" />;
      case 'in_progress':
        return <Clock className="h-5 w-5 text-blue-600 animate-pulse" />;
      default:
        return <AlertCircle className="h-5 w-5 text-gray-400" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'MATCH':
        return 'text-green-600 dark:text-green-400 bg-green-50 dark:bg-green-900/20';
      case 'OVER':
      case 'UNDER':
        return 'text-orange-600 dark:text-orange-400 bg-orange-50 dark:bg-orange-900/20';
      default:
        return 'text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-blue-900/20';
    }
  };

  return (
    <div className="space-y-4">
      {/* Real-time Status Indicator */}
      <div className="flex items-center justify-end">
        <div className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-sm ${
          sseConnected 
            ? 'bg-green-50 dark:bg-green-900/20 text-green-700 dark:text-green-400' 
            : 'bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-400'
        }`}>
          <span className={`h-2 w-2 rounded-full animate-pulse ${
            sseConnected ? 'bg-green-500' : 'bg-red-500'
          }`} />
          <span className="font-medium">
            {sseConnected ? 'Real-time Updates Active' : 'Connecting...'}
          </span>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Inventory Overview */}
        <Card>
          <CardHeader>
            <CardTitle>Inventory Overview</CardTitle>
            <CardDescription>BOMs loaded and scanning progress by category</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {overview.map((cat) => (
              <div key={cat.category} className="border rounded-lg overflow-hidden">
                {/* Category Header */}
                <div
                  className="flex items-center justify-between p-4 bg-muted/30 cursor-pointer hover:bg-muted/50 transition-colors"
                  onClick={() => setExpandedCategory(expandedCategory === cat.category ? null : cat.category)}
                >
                  <div className="flex items-center gap-3 flex-1">
                    {getStatusIcon(cat.status)}
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <span className="font-medium">{cat.category}</span>
                        <span className={`text-xs px-2 py-0.5 rounded-full ${
                          cat.status === 'in_progress' 
                            ? 'bg-blue-100 text-blue-700' 
                            : cat.status === 'completed'
                            ? 'bg-green-100 text-green-700'
                            : 'bg-gray-100 text-gray-700'
                        }`}>
                          {cat.status.replace('_', ' ')}
                        </span>
                      </div>
                      
                      {/* BOM Info */}
                      {cat.bom && (
                        <p className="text-xs text-muted-foreground mt-1">
                          📋 {cat.bom.name} ({cat.bom.items_count} items)
                        </p>
                      )}
                      
                      {/* Progress Info */}
                      {cat.progress && (
                        <div className="flex items-center gap-3 mt-2">
                          <span className="text-sm font-medium">
                            {cat.progress.scanned_items}
                            {cat.progress.expected_items && ` / ${cat.progress.expected_items}`} scanned
                          </span>
                          <div className="flex gap-2 text-xs">
                            <span className="text-green-600">✓ {cat.progress.match_count}</span>
                            <span className="text-orange-600">↑ {cat.progress.over_count}</span>
                            <span className="text-red-600">↓ {cat.progress.under_count}</span>
                          </div>
                        </div>
                      )}
                      
                      {!cat.bom && (
                        <p className="text-xs text-red-500 mt-1">
                          ⚠️ No BOM loaded
                        </p>
                      )}
                    </div>
                  </div>
                  
                  {expandedCategory === cat.category ? 
                    <ChevronDown className="h-5 w-5 text-muted-foreground" /> : 
                    <ChevronRight className="h-5 w-5 text-muted-foreground" />
                  }
                </div>
                
                {/* Expanded Details */}
                {expandedCategory === cat.category && (
                  <div className="p-4 border-t bg-background space-y-3">
                    {/* ⭐ NUEVO: Lista de sesiones activas con selector visual */}
                    {cat.active_sessions && cat.active_sessions.length > 0 && (
                      <div className="space-y-2">
                        <p className="text-sm font-medium">
                          Active Sessions ({cat.active_sessions.length})
                        </p>
                        {cat.active_sessions.map((session: any) => {
                          const isBomSession = session.mode === 'BOM';
                          const isInventorySession = session.mode === 'INVENTORY';
                          const isSelected = selectedSession === session.id;
                          
                          // Color schemes based on session type
                          const borderColor = isSelected
                            ? (isBomSession ? 'border-purple-500' : 'border-green-500')
                            : (isBomSession ? 'border-purple-200 dark:border-purple-800' : 'border-green-200 dark:border-green-800');
                          
                          const bgColor = isSelected
                            ? (isBomSession ? 'bg-purple-50 dark:bg-purple-900/30' : 'bg-green-50 dark:bg-green-900/30')
                            : (isBomSession ? 'bg-purple-50/50 dark:bg-purple-900/10' : 'bg-green-50/50 dark:bg-green-900/10');
                          
                          return (
                          <div 
                            key={session.id}
                            className={`p-3 rounded-lg transition-all border-2 ${borderColor} ${bgColor} ${
                              isSelected ? 'shadow-lg' : 'hover:shadow-md'
                            }`}
                          >
                            <div className="flex items-center justify-between">
                              <div className="flex-1">
                                {/* Session Header with Mode Badge */}
                                <div className="flex items-center gap-2 mb-2">
                                  {/* Mode Badge with Icon */}
                                  <div className={`flex items-center gap-1.5 px-2 py-1 rounded-md font-semibold text-xs ${
                                    isBomSession 
                                      ? 'bg-purple-100 dark:bg-purple-900/50 text-purple-700 dark:text-purple-300 border border-purple-300 dark:border-purple-700'
                                      : 'bg-green-100 dark:bg-green-900/50 text-green-700 dark:text-green-300 border border-green-300 dark:border-green-700'
                                  }`}>
                                    {isBomSession ? (
                                      <>
                                        <ClipboardList className="h-3.5 w-3.5" />
                                        <span>BOM MODE</span>
                                      </>
                                    ) : (
                                      <>
                                        <Package className="h-3.5 w-3.5" />
                                        <span>INVENTORY</span>
                                      </>
                                    )}
                                  </div>
                                  
                                  {/* Selected Indicator */}
                                  {isSelected && (
                                    <div className={`flex items-center gap-1.5 ${
                                      isBomSession ? 'text-purple-600 dark:text-purple-400' : 'text-green-600 dark:text-green-400'
                                    }`}>
                                      <div className={`h-2 w-2 rounded-full animate-pulse ${
                                        isBomSession ? 'bg-purple-500' : 'bg-green-500'
                                      }`} />
                                      <span className="text-xs font-semibold uppercase">Active</span>
                                    </div>
                                  )}
                                </div>

                                {/* Session ID and Timestamp */}
                                <p className="text-sm font-bold mb-1">Session #{session.id}</p>
                                <p className="text-xs text-muted-foreground">
                                  Started: {format(new Date(session.started_at), 'MMM dd, HH:mm')}
                                </p>
                                
                                {/* BOM Name for BOM sessions */}
                                {session.bom_name && (
                                  <div className="mt-1.5 flex items-center gap-1.5">
                                    <ClipboardList className="h-3 w-3 text-purple-600" />
                                    <p className="text-xs font-medium text-purple-700 dark:text-purple-300">
                                      {session.bom_name}
                                    </p>
                                  </div>
                                )}
                                
                                {/* Progress for this session */}
                                <div className="flex items-center gap-3 mt-2">
                                  <span className="text-xs font-medium">
                                    {session.scanned_items}
                                    {session.expected_items && ` / ${session.expected_items}`} scanned
                                  </span>
                                  {isBomSession && (
                                    <div className="flex gap-2 text-xs">
                                      <span className="text-green-600">✓ {session.match_count}</span>
                                      <span className="text-orange-600">↑ {session.over_count}</span>
                                      <span className="text-red-600">↓ {session.under_count}</span>
                                    </div>
                                  )}
                                </div>
                              </div>
                              
                              {/* Action Buttons */}
                              <div className="flex gap-2 ml-3">
                                <Button
                                  size="sm"
                                  variant={isSelected ? "default" : "outline"}
                                  onClick={() => viewSessionSummary(session.id, session.mode)}
                                  className={isSelected 
                                    ? (isBomSession ? "bg-purple-600 hover:bg-purple-700" : "bg-green-600 hover:bg-green-700")
                                    : (isBomSession ? "border-purple-300 hover:bg-purple-50" : "border-green-300 hover:bg-green-50")
                                  }
                                >
                                  <Eye className="h-4 w-4" />
                                </Button>
                                <Button
                                  size="sm"
                                  variant="outline"
                                  onClick={() => handleEndSession(session.id)}
                                  className="text-orange-600 hover:text-orange-700 hover:bg-orange-50"
                                >
                                  End
                                </Button>
                                <Button
                                  size="sm"
                                  variant="outline"
                                  onClick={() => handleDeleteSession(session.id)}
                                  className="text-red-600 hover:text-red-700 hover:bg-red-50"
                                >
                                  <Trash2 className="h-4 w-4" />
                                </Button>
                              </div>
                            </div>
                          </div>
                        )
                        })}
                      </div>
                    )}
                    
                    {/* Last session - only show if NO active sessions */}
                    {(!cat.active_sessions || cat.active_sessions.length === 0) && cat.last_session && (
                      <div className="space-y-2">
                        <p className="text-sm font-medium">Last Session</p>
                        <div className="p-3 bg-gray-50 dark:bg-gray-900/20 rounded-lg">
                          <div className="flex items-center justify-between">
                            <div>
                              <p className="text-sm">Session #{cat.last_session.id}</p>
                              <p className="text-xs text-muted-foreground">
                                {cat.last_session.ended_at 
                                  ? `Ended: ${format(new Date(cat.last_session.ended_at), 'MMM dd, HH:mm')}`
                                  : `Started: ${format(new Date(cat.last_session.started_at), 'MMM dd, HH:mm')}`
                                }
                              </p>
                            </div>
                            <div className="flex gap-2">
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={() => viewSessionSummary(cat.last_session!.id, cat.last_session!.mode)}
                              >
                                <Eye className="h-4 w-4" />
                              </Button>
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={() => handleDeleteSession(cat.last_session!.id)}
                                className="text-red-600 hover:text-red-700"
                              >
                                <Trash2 className="h-4 w-4" />
                              </Button>
                            </div>
                          </div>
                        </div>
                      </div>
                    )}
                    
                    {(!cat.active_sessions || cat.active_sessions.length === 0) && !cat.last_session && cat.bom && (
                      <p className="text-sm text-muted-foreground text-center py-2">
                        BOM ready. Start scanning from mobile app.
                      </p>
                    )}
                    
                    {!cat.bom && (
                      <p className="text-sm text-red-500 text-center py-2">
                        Please upload a BOM file first.
                      </p>
                    )}
                  </div>
                )}
              </div>
            ))}
          </CardContent>
        </Card>

        {/* ⭐ NUEVO: INVENTORY Overview Card */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Package className="h-5 w-5 text-green-600" />
              Inventory Sessions
            </CardTitle>
            <CardDescription>Mixed-category inventory scanning sessions</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="border rounded-lg overflow-hidden">
              {/* Inventory Header */}
              <div
                className="flex items-center justify-between p-4 bg-green-50 dark:bg-green-900/20 cursor-pointer hover:bg-green-100 dark:hover:bg-green-900/30 transition-colors"
                onClick={() => setExpandedCategory(expandedCategory === 'INVENTORY' ? null : 'INVENTORY')}
              >
                <div className="flex items-center gap-3 flex-1">
                  {inventoryOverview && getStatusIcon(inventoryOverview.status)}
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <span className="font-medium">INVENTORY MODE</span>
                      <span className={`text-xs px-2 py-0.5 rounded-full ${
                        inventoryOverview?.status === 'in_progress' 
                          ? 'bg-green-100 text-green-700' 
                          : inventoryOverview?.status === 'completed'
                          ? 'bg-gray-100 text-gray-700'
                          : 'bg-gray-100 text-gray-500'
                      }`}>
                        {inventoryOverview?.status?.replace('_', ' ') || 'not started'}
                      </span>
                    </div>
                    <p className="text-xs text-muted-foreground mt-1">
                      📦 Multi-category inventory tracking
                    </p>
                  </div>
                </div>
                
                {expandedCategory === 'INVENTORY' ? 
                  <ChevronDown className="h-5 w-5 text-muted-foreground" /> : 
                  <ChevronRight className="h-5 w-5 text-muted-foreground" />
                }
              </div>
              
              {/* Expanded Inventory Details */}
              {expandedCategory === 'INVENTORY' && inventoryOverview && (
                <div className="p-4 border-t bg-background space-y-3">
                  {/* Active Inventory Sessions */}
                  {inventoryOverview.active_sessions && inventoryOverview.active_sessions.length > 0 && (
                    <div className="space-y-2">
                      <p className="text-sm font-medium">
                        Active Sessions ({inventoryOverview.active_sessions.length})
                      </p>
                      {inventoryOverview.active_sessions.map((session: any) => {
                        const isSelected = selectedSession === session.id;
                        
                        return (
                          <div 
                            key={session.id}
                            className={`p-3 rounded-lg transition-all border-2 ${
                              isSelected 
                                ? 'border-green-500 bg-green-50 dark:bg-green-900/30 shadow-lg'
                                : 'border-green-200 dark:border-green-800 bg-green-50/50 dark:bg-green-900/10 hover:shadow-md'
                            }`}
                          >
                            <div className="flex items-center justify-between">
                              <div className="flex-1">
                                {/* Mode Badge */}
                                <div className="flex items-center gap-2 mb-2">
                                  <div className="flex items-center gap-1.5 px-2 py-1 rounded-md font-semibold text-xs bg-green-100 dark:bg-green-900/50 text-green-700 dark:text-green-300 border border-green-300 dark:border-green-700">
                                    <Package className="h-3.5 w-3.5" />
                                    <span>INVENTORY</span>
                                  </div>
                                  
                                  {/* Selected Indicator */}
                                  {isSelected && (
                                    <div className="flex items-center gap-1.5 text-green-600 dark:text-green-400">
                                      <div className="h-2 w-2 rounded-full animate-pulse bg-green-500" />
                                      <span className="text-xs font-semibold uppercase">Active</span>
                                    </div>
                                  )}
                                </div>

                                {/* Session Info */}
                                <p className="text-sm font-bold mb-1">Session #{session.id}</p>
                                <p className="text-xs text-muted-foreground">
                                  Started: {format(new Date(session.started_at), 'MMM dd, HH:mm')}
                                </p>
                                
                                {/* Stats */}
                                <div className="flex items-center gap-3 mt-2">
                                  <span className="text-xs font-medium">
                                    {session.scanned_items}
                                    {session.expected_items && ` / ${session.expected_items}`} scanned
                                  </span>
                                  <div className="flex gap-2 text-xs">
                                    <span className="text-green-600">✓ {session.match_count}</span>
                                    <span className="text-orange-600">↑ {session.over_count}</span>
                                    <span className="text-red-600">↓ {session.under_count}</span>
                                  </div>
                                </div>
                              </div>
                              
                              {/* Action Buttons */}
                              <div className="flex gap-2 ml-3">
                                <Button
                                  size="sm"
                                  variant={isSelected ? "default" : "outline"}
                                  onClick={() => viewSessionSummary(session.id, 'INVENTORY')}
                                  className={isSelected 
                                    ? "bg-green-600 hover:bg-green-700"
                                    : "border-green-300 hover:bg-green-50"
                                  }
                                >
                                  <Eye className="h-4 w-4" />
                                </Button>
                                <Button
                                  size="sm"
                                  variant="outline"
                                  onClick={() => handleEndSession(session.id)}
                                  className="text-orange-600 hover:text-orange-700 hover:bg-orange-50"
                                >
                                  End
                                </Button>
                                <Button
                                  size="sm"
                                  variant="outline"
                                  onClick={() => handleDeleteSession(session.id)}
                                  className="text-red-600 hover:text-red-700 hover:bg-red-50"
                                >
                                  <Trash2 className="h-4 w-4" />
                                </Button>
                              </div>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  )}
                  
                  {/* Last Inventory Session */}
                  {(!inventoryOverview.active_sessions || inventoryOverview.active_sessions.length === 0) && inventoryOverview.last_session && (
                    <div className="space-y-2">
                      <p className="text-sm font-medium">Last Session</p>
                      <div className="p-3 bg-gray-50 dark:bg-gray-900/20 rounded-lg">
                        <div className="flex items-center justify-between">
                          <div>
                            <p className="text-sm">Session #{inventoryOverview.last_session.id}</p>
                            <p className="text-xs text-muted-foreground">
                              {inventoryOverview.last_session.ended_at 
                                ? `Ended: ${format(new Date(inventoryOverview.last_session.ended_at), 'MMM dd, HH:mm')}`
                                : `Started: ${format(new Date(inventoryOverview.last_session.started_at), 'MMM dd, HH:mm')}`
                              }
                            </p>
                          </div>
                          <div className="flex gap-2">
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => viewSessionSummary(inventoryOverview.last_session!.id, 'INVENTORY')}
                            >
                              <Eye className="h-4 w-4" />
                            </Button>
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => handleDeleteSession(inventoryOverview.last_session!.id)}
                              className="text-red-600 hover:text-red-700"
                            >
                              <Trash2 className="h-4 w-4" />
                            </Button>
                          </div>
                        </div>
                      </div>
                    </div>
                  )}
                  
                  {(!inventoryOverview.active_sessions || inventoryOverview.active_sessions.length === 0) && !inventoryOverview.last_session && (
                    <p className="text-sm text-muted-foreground text-center py-2">
                      No inventory sessions yet. Start scanning from mobile app.
                    </p>
                  )}
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Session Summary */}
        <Card>
          <CardHeader>
            <CardTitle>Session Details</CardTitle>
            <CardDescription>
              {selectedSession
                ? `Details for Session #${selectedSession}`
                : 'Select a session to view details'}
            </CardDescription>
          </CardHeader>
          <CardContent>
            {selectedSessionMode === 'INVENTORY' && selectedSession ? (
              <InventorySessionView 
                sessionId={selectedSession}
                refreshTrigger={inventoryRefreshTrigger}
                onClose={() => {
                  setSelectedSession(null);
                  setSelectedSessionMode(null);
                }}
              />
            ) : loading ? (
              <div className="text-center py-12">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto" />
                <p className="mt-3 text-muted-foreground">Loading summary...</p>
              </div>
            ) : summary ? (
              <div className="space-y-4">
                {/* ⭐ NUEVO: Título de sesión BOM (igual que INVENTORY) */}
                {summary.session && (
                  <div className="flex items-center justify-between mb-4">
                    <div>
                      <h3 className="text-xl font-bold flex items-center gap-2">
                        <CheckCircle2 className="h-5 w-5" />
                        {summary.session.category} BOM Check - Session #{summary.session.id}
                      </h3>
                      <p className="text-sm text-muted-foreground mt-1">
                        {format(new Date(summary.session.started_at), 'PPpp')}
                      </p>
                    </div>
                  </div>
                )}
                {/* Stats */}
                <div className="grid grid-cols-3 gap-3">
                  <div className="p-3 bg-green-50 dark:bg-green-900/20 rounded-lg">
                    <p className="text-xs text-green-700 dark:text-green-400 font-medium">
                      MATCH
                    </p>
                    <p className="text-2xl font-bold text-green-600 dark:text-green-400">
                      {summary.match_count || 0}
                    </p>
                  </div>
                  <div className="p-3 bg-orange-50 dark:bg-orange-900/20 rounded-lg">
                    <p className="text-xs text-orange-700 dark:text-orange-400 font-medium">
                      OVER
                    </p>
                    <p className="text-2xl font-bold text-orange-600 dark:text-orange-400">
                      {summary.over_count || 0}
                    </p>
                  </div>
                  <div className="p-3 bg-orange-50 dark:bg-orange-900/20 rounded-lg">
                    <p className="text-xs text-orange-700 dark:text-orange-400 font-medium">
                      UNDER
                    </p>
                    <p className="text-2xl font-bold text-orange-600 dark:text-orange-400">
                      {summary.under_count || 0}
                    </p>
                  </div>
                </div>

                {/* Items */}
                <div className="space-y-2 max-h-[400px] overflow-y-auto">
                  {summary.items?.map((item: any, index: number) => (
                    <div
                      key={index}
                      className={`p-3 border rounded-lg ${getStatusColor(item.status)}`}
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                        <div className="flex items-center gap-2">
                          <p className="font-medium">{item.sap_article}</p>
                          {item.detected_category && (
                            <span className="text-xs px-2 py-0.5 bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-400 rounded-full font-medium">
                              {item.detected_category}
                            </span>
                          )}
                        </div>
                          {item.part_number && (
                            <p className="text-xs opacity-75">PN: {item.part_number}</p>
                          )}
                          {item.description && (
                            <p className="text-sm mt-1">{item.description}</p>
                          )}
                        </div>
                        <div className="text-right ml-3 flex-shrink-0">
                          {editingRecord === item.record_id ? (
                            <div className="flex items-center gap-2">
                              <Input
                                type="number"
                                value={editQuantity}
                                onChange={(e) => setEditQuantity(e.target.value)}
                                className="w-20 h-8"
                                min="0"
                                step="1"
                              />
                              <Button
                                size="sm"
                                variant="ghost"
                                onClick={() => handleSaveEdit(item.record_id)}
                              >
                                <Save className="h-4 w-4 text-green-600" />
                              </Button>
                              <Button
                                size="sm"
                                variant="ghost"
                                onClick={handleCancelEdit}
                              >
                                <X className="h-4 w-4 text-red-600" />
                              </Button>
                            </div>
                          ) : (
                            <>
                              <div className="flex items-center gap-2">
                                <div>
                                  <p className="text-lg font-bold">
                                    {item.scanned_quantity || 0}
                                    {item.expected_quantity !== undefined && (
                                      <span className="text-xs opacity-75"> of {item.expected_quantity}</span>
                                    )}
                                  </p>
                                  {item.difference !== undefined && item.difference !== 0 && (
                                    <p
                                      className={`text-xs font-medium ${
                                        item.difference > 0 ? 'text-orange-600' : 'text-red-600'
                                      }`}
                                    >
                                      {item.difference > 0 ? '+' : ''}
                                      {item.difference}
                                    </p>
                                  )}
                                </div>
                                {item.record_id && (
                                  <div className="flex gap-1">
                                    <Button
                                      size="sm"
                                      variant="ghost"
                                      onClick={() => handleEditRecord(item.record_id, item.scanned_quantity)}
                                    >
                                      <Edit2 className="h-4 w-4 text-blue-600" />
                                    </Button>
                                    <Button
                                      size="sm"
                                      variant="ghost"
                                      onClick={() => handleDeleteRecord(item.record_id)}
                                    >
                                      <Trash2 className="h-4 w-4 text-red-600" />
                                    </Button>
                                  </div>
                                )}
                              </div>
                            </>
                          )}
                        </div>
                      </div>
                      <div className="mt-2">
                        <span className="text-xs font-bold px-2 py-1 rounded-full">
                          {item.status}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              <div className="text-center py-12 text-muted-foreground">
                <FileSpreadsheet className="h-12 w-12 mx-auto mb-2 opacity-50" />
                <p>Select a session to view details</p>
              </div>
            )}
          </CardContent>
        </Card>
        {/* Finalization Modal */}
        {sessionToFinalize && (
          <SessionFinalizationModal
            sessionId={sessionToFinalize}
            isOpen={isFinalizationModalOpen}
            onClose={() => {
              setIsFinalizationModalOpen(false);
              setSessionToFinalize(null);
            }}
            onConfirm={handleConfirmFinalization}
          />
        )}
      </div>
    </div>
  );
}