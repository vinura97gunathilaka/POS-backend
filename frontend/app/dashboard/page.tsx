'use client';

import React from 'react';
import { 
  DollarSign, ShoppingBag, Users, Layers, 
  ArrowUpRight, AlertTriangle, TrendingUp, Award
} from 'lucide-react';
import { Card } from '@/components/UI';
import { apiClient } from '@/services/api';
import { 
  AreaChart, Area, XAxis, YAxis, 
  CartesianGrid, Tooltip, ResponsiveContainer 
} from 'recharts';

export default function DashboardHome() {
  const [stats, setStats] = React.useState({
    revenue: 0,
    orders: 0,
    customers: 0,
    branches: 0
  });

  const [lowStock, setLowStock] = React.useState<any[]>([]);

  const [salesTrend, setSalesTrend] = React.useState<any[]>([
    { name: '08:00', sales: 0 },
    { name: '10:00', sales: 0 },
    { name: '12:00', sales: 0 },
    { name: '14:00', sales: 0 },
    { name: '16:00', sales: 0 },
    { name: '18:00', sales: 0 },
    { name: '20:00', sales: 0 }
  ]);

  React.useEffect(() => {
    // Dynamic fetch of statistics
    apiClient.get('/sales')
      .then((res) => {
        if (res.data.success && res.data.data) {
          const sales = res.data.data;
          const completedSales = sales.filter((s: any) => s.sale_status === 'completed');
          const totalRev = completedSales.reduce((acc: number, cur: any) => acc + parseFloat(cur.net_amount || 0), 0);
          
          setStats(prev => ({
            ...prev,
            revenue: totalRev,
            orders: completedSales.length
          }));

          // Compute sales trend dynamically by hour
          const hourBuckets = [
            { name: '08:00', sales: 0 },
            { name: '10:00', sales: 0 },
            { name: '12:00', sales: 0 },
            { name: '14:00', sales: 0 },
            { name: '16:00', sales: 0 },
            { name: '18:00', sales: 0 },
            { name: '20:00', sales: 0 }
          ];

          completedSales.forEach((s: any) => {
            if (s.sale_date) {
              const date = new Date(s.sale_date);
              const hour = date.getHours();
              const amount = parseFloat(s.net_amount || 0);

              if (hour < 9) hourBuckets[0].sales += amount;
              else if (hour < 11) hourBuckets[1].sales += amount;
              else if (hour < 13) hourBuckets[2].sales += amount;
              else if (hour < 15) hourBuckets[3].sales += amount;
              else if (hour < 17) hourBuckets[4].sales += amount;
              else if (hour < 19) hourBuckets[5].sales += amount;
              else hourBuckets[6].sales += amount;
            }
          });
          setSalesTrend(hourBuckets);
        }
      })
      .catch(() => {});

    apiClient.get('/crm/customers')
      .then((res) => {
        if (res.data.success && res.data.data) {
          setStats(prev => ({
            ...prev,
            customers: res.data.data.length
          }));
        }
      })
      .catch(() => {});

    apiClient.get('/branches')
      .then((res) => {
        if (res.data.success && res.data.data) {
          setStats(prev => ({
            ...prev,
            branches: res.data.data.length
          }));
        }
      })
      .catch(() => {});

    apiClient.get('/catalog/products')
      .then((res) => {
        if (res.data.success && res.data.data) {
          // Identify low stock
          const list: any[] = [];
          res.data.data.forEach((p: any) => {
            if (p.variants) {
              p.variants.forEach((v: any) => {
                if (v.inventories) {
                  v.inventories.forEach((i: any) => {
                    if (i.quantity <= p.reorder_level) {
                      list.push({
                        name: `${p.name} - ${v.name}`,
                        sku: v.sku || p.sku,
                        stock: i.quantity,
                        reorder: p.reorder_level
                      });
                    }
                  });
                }
              });
            }
          });
          setLowStock(list);
        }
      })
      .catch(() => {});
  }, []);

  const cards = [
    { name: 'Today Revenue', value: `Rs. ${stats.revenue.toLocaleString()}`, change: '+12%', desc: 'compared to yesterday', icon: <DollarSign className="w-5 h-5 text-brand-500" />, bg: 'bg-brand-500/10' },
    { name: 'Sales Transactions', value: stats.orders.toString(), change: '+8%', desc: 'successful checkouts', icon: <ShoppingBag className="w-5 h-5 text-emerald-500" />, bg: 'bg-emerald-500/10' },
    { name: 'CRM Customers', value: stats.customers.toString(), change: '+4%', desc: 'loyalty enrollments', icon: <Users className="w-5 h-5 text-violet-500" />, bg: 'bg-violet-500/10' },
    { name: 'Active Branches', value: stats.branches.toString(), change: 'Stable', desc: 'live terminal syncing', icon: <Layers className="w-5 h-5 text-amber-500" />, bg: 'bg-amber-500/10' }
  ];

  return (
    <div className="flex flex-col gap-6 text-left">
      
      {/* Welcome Banner */}
      <div className="flex flex-col gap-1">
        <h2 className="text-2xl font-bold dark:text-white">Store Analytics Overview</h2>
        <p className="text-xs text-slate-400">Real-time metrics monitoring company-wide sales performance.</p>
      </div>

      {/* KPI Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        {cards.map((card, idx) => (
          <Card key={idx} className="flex items-center justify-between p-6">
            <div className="flex flex-col gap-1">
              <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">{card.name}</span>
              <span className="text-2xl font-extrabold text-slate-800 dark:text-white mt-1">{card.value}</span>
              <span className="text-[10px] text-slate-400 flex items-center gap-1 mt-2">
                <span className="text-emerald-500 font-bold">{card.change}</span>
                {card.desc}
              </span>
            </div>
            <div className={`p-3.5 rounded-2xl ${card.bg}`}>
              {card.icon}
            </div>
          </Card>
        ))}
      </div>

      {/* Graphic Sales Chart and Action Alerts Panel */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        
        {/* Sales Trend Chart */}
        <Card className="lg:col-span-8 p-6 flex flex-col gap-4">
          <div className="flex items-center justify-between">
            <div className="flex flex-col gap-0.5">
              <h3 className="font-bold text-base text-slate-800 dark:text-white">Intraday Sales Flow</h3>
              <p className="text-[11px] text-slate-400">Total gross receipts tracked every 2 hours.</p>
            </div>
            <div className="flex items-center gap-1.5 text-xs text-brand-600 dark:text-brand-400 font-bold bg-brand-500/10 px-2.5 py-1.5 rounded-xl">
              <TrendingUp className="w-4 h-4" />
              Live Feed
            </div>
          </div>
          
          <div className="w-full h-80 mt-4">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={salesTrend}>
                <defs>
                  <linearGradient id="colorSales" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.25}/>
                    <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="rgba(255,255,255,0.05)" />
                <XAxis dataKey="name" stroke="#94a3b8" fontSize={11} tickLine={false} axisLine={false} />
                <YAxis stroke="#94a3b8" fontSize={11} tickLine={false} axisLine={false} />
                <Tooltip 
                  contentStyle={{ background: '#0f172a', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '12px' }}
                  labelStyle={{ color: '#fff', fontWeight: 'bold' }}
                />
                <Area type="monotone" dataKey="sales" stroke="#8b5cf6" strokeWidth={3} fillOpacity={1} fill="url(#colorSales)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </Card>

        {/* Action Panel: Low Stock Alert Ledger */}
        <Card className="lg:col-span-4 p-6 flex flex-col gap-4">
          <div className="flex items-center gap-2 text-amber-500">
            <AlertTriangle className="w-5 h-5 animate-pulse" />
            <h3 className="font-bold text-base text-slate-800 dark:text-white">Critical Low Stock</h3>
          </div>
          <p className="text-[11px] text-slate-400 leading-normal">
            The following variants are currently at or below safety reorder stock levels. Initiate purchase orders immediately.
          </p>

          <div className="flex flex-col gap-3 mt-2 overflow-y-auto max-h-72 pr-1">
            {lowStock.map((item, idx) => (
              <div key={idx} className="p-3 rounded-xl border border-slate-100 dark:border-slate-800/60 bg-slate-50/50 dark:bg-slate-900/40 flex items-center justify-between text-xs gap-3">
                <div className="flex flex-col gap-0.5 min-w-0">
                  <span className="font-bold text-slate-700 dark:text-slate-200 truncate">{item.name}</span>
                  <span className="text-[10px] text-slate-400">SKU: {item.sku}</span>
                </div>
                <div className="flex flex-col items-end shrink-0">
                  <span className="font-bold text-red-500">Qty: {item.stock}</span>
                  <span className="text-[9px] text-slate-400">Reorder limit: {item.reorder}</span>
                </div>
              </div>
            ))}
          </div>

        </Card>
      </div>

    </div>
  );
}
