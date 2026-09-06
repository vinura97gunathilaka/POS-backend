'use client';

import React from 'react';
import { Terminal, Shield, Eye, Calendar, RefreshCw, ShieldAlert } from 'lucide-react';
import { Card, Table, Button, Skeleton } from '@/components/UI';
import { apiClient } from '@/services/api';
import { usePOSStore } from '@/store/usePOSStore';
import { hasPermission } from '@/utils/permissions';

export default function AuditLogsPage() {
  const { currentUser } = usePOSStore();

  if (!currentUser || !hasPermission(currentUser, 'audit:read')) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] text-center p-6 bg-white dark:bg-slate-900 rounded-3xl border border-slate-100 dark:border-slate-800 shadow-sm text-left">
        <ShieldAlert className="w-16 h-16 text-red-500 mb-4 animate-bounce" />
        <h3 className="text-xl font-bold text-slate-800 dark:text-white mb-2">Access Denied</h3>
        <p className="text-sm text-slate-500 dark:text-slate-400 max-w-md">
          You do not have the required permissions (`audit:read`) to view the System Security Audit Trail logs. Please contact your company administrator.
        </p>
      </div>
    );
  }

  const [logs, setLogs] = React.useState<any[]>([]);
  const [page, setPage] = React.useState(1);
  const [totalPages, setTotalPages] = React.useState(1);
  const [isLoading, setIsLoading] = React.useState(false);

  const fetchLogs = async (pageNum: number) => {
    setIsLoading(true);
    try {
      const res = await apiClient.get('/logging/audit-logs', {
        params: { page: pageNum, limit: 15 }
      });
      if (res.data.success && res.data.data) {
        setLogs(res.data.data);
        const total = parseInt(res.headers['x-total-pages'] || '1');
        setTotalPages(total);
      }
    } catch (err) {}
    finally {
      setIsLoading(false);
    }
  };

  React.useEffect(() => {
    fetchLogs(page);
  }, [page]);

  return (
    <div className="flex flex-col gap-6 text-left">
      
      {/* Banner */}
      <div className="flex items-center justify-between">
        <div className="flex flex-col gap-1">
          <h2 className="text-2xl font-bold dark:text-white">System Security Audit Trail</h2>
          <p className="text-xs text-slate-400">Strictly monitors all modifications, login activities, and cart cancellations.</p>
        </div>
        <Button onClick={() => fetchLogs(page)} variant="secondary" icon={<RefreshCw className="w-4 h-4" />} isLoading={isLoading}>
          Reload Feed
        </Button>
      </div>

      <Card className="p-6">
        <div className="flex items-center gap-2 mb-4">
          <Shield className="w-5 h-5 text-brand-500" />
          <h3 className="font-bold text-base text-slate-800 dark:text-white">Audit Log Listing</h3>
        </div>

        {isLoading ? (
          <div className="flex flex-col gap-3 py-6">
            <Skeleton className="h-10 w-full" />
            <Skeleton className="h-10 w-full" />
            <Skeleton className="h-10 w-full" />
          </div>
        ) : logs.length === 0 ? (
          <span className="text-sm text-slate-400 text-center py-10">No audit log records found.</span>
        ) : (
          <>
            <Table
              headers={["Timestamp", "Operator", "Security Action", "IP Address"]}
              rows={logs.map((log, idx) => [
                <span key={1} className="font-mono text-[10px] text-slate-400">
                  {new Date(log.created_at).toLocaleString()}
                </span>,
                <span key={2} className="font-semibold text-slate-700 dark:text-slate-200">
                  {log.user_name || `User #${log.user_id || 'System'}`}
                </span>,
                <span key={3} className="px-2 py-1 bg-violet-500/10 text-violet-500 rounded-lg text-[10px] font-bold uppercase tracking-wider font-mono">
                  {log.action}
                </span>,
                <span key={4} className="font-mono text-xs text-slate-400">{log.ip_address || 'N/A'}</span>
              ])}
            />

            {/* Pagination Controls */}
            <div className="flex items-center justify-between border-t border-slate-100 dark:border-slate-800 pt-4 mt-4 text-xs font-sans">
              <Button 
                onClick={() => setPage(p => Math.max(1, p - 1))}
                disabled={page === 1 || isLoading}
                variant="secondary"
                className="py-1.5 px-3 font-semibold"
              >
                Previous
              </Button>
              <span className="font-medium text-slate-500 dark:text-slate-400">
                Page {page} of {totalPages}
              </span>
              <Button 
                onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                disabled={page === totalPages || isLoading}
                variant="secondary"
                className="py-1.5 px-3 font-semibold"
              >
                Next
              </Button>
            </div>
          </>
        )}
      </Card>

    </div>
  );
}
