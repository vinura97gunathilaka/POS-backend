'use client';

import React from 'react';
import { 
  TrendingUp, DollarSign, Percent, ShoppingBag, 
  Users, BarChart2, Calendar, Store, ShieldAlert,
  ArrowUpRight, RefreshCw, Layers, CreditCard
} from 'lucide-react';
import { Card, Table, Button, Select, Skeleton } from '@/components/UI';
import { apiClient } from '@/services/api';
import { usePOSStore } from '@/store/usePOSStore';
import { hasPermission } from '@/utils/permissions';
import { 
  AreaChart, Area, XAxis, YAxis, CartesianGrid, 
  Tooltip, ResponsiveContainer, PieChart, Pie, Cell, Legend 
} from 'recharts';

export default function AnalyticsDashboardPage() {
  const { currentUser, activeBranch } = usePOSStore();

  const [activeTab, setActiveTab] = React.useState<'executive' | 'auditing' | 'feedback'>('executive');
  const [preset, setPreset] = React.useState<string>('30days');
  const [startDate, setStartDate] = React.useState<string>('');
  const [endDate, setEndDate] = React.useState<string>('');
  const [branchId, setBranchId] = React.useState<string>('all');
  const [branches, setBranches] = React.useState<any[]>([]);
  const [data, setData] = React.useState<any>(null);
  const [isLoading, setIsLoading] = React.useState<boolean>(true);

  // Pagination and state for Security Audit Feed
  const [feedLogs, setFeedLogs] = React.useState<any[]>([]);
  const [feedPage, setFeedPage] = React.useState<number>(1);
  const [feedTotalPages, setFeedTotalPages] = React.useState<number>(1);
  const [isFeedLoading, setIsFeedLoading] = React.useState<boolean>(false);

  // CSAT rating feedback analytics states
  const [csatData, setCsatData] = React.useState<any>(null);
  const [csatPage, setCsatPage] = React.useState<number>(1);
  const [csatTotalPages, setCsatTotalPages] = React.useState<number>(1);
  const [isCsatLoading, setIsCsatLoading] = React.useState<boolean>(false);

  // Define tailored colors for visual metrics
  const PIE_COLORS = ['#8b5cf6', '#10b981', '#f59e0b', '#ef4444', '#06b6d4', '#ec4899'];

  // Check authorization
  const isAuthorized = React.useMemo(() => {
    if (!currentUser) return false;
    return currentUser.is_superadmin || 
           hasPermission(currentUser, 'finance:manage') || 
           hasPermission(currentUser, 'audit:read');
  }, [currentUser]);

  // Load branches
  React.useEffect(() => {
    if (!isAuthorized) return;
    apiClient.get('/branches')
      .then((res) => {
        if (res.data.success && res.data.data) {
          setBranches(res.data.data);
        }
      })
      .catch(() => {});
  }, [isAuthorized]);

  // Handle Preset Changes
  React.useEffect(() => {
    const today = new Date();
    let start = new Date();
    
    if (preset === 'today') {
      start.setHours(0, 0, 0, 0);
    } else if (preset === '7days') {
      start.setDate(today.getDate() - 7);
    } else if (preset === '30days') {
      start.setDate(today.getDate() - 30);
    } else if (preset === 'ytd') {
      start = new Date(today.getFullYear(), 0, 1);
    } else {
      // Custom range: do not auto-overwrite start/end
      return;
    }

    setStartDate(start.toISOString().split('T')[0]);
    setEndDate(today.toISOString().split('T')[0]);
  }, [preset]);

  // Fetch Analytics
  const fetchAnalytics = React.useCallback(async () => {
    if (!isAuthorized) return;
    setIsLoading(true);
    try {
      const params: any = {};
      if (startDate) params.start_date = startDate;
      if (endDate) params.end_date = endDate;
      if (branchId !== 'all') params.branch_id = parseInt(branchId);

      const res = await apiClient.get('/analytics/dashboard', { params });
      if (res.data.success && res.data.data) {
        setData(res.data.data);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  }, [isAuthorized, startDate, endDate, branchId]);

  React.useEffect(() => {
    if (startDate && endDate) {
      fetchAnalytics();
    }
  }, [startDate, endDate, branchId, fetchAnalytics]);

  const fetchFeedLogs = React.useCallback(async (page: number) => {
    if (!isAuthorized) return;
    setIsFeedLoading(true);
    try {
      const res = await apiClient.get('/logging/audit-logs', {
        params: { page, limit: 10 }
      });
      if (res.data.success && res.data.data) {
        setFeedLogs(res.data.data);
        const totalPages = parseInt(res.headers['x-total-pages'] || '1');
        setFeedTotalPages(totalPages);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setIsFeedLoading(false);
    }
  }, [isAuthorized]);

  React.useEffect(() => {
    if (isAuthorized) {
      fetchFeedLogs(feedPage);
    }
  }, [feedPage, isAuthorized, fetchFeedLogs]);

  const fetchCsatFeedback = React.useCallback(async (page: number) => {
    if (!isAuthorized) return;
    setIsCsatLoading(true);
    try {
      const params: any = { page, limit: 10 };
      if (branchId !== 'all') params.branch_id = parseInt(branchId);
      const res = await apiClient.get('/analytics/csat', { params });
      if (res.data.success && res.data.data) {
        setCsatData(res.data.data);
        setCsatTotalPages(res.data.data.pagination.pages || 1);
      }
    } catch (err) {
      console.error("Failed to load CSAT feedback metrics", err);
    } finally {
      setIsCsatLoading(false);
    }
  }, [isAuthorized, branchId]);

  React.useEffect(() => {
    if (activeTab === 'feedback' && isAuthorized) {
      fetchCsatFeedback(csatPage);
    }
  }, [activeTab, csatPage, branchId, isAuthorized, fetchCsatFeedback]);

  if (!currentUser) return null;

  if (!isAuthorized) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] text-center p-6 bg-white dark:bg-slate-900 rounded-3xl border border-slate-100 dark:border-slate-800 shadow-sm text-left">
        <ShieldAlert className="w-16 h-16 text-red-500 mb-4 animate-bounce" />
        <h3 className="text-xl font-bold text-slate-800 dark:text-white mb-2">Access Denied</h3>
        <p className="text-sm text-slate-500 dark:text-slate-400 max-w-md leading-normal">
          You do not have the required privileges to view store performance metrics and reports. Contact your company administrator.
        </p>
      </div>
    );
  }

  const summary = data?.summary || {
    total_revenue: 0,
    total_cost: 0,
    total_profit: 0,
    margin_percent: 0,
    total_sales_count: 0,
    average_order_value: 0,
    total_tax: 0,
    total_discount: 0
  };

  const cards = [
    { name: 'Gross Revenue', value: `Rs. ${summary.total_revenue.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`, label: 'Sales receipts in range', icon: <DollarSign className="w-5 h-5 text-brand-500" />, bg: 'bg-brand-500/10' },
    { name: 'Gross Profit', value: `Rs. ${summary.total_profit.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`, label: `COGS: Rs. ${summary.total_cost.toLocaleString()}`, icon: <TrendingUp className="w-5 h-5 text-emerald-500" />, bg: 'bg-emerald-500/10' },
    { name: 'Gross Margin', value: `${summary.margin_percent.toFixed(2)}%`, label: 'Revenue profitability ratio', icon: <Percent className="w-5 h-5 text-violet-500" />, bg: 'bg-violet-500/10' },
    { name: 'Average Ticket Size', value: `Rs. ${summary.average_order_value.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`, label: `${summary.total_sales_count} Transactions completed`, icon: <ShoppingBag className="w-5 h-5 text-amber-500" />, bg: 'bg-amber-500/10' }
  ];

  return (
    <div className="flex flex-col gap-6 text-left pb-10">
      
      {/* HEADER CONTROLS */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-100 dark:border-slate-800/80 pb-4">
        <div className="flex flex-col gap-1">
          <h2 className="text-2xl font-bold dark:text-white">Business Intelligence & Reports</h2>
          <p className="text-xs text-slate-400">Detailed overview of revenue streams, margins, and operational audit logs.</p>
        </div>
        
        {/* Date presets & filters */}
        <div className="flex flex-wrap items-center gap-3 bg-white dark:bg-slate-900 p-2.5 rounded-2xl border border-slate-100 dark:border-slate-800/80 shadow-sm shrink-0">
          
          <div className="flex items-center gap-1 bg-slate-100 dark:bg-slate-800 p-1 rounded-xl text-xs font-semibold">
            {[
              { id: 'today', name: 'Today' },
              { id: '7days', name: '7D' },
              { id: '30days', name: '30D' },
              { id: 'ytd', name: 'YTD' },
              { id: 'custom', name: 'Custom' }
            ].map(p => (
              <button
                key={p.id}
                onClick={() => setPreset(p.id)}
                className={`px-3 py-1.5 rounded-lg transition-colors ${preset === p.id ? 'bg-white dark:bg-slate-700 text-brand-600 dark:text-white shadow-sm' : 'text-slate-500 dark:text-slate-400'}`}
              >
                {p.name}
              </button>
            ))}
          </div>

          {preset === 'custom' && (
            <div className="flex items-center gap-2">
              <input
                type="date"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
                className="bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700/60 rounded-xl px-2.5 py-1.5 text-xs focus:outline-none focus:ring-1 focus:ring-brand-500 text-slate-700 dark:text-slate-200"
              />
              <span className="text-xs text-slate-400">to</span>
              <input
                type="date"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
                className="bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700/60 rounded-xl px-2.5 py-1.5 text-xs focus:outline-none focus:ring-1 focus:ring-brand-500 text-slate-700 dark:text-slate-200"
              />
            </div>
          )}

          {/* Branch filter dropdown */}
          <select
            value={branchId}
            onChange={(e) => setBranchId(e.target.value)}
            className="bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700/60 rounded-xl px-2.5 py-1.5 text-xs focus:outline-none focus:ring-1 focus:ring-brand-500 font-semibold text-slate-700 dark:text-slate-200"
          >
            <option value="all">All Branches</option>
            {branches.map(b => (
              <option key={b.id} value={b.id.toString()}>{b.name}</option>
            ))}
          </select>

          <Button onClick={fetchAnalytics} variant="ghost" className="p-2 shrink-0 min-h-[auto]" isLoading={isLoading}>
            <RefreshCw className="w-4 h-4" />
          </Button>

        </div>
      </div>

      {/* Tab Switching */}
      <div className="flex gap-4 border-b border-slate-200 dark:border-slate-800 text-sm font-semibold mb-2">
        <button
          onClick={() => setActiveTab('executive')}
          className={`pb-3 px-1 border-b-2 transition-colors ${activeTab === 'executive' ? 'border-brand-500 text-brand-600 dark:text-white font-bold' : 'border-transparent text-slate-500 hover:text-slate-700'}`}
        >
          Executive Summary Metrics
        </button>
        <button
          onClick={() => setActiveTab('auditing')}
          className={`pb-3 px-1 border-b-2 transition-colors ${activeTab === 'auditing' ? 'border-brand-500 text-brand-600 dark:text-white font-bold' : 'border-transparent text-slate-500 hover:text-slate-700'}`}
        >
          Intraday Heatmaps & Cashier Audits
        </button>
        <button
          onClick={() => setActiveTab('feedback')}
          className={`pb-3 px-1 border-b-2 transition-colors ${activeTab === 'feedback' ? 'border-brand-500 text-brand-600 dark:text-white font-bold' : 'border-transparent text-slate-500 hover:text-slate-700'}`}
        >
          Customer Feedback (CSAT)
        </button>
      </div>

      {activeTab === 'executive' && (
        <>
          {/* KPI METRIC CARDS */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {cards.map((card, idx) => (
              <Card key={idx} className="flex items-center justify-between p-6">
                <div className="flex flex-col gap-1">
                  <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">{card.name}</span>
                  {isLoading ? (
                    <Skeleton className="h-8 w-36 mt-1" />
                  ) : (
                    <span className="text-2xl font-extrabold text-slate-800 dark:text-white mt-1">{card.value}</span>
                  )}
                  <span className="text-[10px] text-slate-400 mt-2 font-bold">{card.label}</span>
                </div>
                <div className={`p-3.5 rounded-2xl ${card.bg}`}>
                  {card.icon}
                </div>
              </Card>
            ))}
          </div>

          {/* REVENUE VS PROFIT PROGRESSION AREA CHART */}
          <Card className="p-6 flex flex-col gap-4">
            <div className="flex items-center justify-between">
              <div className="flex flex-col gap-0.5">
                <h3 className="font-bold text-base text-slate-800 dark:text-white">Revenue & Profit Progression</h3>
                <p className="text-[11px] text-slate-400">Comparing gross receipts against calculated profits in the active date range.</p>
              </div>
              <div className="flex items-center gap-3 text-xs font-semibold text-slate-500">
                <div className="flex items-center gap-1.5">
                  <span className="w-3 h-3 rounded-full bg-brand-500" />
                  <span>Revenue</span>
                </div>
                <div className="flex items-center gap-1.5">
                  <span className="w-3 h-3 rounded-full bg-emerald-500" />
                  <span>Profit</span>
                </div>
              </div>
            </div>

            <div className="w-full h-80 mt-4">
              {isLoading ? (
                <Skeleton className="w-full h-full" />
              ) : (
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={data?.sales_trend || []}>
                    <defs>
                      <linearGradient id="colorRev" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.2}/>
                        <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0}/>
                      </linearGradient>
                      <linearGradient id="colorProf" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#10b981" stopOpacity={0.2}/>
                        <stop offset="95%" stopColor="#10b981" stopOpacity={0}/>
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="rgba(255,255,255,0.05)" />
                    <XAxis dataKey="date" stroke="#94a3b8" fontSize={11} tickLine={false} axisLine={false} />
                    <YAxis stroke="#94a3b8" fontSize={11} tickLine={false} axisLine={false} />
                    <Tooltip 
                      contentStyle={{ background: '#0f172a', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '12px' }}
                      labelStyle={{ color: '#fff', fontWeight: 'bold' }}
                    />
                    <Area type="monotone" dataKey="revenue" name="Revenue" stroke="#8b5cf6" strokeWidth={3} fillOpacity={1} fill="url(#colorRev)" />
                    <Area type="monotone" dataKey="profit" name="Profit" stroke="#10b981" strokeWidth={3} fillOpacity={1} fill="url(#colorProf)" />
                  </AreaChart>
                </ResponsiveContainer>
              )}
            </div>
          </Card>

          {/* MID PANEL SECTION: DUAL GRID SPLIT */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
            
            {/* Category Split Chart */}
            <Card className="lg:col-span-6 p-6 flex flex-col gap-4">
              <h3 className="font-bold text-base text-slate-800 dark:text-white">Revenue by Sales Category</h3>
              <p className="text-[11px] text-slate-400">Proportional distribution of sales receipts by product categories.</p>
              
              <div className="flex flex-col sm:flex-row items-center justify-center gap-6 mt-4 min-h-[220px]">
                {isLoading ? (
                  <Skeleton className="w-48 h-48 rounded-full animate-pulse" />
                ) : (data?.category_breakdown?.length || 0) === 0 ? (
                  <span className="text-xs text-slate-400">No category breakdown data.</span>
                ) : (
                  <>
                    <div className="w-48 h-48 relative flex-shrink-0">
                      <ResponsiveContainer width="100%" height="100%">
                        <PieChart>
                          <Pie
                            data={data?.category_breakdown || []}
                            cx="50%"
                            cy="50%"
                            innerRadius={60}
                            outerRadius={80}
                            paddingAngle={3}
                            dataKey="revenue"
                          >
                            {(data?.category_breakdown || []).map((entry: any, index: number) => (
                              <Cell key={`cell-${index}`} fill={PIE_COLORS[index % PIE_COLORS.length]} />
                            ))}
                          </Pie>
                          <Tooltip formatter={(val) => `Rs. ${parseFloat(val as string).toLocaleString()}`} />
                        </PieChart>
                      </ResponsiveContainer>
                      <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
                        <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider">Top Category</span>
                        <span className="text-sm font-extrabold text-slate-700 dark:text-slate-200 mt-0.5 truncate max-w-[120px]">
                          {data?.category_breakdown?.[0]?.category_name || 'N/A'}
                        </span>
                      </div>
                    </div>
                    
                    {/* Visual Legend checklist */}
                    <div className="flex flex-col gap-2 flex-grow w-full text-xs">
                      {(data?.category_breakdown || []).map((cat: any, index: number) => (
                        <div key={index} className="flex items-center justify-between gap-3 p-1">
                          <div className="flex items-center gap-2 min-w-0">
                            <span className="w-2.5 h-2.5 rounded-full shrink-0" style={{ backgroundColor: PIE_COLORS[index % PIE_COLORS.length] }} />
                            <span className="font-semibold text-slate-600 dark:text-slate-300 truncate">{cat.category_name}</span>
                          </div>
                          <div className="flex items-center gap-2 shrink-0">
                            <span className="font-extrabold text-slate-800 dark:text-slate-200">Rs. {cat.revenue.toLocaleString()}</span>
                            <span className="text-[10px] font-bold text-slate-400 bg-slate-100 dark:bg-slate-850 px-1.5 py-0.5 rounded">
                              {cat.percentage.toFixed(1)}%
                            </span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </>
                )}
              </div>
            </Card>

            {/* Payment Methods Split */}
            <Card className="lg:col-span-6 p-6 flex flex-col gap-4">
              <h3 className="font-bold text-base text-slate-800 dark:text-white">Payment Method Preferences</h3>
              <p className="text-[11px] text-slate-400">Visual share of checkout billing settle methods used in range.</p>

              <div className="flex flex-col gap-4 mt-4 overflow-y-auto max-h-[260px] pr-1">
                {isLoading ? (
                  <div className="flex flex-col gap-3">
                    <Skeleton className="h-10 w-full" />
                    <Skeleton className="h-10 w-full" />
                    <Skeleton className="h-10 w-full" />
                  </div>
                ) : (data?.payment_methods?.length || 0) === 0 ? (
                  <span className="text-xs text-slate-400 text-center py-10">No payment transaction records.</span>
                ) : (
                  (data?.payment_methods || []).map((method: any, idx: number) => (
                    <div key={idx} className="flex flex-col gap-1.5">
                      <div className="flex items-center justify-between text-xs font-semibold">
                        <span className="flex items-center gap-1.5 text-slate-600 dark:text-slate-300">
                          <CreditCard className="w-3.5 h-3.5 text-brand-500" />
                          {method.method}
                        </span>
                        <span className="font-extrabold text-slate-800 dark:text-slate-200">
                          Rs. {method.amount.toLocaleString()} ({method.percentage}%)
                        </span>
                      </div>
                      <div className="w-full h-2.5 rounded-full bg-slate-100 dark:bg-slate-800 overflow-hidden">
                        <div 
                          className="h-full bg-brand-500 rounded-full transition-all duration-300"
                          style={{ width: `${method.percentage}%` }}
                        />
                      </div>
                    </div>
                  ))
                )}
              </div>
            </Card>
          </div>

          {/* LOWER PANEL SECTION: TABLES GRID */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
            
            {/* Top 5 Products Table */}
            <Card className="lg:col-span-7 p-6 flex flex-col gap-4">
              <div className="flex items-center justify-between">
                <h3 className="font-bold text-base text-slate-800 dark:text-white">Top 5 Best-Selling Products</h3>
                <span className="text-[10px] font-bold text-slate-400 bg-slate-100 dark:bg-slate-800 px-2 py-1 rounded-lg">Product Leaderboard</span>
              </div>
              <p className="text-[11px] text-slate-400 leading-normal">
                Calculated based on unit volumes sold in active duration, displaying margins and net earnings.
              </p>

              <div className="mt-2">
                {isLoading ? (
                  <Skeleton className="h-44 w-full" />
                ) : (
                  <Table
                    headers={["Product / SKU", "Qty Sold", "Gross Revenue", "Margin / Profit"]}
                    rows={(data?.top_products || []).map((prod: any, idx: number) => [
                      <div key={1} className="flex flex-col text-left min-w-0">
                        <span className="font-bold text-slate-700 dark:text-slate-200 truncate">{prod.product_name}</span>
                        <span className="text-[10px] text-slate-400 font-mono">SKU: {prod.sku}</span>
                      </div>,
                      <span key={2} className="font-extrabold text-slate-700 dark:text-slate-350">{prod.quantity_sold} units</span>,
                      <span key={3} className="font-extrabold text-slate-800 dark:text-white">Rs. {prod.revenue.toLocaleString()}</span>,
                      <div key={4} className="flex flex-col items-end">
                        <span className="font-bold text-emerald-500">Rs. {prod.profit.toLocaleString()}</span>
                        <span className="text-[9px] text-slate-450">Margin: {((prod.profit / prod.revenue) * 100).toFixed(1)}%</span>
                      </div>
                    ])}
                  />
                )}
              </div>
            </Card>

            {/* Cashier performance Leaderboard */}
            <Card className="lg:col-span-5 p-6 flex flex-col gap-4">
              <div className="flex items-center justify-between">
                <h3 className="font-bold text-base text-slate-800 dark:text-white">Cashier Performance Leaderboard</h3>
                <span className="text-[10px] font-bold text-slate-400 bg-slate-100 dark:bg-slate-800 px-2 py-1 rounded-lg">Staff Ranking</span>
              </div>
              <p className="text-[11px] text-slate-400 leading-normal">
                Employees ranked by completed receipts value and ticket averages.
              </p>

              <div className="mt-2">
                {isLoading ? (
                  <Skeleton className="h-44 w-full" />
                ) : (
                  <Table
                    headers={["Cashier Staff", "Tickets", "AOV", "Total Revenue"]}
                    rows={(data?.cashier_performance || []).map((cashier: any, idx: number) => [
                      <span key={1} className="font-bold text-slate-700 dark:text-slate-200">{cashier.cashier_name}</span>,
                      <span key={2} className="font-semibold text-slate-500 font-mono">{cashier.transactions}</span>,
                      <span key={3} className="font-semibold text-slate-600 dark:text-slate-400 font-mono">Rs. {cashier.aov.toLocaleString()}</span>,
                      <span key={4} className="font-extrabold text-brand-500">Rs. {cashier.revenue.toLocaleString()}</span>
                    ])}
                  />
                )}
              </div>
            </Card>
          </div>

          {/* BRANCH STATS (If viewing all branches) */}
          {branchId === 'all' && (data?.branch_performance?.length || 0) > 1 && (
            <Card className="p-6 flex flex-col gap-4">
              <div className="flex items-center justify-between">
                <h3 className="font-bold text-base text-slate-800 dark:text-white">Branch-wise Sales Performance</h3>
                <span className="text-[10px] font-bold text-slate-400 bg-slate-100 dark:bg-slate-800 px-2 py-1 rounded-lg">Multi-Branch Analytics</span>
              </div>
              <div className="mt-2">
                {isLoading ? (
                  <Skeleton className="h-32 w-full" />
                ) : (
                  <Table
                    headers={["Branch Location", "Tickets Completed", "Average Ticket Size (AOV)", "Aggregate Net Revenue"]}
                    rows={(data?.branch_performance || []).map((branch: any, idx: number) => [
                      <div key={1} className="flex items-center gap-2">
                        <Store className="w-4 h-4 text-brand-500" />
                        <span className="font-bold text-slate-700 dark:text-slate-200">{branch.branch_name}</span>
                      </div>,
                      <span key={2} className="font-semibold text-slate-500 font-mono">{branch.transactions} checkouts</span>,
                      <span key={3} className="font-semibold text-slate-600 dark:text-slate-450 font-mono">Rs. {branch.aov.toLocaleString()}</span>,
                      <span key={4} className="font-extrabold text-emerald-500">Rs. {branch.revenue.toLocaleString()}</span>
                    ])}
                  />
                )}
              </div>
            </Card>
          )}
        </>
      )}

      {activeTab === 'auditing' && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 animate-fade-in text-left">
          
          {/* LEFT SECTION: HEATMAP & CASHIER VARIANCE LIST */}
          <div className="lg:col-span-8 flex flex-col gap-6">
            
            {/* Heatmap Grid card */}
            <Card className="p-6 flex flex-col gap-4">
              <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-800 pb-3">
                <div className="flex flex-col gap-0.5">
                  <h3 className="font-bold text-base text-slate-800 dark:text-white">Intraday Sales Volume Heatmap</h3>
                  <p className="text-[11px] text-slate-400">Identify rush-hours based on transaction counts grouped by weekday and hour slots.</p>
                </div>
              </div>

              {isLoading ? (
                <Skeleton className="h-64 w-full" />
              ) : (
                <div className="overflow-x-auto pb-2 mt-2">
                  <div className="min-w-[700px] flex flex-col gap-1.5">
                    {/* Hours Header Row */}
                    <div className="flex items-center text-[10px] font-bold text-slate-400 border-b border-slate-100 dark:border-slate-800 pb-1.5">
                      <div className="w-16 shrink-0 text-left">Day</div>
                      {Array.from({ length: 24 }).map((_, h) => (
                        <div key={h} className="flex-1 text-center font-mono">
                          {h.toString().padStart(2, '0')}:00
                        </div>
                      ))}
                    </div>

                    {/* Weekday Row Grids */}
                    {["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"].map(day => (
                      <div key={day} className="flex items-center gap-1">
                        {/* Day Column label */}
                        <div className="w-16 shrink-0 text-xs font-bold text-slate-650 dark:text-slate-350">{day}</div>
                        
                        {/* 24 Hour blocks */}
                        {Array.from({ length: 24 }).map((_, h) => {
                          const matchingHourData = data?.intraday_heatmap?.find((x: any) => x.day === day && x.hour === h) || { transactions: 0, revenue: 0 };
                          const txs = matchingHourData.transactions;
                          
                          // Color density calculation
                          let bgClass = "bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-750"; // empty
                          if (txs > 0 && txs <= 2) bgClass = "bg-emerald-500/15 hover:bg-emerald-500/25 text-emerald-600";
                          else if (txs > 2 && txs <= 5) bgClass = "bg-emerald-500/35 hover:bg-emerald-500/45 text-emerald-700";
                          else if (txs > 5 && txs <= 10) bgClass = "bg-emerald-500/65 hover:bg-emerald-500/75 text-emerald-50";
                          else if (txs > 10) bgClass = "bg-emerald-500 text-white shadow-sm shadow-emerald-500/20";

                          return (
                            <div 
                              key={h}
                              className={`flex-1 min-h-[30px] rounded-lg transition-all flex items-center justify-center font-mono text-[10px] font-extrabold select-none cursor-pointer ${bgClass}`}
                              title={`${day} at ${h.toString().padStart(2, '0')}:00\nTransactions: ${txs}\nRevenue: Rs. ${matchingHourData.revenue.toLocaleString()}`}
                            >
                              {txs > 0 ? txs : ''}
                            </div>
                          );
                        })}
                      </div>
                    ))}
                  </div>

                  {/* Shading Color Legend key */}
                  <div className="flex items-center gap-4 text-[10px] font-bold text-slate-400 mt-4 justify-end">
                    <span>Transaction Density:</span>
                    <div className="flex items-center gap-1.5">
                      <div className="w-3.5 h-3.5 rounded bg-slate-100 dark:bg-slate-800" />
                      <span>0</span>
                    </div>
                    <div className="flex items-center gap-1.5">
                      <div className="w-3.5 h-3.5 rounded bg-emerald-500/15" />
                      <span>1-2</span>
                    </div>
                    <div className="flex items-center gap-1.5">
                      <div className="w-3.5 h-3.5 rounded bg-emerald-500/35" />
                      <span>3-5</span>
                    </div>
                    <div className="flex items-center gap-1.5">
                      <div className="w-3.5 h-3.5 rounded bg-emerald-500/65" />
                      <span>6-10</span>
                    </div>
                    <div className="flex items-center gap-1.5">
                      <div className="w-3.5 h-3.5 rounded bg-emerald-500" />
                      <span>10+ (Peak)</span>
                    </div>
                  </div>

                </div>
              )}
            </Card>

            {/* Cashier Discrepancy Ledger Table */}
            <Card className="p-6 flex flex-col gap-4">
              <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-800 pb-3">
                <div className="flex flex-col gap-0.5">
                  <h3 className="font-bold text-base text-slate-800 dark:text-white">Cashier Auditing & Drawer Variances</h3>
                  <p className="text-[11px] text-slate-400">Track cashier transaction velocity, total voided invoices, and cash drawer discrepancies.</p>
                </div>
              </div>

              <div className="mt-2">
                {isLoading ? (
                  <Skeleton className="h-44 w-full" />
                ) : (
                  <Table
                    headers={["Cashier Staff", "Receipts Value", "Transaction Count", "Void Count", "Shift Discrepancy"]}
                    rows={(data?.cashier_performance || []).map((cashier: any, idx: number) => {
                      const variance = cashier.total_variance || 0;
                      let varianceText = `Rs. ${variance.toLocaleString()}`;
                      let varianceClass = "text-slate-500 dark:text-slate-450 font-bold";

                      if (variance < 0) {
                        varianceText = `- Rs. ${Math.abs(variance).toLocaleString()}`;
                        varianceClass = "text-red-500 font-extrabold animate-pulse";
                      } else if (variance > 0) {
                        varianceText = `+ Rs. ${variance.toLocaleString()}`;
                        varianceClass = "text-emerald-500 font-extrabold";
                      }

                      return [
                        <span key={1} className="font-bold text-slate-700 dark:text-slate-200">{cashier.cashier_name}</span>,
                        <span key={2} className="font-semibold text-slate-550 font-mono">Rs. {cashier.revenue.toLocaleString()}</span>,
                        <span key={3} className="font-semibold text-slate-500 font-mono">{cashier.transactions} checkouts</span>,
                        <span key={4} className={`font-extrabold font-mono ${cashier.voids_count > 0 ? 'text-amber-500' : 'text-slate-400'}`}>
                          {cashier.voids_count || 0} voids
                        </span>,
                        <span key={5} className={`font-mono ${varianceClass}`}>{varianceText}</span>
                      ];
                    })}
                  />
                )}
              </div>
            </Card>

          </div>

          {/* RIGHT SECTION: SECURITY AUDIT TIMELINE FEED */}
          <div className="lg:col-span-4 flex flex-col h-full">
            <Card className="p-6 flex flex-col gap-4 h-full overflow-hidden min-h-[500px]">
              <div className="flex flex-col gap-0.5 border-b border-slate-100 dark:border-slate-800 pb-3 shrink-0">
                <h3 className="font-bold text-base text-slate-800 dark:text-white">Security Audit Log Feed</h3>
                <p className="text-[10px] text-slate-450 uppercase tracking-widest font-bold mt-1">Live Employee Activity Logs</p>
              </div>

              <div className="flex-grow overflow-y-auto pr-1 flex flex-col gap-4 mt-2">
                {isFeedLoading ? (
                  <div className="flex flex-col gap-3">
                    <Skeleton className="h-10 w-full" />
                    <Skeleton className="h-10 w-full" />
                    <Skeleton className="h-10 w-full" />
                  </div>
                ) : feedLogs.length === 0 ? (
                  <span className="text-xs text-slate-400 text-center py-10">No recent security audit records.</span>
                ) : (
                  feedLogs.map((log: any, idx: number) => {
                    const cleanDate = new Date(log.created_at).toLocaleTimeString(undefined, { hour: '2-digit', minute: '2-digit', second: '2-digit' });
                    
                    // Style config mapping for action kinds
                    let actionLabel = log.action;
                    let badgeColor = "bg-slate-100 text-slate-700 dark:bg-slate-850 dark:text-slate-400 border-slate-200/50";
                    
                    if (log.action === "sale_checkout") {
                      actionLabel = "POS checkout";
                      badgeColor = "bg-emerald-500/10 text-emerald-600 dark:bg-emerald-950/20 dark:text-emerald-400 border-emerald-500/20";
                    } else if (log.action === "sale_cancellation") {
                      actionLabel = "Void override";
                      badgeColor = "bg-red-500/10 text-red-600 dark:bg-red-950/20 dark:text-red-400 border-red-500/20 font-bold";
                    } else if (log.action === "held_sale_park") {
                      actionLabel = "Park bill";
                      badgeColor = "bg-amber-500/10 text-amber-600 dark:bg-amber-950/20 dark:text-amber-400 border-amber-500/20";
                    } else if (log.action === "held_sale_recall") {
                      actionLabel = "Recall bill";
                      badgeColor = "bg-blue-500/10 text-blue-600 dark:bg-blue-950/20 dark:text-blue-400 border-blue-500/20";
                    } else if (log.action === "shift_open") {
                      actionLabel = "Shift open";
                      badgeColor = "bg-violet-500/10 text-violet-600 dark:bg-violet-950/20 dark:text-violet-400 border-violet-500/20";
                    } else if (log.action === "shift_close") {
                      actionLabel = "Shift close";
                      badgeColor = "bg-fuchsia-500/10 text-fuchsia-600 dark:bg-fuchsia-950/20 dark:text-fuchsia-400 border-fuchsia-500/20";
                    }

                    return (
                      <div key={idx} className="flex gap-3 border-l-2 border-slate-100 dark:border-slate-850 pl-3.5 relative py-1 text-left text-xs leading-normal">
                        {/* Glow indicator dot */}
                        <div className="absolute w-2 h-2 rounded-full -left-[5px] top-[14px] bg-slate-350 dark:bg-slate-700" />
                        
                        <div className="flex flex-col gap-1 w-full min-w-0">
                          <div className="flex items-center justify-between gap-2">
                            <span className="font-extrabold text-slate-800 dark:text-slate-200 truncate">{log.user_name}</span>
                            <span className="text-[9px] text-slate-400 shrink-0 font-mono font-bold bg-slate-50 dark:bg-slate-850 px-1 py-0.5 rounded">{cleanDate}</span>
                          </div>
                          
                          <div className="flex items-center gap-1.5 mt-0.5">
                            <span className={`px-2 py-0.5 rounded-full text-[9px] uppercase tracking-wider font-bold border shrink-0 ${badgeColor}`}>
                              {actionLabel}
                            </span>
                            
                            {/* Summary description details */}
                            <span className="text-[10px] text-slate-450 truncate">
                              {log.action === "sale_checkout" && `Invoice: ${log.details?.invoice_number?.split('-').slice(-2).join('-')} (Rs. ${log.details?.net_amount?.toLocaleString()})`}
                              {log.action === "sale_cancellation" && `Void: ${log.details?.invoice_number?.split('-').slice(-2).join('-')} | Reason: ${log.details?.reason}`}
                              {log.action === "held_sale_park" && `Ref: ${log.details?.hold_reference} (Rs. ${log.details?.net_amount})`}
                              {log.action === "held_sale_recall" && `Invoice: ${log.details?.invoice_number?.split('-').slice(-2).join('-')}`}
                              {log.action === "shift_open" && `Opening: Rs. ${log.details?.opening_balance}`}
                              {log.action === "shift_close" && `Expected: Rs. ${log.details?.expected_cash?.toLocaleString()} | Cashier Discrepancy: ${log.details?.variance >= 0 ? '+' : ''}Rs. ${log.details?.variance?.toLocaleString()}`}
                            </span>
                          </div>
                        </div>
                      </div>
                    );
                  })
                )}
              </div>

              {/* Pagination controls */}
              <div className="flex items-center justify-between border-t border-slate-100 dark:border-slate-800 pt-3 mt-auto shrink-0 text-[11px] font-sans">
                <Button 
                  onClick={() => setFeedPage(p => Math.max(1, p - 1))}
                  disabled={feedPage === 1 || isFeedLoading}
                  variant="ghost"
                  className="py-1 px-2.5 min-h-[auto] font-bold text-slate-500 hover:text-slate-700 disabled:opacity-50"
                >
                  Previous
                </Button>
                <span className="font-semibold text-slate-500 dark:text-slate-400">
                  Page {feedPage} of {feedTotalPages}
                </span>
                <Button 
                  onClick={() => setFeedPage(p => Math.min(feedTotalPages, p + 1))}
                  disabled={feedPage === feedTotalPages || isFeedLoading}
                  variant="ghost"
                  className="py-1 px-2.5 min-h-[auto] font-bold text-slate-500 hover:text-slate-700 disabled:opacity-50"
                >
                  Next
                </Button>
              </div>
            </Card>
          </div>

        </div>
      )}

      {activeTab === 'feedback' && (
        <div className="flex flex-col gap-6 animate-fade-in text-left">
          {isCsatLoading && !csatData ? (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <Skeleton className="h-28 w-full" />
              <Skeleton className="h-28 w-full" />
              <Skeleton className="h-28 w-full" />
            </div>
          ) : (
            <>
              {/* Score Grid Cards */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <Card className="p-5 flex items-center justify-between border-brand-500/10">
                  <div className="flex flex-col gap-1.5 text-left">
                    <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider">Average CSAT Score</span>
                    <span className="text-2xl font-black text-slate-800 dark:text-white">
                      {csatData?.summary?.average_rating || '0.00'} / 5.00
                    </span>
                    <div className="flex items-center gap-1 text-sm mt-0.5 animate-pulse">
                      {[1, 2, 3, 4, 5].map((star) => (
                        <span 
                          key={star} 
                          className={`text-sm ${star <= Math.round(csatData?.summary?.average_rating || 0) ? 'opacity-100' : 'opacity-20'}`}
                        >
                          ⭐
                        </span>
                      ))}
                    </div>
                  </div>
                  <div className="p-3 bg-brand-500/10 rounded-2xl">
                    <TrendingUp className="w-6 h-6 text-brand-500" />
                  </div>
                </Card>

                <Card className="p-5 flex items-center justify-between border-emerald-500/10">
                  <div className="flex flex-col gap-1 text-left">
                    <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider">Total Feedbacks</span>
                    <span className="text-2xl font-black text-slate-800 dark:text-white mt-1">
                      {csatData?.summary?.total_count || 0} reviews
                    </span>
                    <span className="text-[10.5px] text-slate-450 leading-relaxed font-semibold">Logged via digital receipts</span>
                  </div>
                  <div className="p-3 bg-emerald-500/10 rounded-2xl">
                    <Users className="w-6 h-6 text-emerald-500" />
                  </div>
                </Card>

                <Card className="p-5 flex items-center justify-between border-indigo-500/10">
                  <div className="flex flex-col gap-1 text-left">
                    <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider">Positive Satisfaction</span>
                    <span className="text-2xl font-black text-slate-800 dark:text-white mt-1">
                      {(() => {
                        const total = csatData?.summary?.total_count || 0;
                        if (total === 0) return '0.0%';
                        const counts = csatData?.summary?.counts || {};
                        const positive = (counts[4] || 0) + (counts[5] || 0);
                        return `${((positive / total) * 100).toFixed(1)}%`;
                      })()}
                    </span>
                    <span className="text-[10.5px] text-slate-450 leading-relaxed font-semibold">Tapped Good 🙂 or Excellent 😊</span>
                  </div>
                  <div className="p-3 bg-indigo-500/10 rounded-2xl">
                    <Percent className="w-6 h-6 text-indigo-500" />
                  </div>
                </Card>
              </div>

              <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
                {/* RATING DISTRIBUTION CHART */}
                <Card className="lg:col-span-4 p-6 flex flex-col gap-4">
                  <h3 className="font-bold text-sm text-slate-800 dark:text-white border-b pb-2 border-slate-100 dark:border-slate-850">Rating Distribution</h3>
                  
                  <div className="flex flex-col gap-3">
                    {[5, 4, 3, 2, 1].map((stars) => {
                      const counts = csatData?.summary?.counts || {};
                      const countVal = counts[stars] || 0;
                      const total = csatData?.summary?.total_count || 1;
                      const percentVal = (countVal / total) * 100;
                      const smileys = ['😠', '🙁', '😐', '🙂', '😊'];
                      
                      return (
                        <div key={stars} className="flex items-center gap-2 text-xs">
                          <span className="w-12 text-left font-semibold text-slate-550 flex items-center gap-1 shrink-0">
                            {stars} {smileys[stars - 1]}
                          </span>
                          <div className="flex-grow h-2 bg-slate-100 dark:bg-slate-800 rounded-full overflow-hidden shrink-0">
                            <div 
                              className={`h-full rounded-full transition-all duration-500 ${
                                stars >= 4 ? 'bg-emerald-500' : stars === 3 ? 'bg-amber-500' : 'bg-red-500'
                              }`} 
                              style={{ width: `${percentVal}%` }}
                            />
                          </div>
                          <span className="w-8 text-right font-mono font-bold text-slate-500 shrink-0">{countVal}</span>
                        </div>
                      );
                    })}
                  </div>
                </Card>

                {/* CSAT REVIEWS TIMELINE TABLE */}
                <Card className="lg:col-span-8 p-6 flex flex-col gap-4">
                  <div className="flex items-center justify-between border-b pb-2 border-slate-100 dark:border-slate-850">
                    <h3 className="font-bold text-sm text-slate-800 dark:text-white">Customer Feedback Ledger</h3>
                    <span className="text-[10px] font-bold text-slate-400 font-sans uppercase">Audit feed</span>
                  </div>

                  {isCsatLoading ? (
                    <div className="flex flex-col gap-3 py-4">
                      <Skeleton className="h-10 w-full" />
                      <Skeleton className="h-10 w-full" />
                      <Skeleton className="h-10 w-full" />
                    </div>
                  ) : !csatData?.feedbacks?.length ? (
                    <div className="text-center py-12 text-slate-400 text-xs font-sans">
                      No customer reviews or satisfaction ratings received yet.
                    </div>
                  ) : (
                    <>
                      <Table
                        headers={["Date & Time", "Invoice ID", "Branch Location", "Customer Rating", "Feedback Note"]}
                        rows={csatData.feedbacks.map((f: any) => {
                          const ratingColors: any = {
                            5: 'bg-emerald-500/10 text-emerald-500 border-emerald-500/20 font-bold',
                            4: 'bg-teal-500/10 text-teal-500 border-teal-500/20',
                            3: 'bg-amber-500/10 text-amber-500 border-amber-500/20',
                            2: 'bg-orange-500/10 text-orange-500 border-orange-500/20',
                            1: 'bg-red-500/10 text-red-500 border-red-500/20 font-bold'
                          };
                          const smileys = ['😠', '🙁', '😐', '🙂', '😊'];
                          return [
                            <span key={1} className="text-xs font-mono font-semibold text-slate-500">{new Date(f.created_at).toLocaleString()}</span>,
                            <span key={2} className="text-xs font-mono font-bold">{f.invoice_number}</span>,
                            <span key={3} className="text-xs font-semibold text-slate-650 dark:text-slate-350">{f.branch_name}</span>,
                            <span key={4} className={`px-2.5 py-0.5 rounded-full text-[10px] border flex items-center gap-1.5 w-fit ${ratingColors[f.rating] || 'bg-slate-500/10 text-slate-505'}`}>
                              <span>{smileys[f.rating - 1]}</span>
                              <span className="font-extrabold">{f.rating} Stars</span>
                            </span>,
                            <p key={5} className="text-xs text-slate-700 dark:text-slate-300 italic font-medium max-w-xs truncate text-left" title={f.feedback_text}>
                              {f.feedback_text || <span className="text-slate-400 not-italic">No comment left</span>}
                            </p>
                          ];
                        })}
                      />

                      {/* CSAT Pagination controls */}
                      <div className="flex items-center justify-between border-t border-slate-105 dark:border-slate-805 pt-4 mt-4 shrink-0 text-xs font-sans">
                        <Button 
                          onClick={() => setCsatPage(p => Math.max(1, p - 1))}
                          disabled={csatPage === 1 || isCsatLoading}
                          variant="secondary"
                          className="py-1.5 px-3 font-semibold"
                        >
                          Previous
                        </Button>
                        <span className="font-medium text-slate-500 dark:text-slate-400">
                          Page {csatPage} of {csatTotalPages}
                        </span>
                        <Button 
                          onClick={() => setCsatPage(p => Math.min(csatTotalPages, p + 1))}
                          disabled={csatPage === csatTotalPages || isCsatLoading}
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
            </>
          )}
        </div>
      )}

    </div>
  );
}
