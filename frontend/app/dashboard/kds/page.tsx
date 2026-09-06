'use client';

import React from 'react';
import { 
  ChefHat, Play, CheckCircle, RefreshCw, Clock, 
  Volume2, ShieldAlert, Monitor, ArrowRight, User
} from 'lucide-react';
import { usePOSStore } from '@/store/usePOSStore';
import { apiClient } from '@/services/api';
import { Button, Card, Toast } from '@/components/UI';

export default function KDSPage() {
  const { activeCompany, activeBranch, currentUser } = usePOSStore();

  const [orders, setOrders] = React.useState<any[]>([]);
  const [prevPendingIds, setPrevPendingIds] = React.useState<Set<number>>(new Set());
  const [toastMsg, setToastMsg] = React.useState('');
  const [isLoading, setIsLoading] = React.useState(false);
  const [soundEnabled, setSoundEnabled] = React.useState(true);
  const isFirstLoad = React.useRef(true);

  // Time ticking helper to trigger render updates for stopwatch
  const [, setTick] = React.useState(0);
  React.useEffect(() => {
    const timer = setInterval(() => setTick(t => t + 1), 10000); // Trigger stopwatch redraw every 10s
    return () => clearInterval(timer);
  }, []);

  const playNotificationSound = React.useCallback(() => {
    if (!soundEnabled) return;
    try {
      const AudioCtx = window.AudioContext || (window as any).webkitAudioContext;
      if (!AudioCtx) return;
      const audioCtx = new AudioCtx();
      const oscillator = audioCtx.createOscillator();
      const gainNode = audioCtx.createGain();
      
      oscillator.type = 'sine';
      oscillator.frequency.setValueAtTime(880, audioCtx.currentTime); // A5 note
      gainNode.gain.setValueAtTime(0.12, audioCtx.currentTime);
      
      oscillator.connect(gainNode);
      gainNode.connect(audioCtx.destination);
      
      if (audioCtx.state === 'suspended') {
        audioCtx.resume();
      }
      
      oscillator.start();
      oscillator.stop(audioCtx.currentTime + 0.15); // beep duration 150ms
    } catch (e) {
      console.warn('Audio synthesis blocked by browser auto-play restrictions.', e);
    }
  }, [soundEnabled]);

  const fetchQueue = async (silent = false) => {
    if (!silent) setIsLoading(true);
    try {
      const res = await apiClient.get('/sales/kds/queue', {
        params: { branch_id: activeBranch?.id }
      });
      if (res.data.success && res.data.data) {
        const queueList = res.data.data;
        setOrders(queueList);

        // Check for new pending orders to sound buzzer
        const currentPending = queueList.filter((o: any) => o.preparation_status === 'pending');
        let hasNew = false;
        const newIds = new Set<number>();
        
        currentPending.forEach((o: any) => {
          newIds.add(o.id);
          if (!prevPendingIds.has(o.id)) {
            hasNew = true;
          }
        });

        if (hasNew && !isFirstLoad.current) {
          playNotificationSound();
        }
        setPrevPendingIds(newIds);
        isFirstLoad.current = false;
      }
    } catch (err) {
      console.error('Failed to reload KDS queue', err);
    } finally {
      if (!silent) setIsLoading(false);
    }
  };

  // Real-time synchronization via Server-Sent Events (SSE)
  React.useEffect(() => {
    if (!activeCompany?.settings?.enable_kds) return;

    fetchQueue();

    const companyId = activeCompany.id;
    const sseUrl = `http://localhost:8000/api/v1/sales/kds/events?company_id=${companyId}`;
    const eventSource = new EventSource(sseUrl);

    eventSource.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data);
        if (payload.event === 'refresh') {
          fetchQueue(true);
        }
      } catch (err) {
        console.error('Failed to parse KDS SSE payload', err);
      }
    };

    eventSource.onerror = (err) => {
      console.warn('KDS SSE connection failed. Reconnecting...', err);
    };

    // Fallback slow polling every 30 seconds
    const fallbackPoll = setInterval(() => fetchQueue(true), 30000);

    return () => {
      eventSource.close();
      clearInterval(fallbackPoll);
    };
  }, [activeCompany, activeBranch]);

  const handleStatusTransition = async (orderId: number, nextStatus: string) => {
    try {
      const res = await apiClient.put(`/sales/${orderId}/kds-status`, {
        preparation_status: nextStatus
      });
      if (res.data.success) {
        setToastMsg(`Ticket #${orderId} moved to ${nextStatus}.`);
        fetchQueue(true);
      }
    } catch (err) {
      setToastMsg('Failed to update preparation status.');
    }
  };

  const getElapsedTime = (saleDateStr: string) => {
    const elapsedMs = Date.now() - new Date(saleDateStr).getTime();
    const elapsedMins = Math.floor(elapsedMs / 60000);
    return elapsedMins;
  };

  if (!activeCompany?.settings?.enable_kds) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] text-center p-6 bg-white dark:bg-slate-900 rounded-3xl border border-slate-100 dark:border-slate-800 shadow-sm text-left">
        <ShieldAlert className="w-16 h-16 text-amber-500 mb-4 animate-pulse" />
        <h3 className="text-xl font-bold text-slate-800 dark:text-white mb-2">KDS Module Disabled</h3>
        <p className="text-sm text-slate-500 dark:text-slate-400 max-w-md">
          The Order Prep Monitor (KDS Queue) is currently disabled for your company. To enable this real-time preparation display queue, please go to **Branches & Store Stats** and toggle it on under the **System Configurations** settings tab.
        </p>
      </div>
    );
  }

  // Filter lists by status
  const pendingOrders = orders.filter(o => o.preparation_status === 'pending');
  const preparingOrders = orders.filter(o => o.preparation_status === 'preparing');
  const readyOrders = orders.filter(o => o.preparation_status === 'ready');

  return (
    <div className="flex flex-col gap-6 text-left pb-10">
      
      {/* Root Sleek SLA Warning Keyframes */}
      <style dangerouslySetInnerHTML={{ __html: `
        @keyframes borderPulse {
          0% { border-color: rgba(239, 68, 68, 0.4); box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.1); }
          50% { border-color: rgba(239, 68, 68, 1); box-shadow: 0 0 12px 2px rgba(239, 68, 68, 0.2); }
          100% { border-color: rgba(239, 68, 68, 0.4); box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.1); }
        }
        .animate-pulse-red-border {
          animation: borderPulse 1.8s infinite ease-in-out;
        }
      `}} />
      
      {/* Header Banner */}
      <div className="flex items-center justify-between gap-4">
        <div className="flex flex-col gap-1">
          <h2 className="text-2xl font-bold dark:text-white flex items-center gap-2">
            <ChefHat className="w-6 h-6 text-brand-500" />
            Order Prep Monitor (KDS Queue)
          </h2>
          <p className="text-xs text-slate-400">
            Live order tracker for active store counters and assembly staff. Branch: <strong>{activeBranch?.name || 'All'}</strong>
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Button 
            onClick={() => {
              const nextState = !soundEnabled;
              setSoundEnabled(nextState);
              if (nextState) {
                // Play a brief sound to initialize and resume AudioContext immediately on user gesture
                try {
                  const AudioCtx = window.AudioContext || (window as any).webkitAudioContext;
                  if (AudioCtx) {
                    const audioCtx = new AudioCtx();
                    const oscillator = audioCtx.createOscillator();
                    const gainNode = audioCtx.createGain();
                    oscillator.type = 'sine';
                    oscillator.frequency.setValueAtTime(880, audioCtx.currentTime);
                    gainNode.gain.setValueAtTime(0.01, audioCtx.currentTime); // quiet confirmation
                    oscillator.connect(gainNode);
                    gainNode.connect(audioCtx.destination);
                    if (audioCtx.state === 'suspended') {
                      audioCtx.resume();
                    }
                    oscillator.start();
                    oscillator.stop(audioCtx.currentTime + 0.1);
                  }
                } catch (e) {}
              }
            }} 
            variant="secondary"
            className="flex items-center gap-1.5"
            icon={<Volume2 className={`w-4 h-4 ${soundEnabled ? 'text-brand-500' : 'text-slate-400'}`} />}
          >
            {soundEnabled ? 'Buzzer On' : 'Buzzer Off'}
          </Button>

          <Button 
            onClick={() => {
              const url = `/order-status?company_id=${activeCompany?.id || 2}${activeBranch?.id ? `&branch_id=${activeBranch.id}` : ''}`;
              window.open(url, '_blank');
            }} 
            variant="secondary"
            className="flex items-center gap-1.5"
            icon={<Monitor className="w-4 h-4 text-brand-550" />}
          >
            Launch Customer TV View
          </Button>

          <Button 
            onClick={() => fetchQueue()} 
            isLoading={isLoading} 
            variant="primary" 
            className="flex items-center gap-1.5"
            icon={<RefreshCw className="w-4 h-4" />}
          >
            Reload Queue
          </Button>
        </div>
      </div>

      {/* THREE LANE BOARD KANBAN */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 h-[calc(100vh-210px)] overflow-hidden">
        
        {/* COLUMN 1: PENDING ORDERS */}
        <div className="flex flex-col bg-slate-50 dark:bg-slate-900/40 border border-slate-100 dark:border-slate-800 rounded-3xl p-5 h-full overflow-hidden">
          <div className="flex items-center justify-between mb-4 border-b border-slate-200 dark:border-slate-800 pb-3">
            <div className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-amber-500 animate-ping" />
              <h3 className="font-bold text-sm text-slate-800 dark:text-white">New Tickets ({pendingOrders.length})</h3>
            </div>
            <span className="text-[10px] uppercase font-bold text-slate-400">Pending</span>
          </div>

          <div className="flex-grow overflow-y-auto flex flex-col gap-4 pr-1">
            {pendingOrders.length === 0 ? (
              <div className="h-full flex flex-col items-center justify-center text-slate-400 py-16 gap-2">
                <Monitor className="w-8 h-8 opacity-20" />
                <span className="text-xs">No new orders waiting</span>
              </div>
            ) : (
              pendingOrders.map(order => (
                <KdsTicketCard 
                  key={order.id} 
                  order={order}
                  getElapsedTime={getElapsedTime}
                  onAction={() => handleStatusTransition(order.id, 'preparing')}
                  actionLabel="Start Preparing"
                  actionColor="bg-amber-500 hover:bg-amber-600 text-white"
                  actionIcon={<Play className="w-3.5 h-3.5" />}
                />
              ))
            )}
          </div>
        </div>

        {/* COLUMN 2: IN PREPARATION */}
        <div className="flex flex-col bg-slate-50 dark:bg-slate-900/40 border border-slate-100 dark:border-slate-800 rounded-3xl p-5 h-full overflow-hidden">
          <div className="flex items-center justify-between mb-4 border-b border-slate-200 dark:border-slate-800 pb-3">
            <div className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-indigo-500 animate-pulse" />
              <h3 className="font-bold text-sm text-slate-800 dark:text-white">In Assembly ({preparingOrders.length})</h3>
            </div>
            <span className="text-[10px] uppercase font-bold text-slate-400">Preparing</span>
          </div>

          <div className="flex-grow overflow-y-auto flex flex-col gap-4 pr-1">
            {preparingOrders.length === 0 ? (
              <div className="h-full flex flex-col items-center justify-center text-slate-400 py-16 gap-2">
                <ChefHat className="w-8 h-8 opacity-20" />
                <span className="text-xs">No active food/stock prep</span>
              </div>
            ) : (
              preparingOrders.map(order => (
                <KdsTicketCard 
                  key={order.id} 
                  order={order}
                  getElapsedTime={getElapsedTime}
                  onAction={() => handleStatusTransition(order.id, 'ready')}
                  actionLabel="Mark as Ready"
                  actionColor="bg-brand-500 hover:bg-brand-600 text-white"
                  actionIcon={<ArrowRight className="w-3.5 h-3.5" />}
                />
              ))
            )}
          </div>
        </div>

        {/* COLUMN 3: READY ORDERS */}
        <div className="flex flex-col bg-slate-50 dark:bg-slate-900/40 border border-slate-100 dark:border-slate-800 rounded-3xl p-5 h-full overflow-hidden">
          <div className="flex items-center justify-between mb-4 border-b border-slate-200 dark:border-slate-800 pb-3">
            <div className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-emerald-500" />
              <h3 className="font-bold text-sm text-slate-800 dark:text-white">Ready for Pickup ({readyOrders.length})</h3>
            </div>
            <span className="text-[10px] uppercase font-bold text-slate-400">Ready</span>
          </div>

          <div className="flex-grow overflow-y-auto flex flex-col gap-4 pr-1">
            {readyOrders.length === 0 ? (
              <div className="h-full flex flex-col items-center justify-center text-slate-400 py-16 gap-2">
                <CheckCircle className="w-8 h-8 opacity-20" />
                <span className="text-xs">No orders awaiting dispatch</span>
              </div>
            ) : (
              readyOrders.map(order => (
                <KdsTicketCard 
                  key={order.id} 
                  order={order}
                  getElapsedTime={getElapsedTime}
                  onAction={() => handleStatusTransition(order.id, 'completed')}
                  actionLabel="Deliver & Clear"
                  actionColor="bg-emerald-500 hover:bg-emerald-600 text-white"
                  actionIcon={<CheckCircle className="w-3.5 h-3.5" />}
                />
              ))
            )}
          </div>
        </div>

      </div>

      {toastMsg && (
        <Toast
          message={toastMsg}
          onClose={() => setToastMsg('')}
        />
      )}

    </div>
  );
}

// Inner Ticket Card Component
function KdsTicketCard({ 
  order, getElapsedTime, onAction, actionLabel, actionColor, actionIcon 
}: { 
  order: any; 
  getElapsedTime: (d: string) => number; 
  onAction: () => void; 
  actionLabel: string;
  actionColor: string;
  actionIcon: React.ReactNode;
}) {
  const { activeCompany } = usePOSStore();
  const slaLimit = activeCompany?.settings?.kds_sla_limit || 10;
  const mins = getElapsedTime(order.sale_date);
  const isDelayed = mins >= slaLimit;

  return (
    <Card className={`p-4 flex flex-col gap-3 border transition-all text-left bg-white dark:bg-slate-900 ${
      isDelayed 
        ? 'border-red-500/60 dark:border-red-500/50 shadow-md shadow-red-500/5 animate-pulse-red-border' 
        : 'border-slate-100 dark:border-slate-800'
    }`}>
      
      {/* Ticket Header metadata */}
      <div className="flex items-start justify-between border-b border-slate-50 dark:border-slate-850 pb-2">
        <div className="flex flex-col gap-0.5 text-left">
          <div className="flex items-center gap-1.5">
            <span className="font-extrabold text-xs text-slate-800 dark:text-white font-mono uppercase">
              {order.invoice_number.split('-').slice(-2).join('-')}
            </span>
            {isDelayed && (
              <span className="text-[8px] uppercase font-black tracking-widest text-red-500 bg-red-500/10 px-2 py-0.5 rounded-full border border-red-500/20 animate-pulse shrink-0">
                Overdue
              </span>
            )}
          </div>
          <span className="text-[9px] text-slate-450 flex items-center gap-1">
            <User className="w-2.5 h-2.5 text-slate-400" /> Cashier ID: #{order.user_id}
          </span>
        </div>

        {/* Stopwatch */}
        <div className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[10px] font-bold shrink-0 ${
          isDelayed 
            ? 'bg-red-500/10 text-red-500 animate-pulse' 
            : 'bg-slate-100 dark:bg-slate-800 text-slate-500 dark:text-slate-400'
        }`}>
          <Clock className="w-3 h-3" />
          <span>{mins}m ({isDelayed ? `${mins - slaLimit}m overdue` : `${slaLimit - mins}m left`})</span>
        </div>
      </div>

      {/* Order list items */}
      <div className="flex flex-col gap-2 py-1">
        {order.items?.map((item: any, idx: number) => {
          return (
            <div key={idx} className="flex justify-between items-start text-xs leading-tight">
              <span className="font-semibold text-slate-700 dark:text-slate-300">
                <span className="font-black text-brand-600 dark:text-brand-400 mr-1.5">{item.quantity}x</span>
                {item.variant?.product?.name || `Product Variant`} <span className="text-[10px] text-slate-400 font-normal">({item.variant?.name || 'Standard'})</span>
              </span>
            </div>
          );
        })}
      </div>

      {/* Ticket Notes */}
      {order.notes && (
        <div className="bg-slate-50 dark:bg-slate-850/50 p-2 rounded-lg text-[10px] text-slate-450 italic leading-snug border-l-2 border-slate-300">
          Note: {order.notes}
        </div>
      )}

      {/* CTA Status progression button */}
      <button
        onClick={onAction}
        className={`w-full py-2.5 rounded-xl font-bold text-xs flex items-center justify-center gap-1.5 transition-colors ${actionColor}`}
      >
        {actionIcon}
        <span>{actionLabel}</span>
      </button>

    </Card>
  );
}
