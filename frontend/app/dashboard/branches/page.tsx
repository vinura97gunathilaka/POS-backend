'use client';

import React from 'react';
import { 
  Store, MapPin, Plus, Edit, Trash2, ShieldAlert, 
  DollarSign, ShoppingBag, TrendingUp, RefreshCw
} from 'lucide-react';
import { usePOSStore } from '@/store/usePOSStore';
import { apiClient } from '@/services/api';
import { Button, Card, Input, Modal, Table, Toast, Select, Skeleton } from '@/components/UI';
import { hasPermission } from '@/utils/permissions';

export default function BranchesPage() {
  const { currentUser, activeCompany } = usePOSStore();
  
  const [activeTab, setActiveTab] = React.useState<'branches' | 'settings'>('branches');
  const [enableKDS, setEnableKDS] = React.useState(false);
  const [autoEmail, setAutoEmail] = React.useState(false);
  const [autoWhatsApp, setAutoWhatsApp] = React.useState(false);
  const [enableRecipe, setEnableRecipe] = React.useState(false);
  const [receiptLogoUrl, setReceiptLogoUrl] = React.useState('');
  const [receiptHeader, setReceiptHeader] = React.useState('');
  const [receiptFooter, setReceiptFooter] = React.useState('');
  const [kdsSlaLimit, setKdsSlaLimit] = React.useState(10);

  // Data lists
  const [branches, setBranches] = React.useState<any[]>([]);
  const [sales, setSales] = React.useState<any[]>([]);
  const [branchStats, setBranchStats] = React.useState<Record<number, { revenue: number; transactions: number }>>({});
  const [dispatchLogs, setDispatchLogs] = React.useState<any[]>([]);
  const [dispatchPage, setDispatchPage] = React.useState(1);
  const [dispatchTotalPages, setDispatchTotalPages] = React.useState(1);
  const [isDispatchLoading, setIsDispatchLoading] = React.useState(false);
  
  // Modals state
  const [isAddBranchOpen, setIsAddBranchOpen] = React.useState(false);
  const [isEditBranchOpen, setIsEditBranchOpen] = React.useState(false);
  const [selectedBranch, setSelectedBranch] = React.useState<any | null>(null);

  // Form: Branch fields
  const [branchName, setBranchName] = React.useState('');
  const [branchAddress, setBranchAddress] = React.useState('');
  const [branchPhone, setBranchPhone] = React.useState('');
  const [branchEmail, setBranchEmail] = React.useState('');
  const [branchStatus, setBranchStatus] = React.useState('active');

  const [toastMsg, setToastMsg] = React.useState('');
  const [toastType, setToastType] = React.useState<'success' | 'error'>('success');
  const [isLoading, setIsLoading] = React.useState(false);

  React.useEffect(() => {
    if (activeCompany?.settings) {
      setEnableKDS(activeCompany.settings.enable_kds || false);
      setAutoEmail(activeCompany.settings.auto_email_receipts || false);
      setAutoWhatsApp(activeCompany.settings.auto_whatsapp_receipts || false);
      setEnableRecipe(activeCompany.settings.enable_recipe || false);
      setReceiptLogoUrl(activeCompany.settings.receipt_logo_url || '');
      setReceiptHeader(activeCompany.settings.receipt_header || '');
      setReceiptFooter(activeCompany.settings.receipt_footer || '');
      setKdsSlaLimit(activeCompany.settings.kds_sla_limit || 10);
    }
  }, [activeCompany]);

  const handleUpdateCompanySettings = async (updates: Record<string, any>) => {
    setIsLoading(true);
    try {
      const updatedSettings = {
        ...(activeCompany?.settings || {}),
        ...updates
      };
      
      const res = await apiClient.put(`/companies/${activeCompany.id}`, {
        settings: updatedSettings
      });
      
      if (res.data.success) {
        usePOSStore.setState({ activeCompany: res.data.data });
        triggerToast('Company settings updated successfully.');
      }
    } catch (err) {
      triggerToast('Failed to update company settings.', 'error');
    } finally {
      setIsLoading(false);
    }
  };

  const fetchDispatchLogs = async (pageNum = 1) => {
    setIsDispatchLoading(true);
    try {
      const res = await apiClient.get('/logging/notification-dispatches', {
        params: { page: pageNum, limit: 10 }
      });
      if (res.data.success && res.data.data) {
        setDispatchLogs(res.data.data);
        const total = parseInt(res.headers['x-total-pages'] || '1');
        setDispatchTotalPages(total);
      }
    } catch (err) {
      console.error("Failed to load dispatch logs", err);
    } finally {
      setIsDispatchLoading(false);
    }
  };

  const handleSendReceipt = async (type: string, recipient: string, saleId: number) => {
    try {
      const res = await apiClient.post(`/sales/${saleId}/dispatch-receipt`, {
        type,
        recipient
      });
      if (res.data.success) {
        triggerToast(`Receipt resent successfully via ${type}!`);
        fetchDispatchLogs(dispatchPage);
      }
    } catch (e) {
      triggerToast('Failed to resend receipt.', 'error');
    }
  };

  React.useEffect(() => {
    if (activeTab === 'settings' && currentUser) {
      fetchDispatchLogs(dispatchPage);
    }
  }, [activeTab, currentUser, dispatchPage]);


  // Fetch all necessary data
  const fetchData = async () => {
    setIsLoading(true);
    try {
      // 1. Fetch branches
      const bRes = await apiClient.get('/branches/');
      let branchesList: any[] = [];
      if (bRes.data.success && bRes.data.data) {
        branchesList = bRes.data.data;
        setBranches(branchesList);
      }

      // 2. Fetch sales
      const sRes = await apiClient.get('/sales/');
      if (sRes.data.success && sRes.data.data) {
        const salesList = sRes.data.data;
        setSales(salesList);

        // Calculate branch wise stats
        const statsMap: Record<number, { revenue: number; transactions: number }> = {};
        
        // Pre-populate with all branches
        branchesList.forEach(b => {
          statsMap[b.id] = { revenue: 0, transactions: 0 };
        });

        // Sum up completed sales
        salesList.forEach((s: any) => {
          if (s.sale_status === 'completed' && s.branch_id) {
            if (!statsMap[s.branch_id]) {
              statsMap[s.branch_id] = { revenue: 0, transactions: 0 };
            }
            statsMap[s.branch_id].revenue += parseFloat(s.net_amount || 0);
            statsMap[s.branch_id].transactions += 1;
          }
        });
        
        setBranchStats(statsMap);
      }
    } catch (err) {
      console.error("Error loading branch data", err);
    } finally {
      setIsLoading(false);
    }
  };

  React.useEffect(() => {
    if (currentUser && hasPermission(currentUser, 'finance:manage')) {
      fetchData();
    }
  }, [currentUser]);

  const triggerToast = (msg: string, type: 'success' | 'error' = 'success') => {
    setToastMsg(msg);
    setToastType(type);
  };

  // Open modals & reset states
  const openAddBranch = () => {
    setBranchName('');
    setBranchAddress('');
    setBranchPhone('');
    setBranchEmail('');
    setIsAddBranchOpen(true);
  };

  const openEditBranch = (b: any) => {
    setSelectedBranch(b);
    setBranchName(b.name);
    setBranchAddress(b.address || '');
    setBranchPhone(b.phone || '');
    setBranchEmail(b.email || '');
    setBranchStatus(b.status || 'active');
    setIsEditBranchOpen(true);
  };

  // Actions
  const handleAddBranch = async () => {
    if (!branchName) {
      triggerToast('Branch Name is required.', 'error');
      return;
    }
    setIsLoading(true);
    try {
      const payload = {
        company_id: activeCompany.id,
        name: branchName,
        address: branchAddress || null,
        phone: branchPhone || null,
        email: branchEmail || null
      };
      
      const res = await apiClient.post('/branches/', payload);
      if (res.data.success) {
        triggerToast('Branch registered successfully.');
        setIsAddBranchOpen(false);
        fetchData();
      }
    } catch (err) {
      triggerToast('Failed to register branch.', 'error');
    } finally {
      setIsLoading(false);
    }
  };

  const handleEditBranch = async () => {
    if (!branchName) {
      triggerToast('Branch Name is required.', 'error');
      return;
    }
    setIsLoading(true);
    try {
      const payload = {
        name: branchName,
        address: branchAddress || null,
        phone: branchPhone || null,
        email: branchEmail || null,
        status: branchStatus
      };
      
      const res = await apiClient.put(`/branches/${selectedBranch.id}`, payload);
      if (res.data.success) {
        triggerToast('Branch updated successfully.');
        setIsEditBranchOpen(false);
        fetchData();
      }
    } catch (err) {
      triggerToast('Failed to update branch.', 'error');
    } finally {
      setIsLoading(false);
    }
  };

  const handleDeleteBranch = async (id: number) => {
    if (!confirm('Are you sure you want to deactivate/archive this branch?')) return;
    try {
      const res = await apiClient.delete(`/branches/${id}`);
      if (res.data.success) {
        triggerToast('Branch deactivated successfully.');
        fetchData();
      }
    } catch (err) {
      triggerToast('Failed to deactivate branch.', 'error');
    }
  };

  // Security Gate
  if (!currentUser || !hasPermission(currentUser, 'finance:manage')) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] text-center p-6 bg-white dark:bg-slate-900 rounded-3xl border border-slate-100 dark:border-slate-800 shadow-sm text-left">
        <ShieldAlert className="w-16 h-16 text-red-500 mb-4 animate-bounce" />
        <h3 className="text-xl font-bold text-slate-800 dark:text-white mb-2">Access Denied</h3>
        <p className="text-sm text-slate-500 dark:text-slate-400 max-w-md">
          You do not have the required permissions to access the Branches Management & Statistics console. Please contact your company administrator.
        </p>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-6 text-left">
      
      {/* Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex flex-col gap-1">
          <h2 className="text-2xl font-bold dark:text-white">Branches & Store Stats</h2>
          <p className="text-xs text-slate-400">Manage multiple business branches, track local store performance, and configure branch properties.</p>
        </div>
        
        {activeTab === 'branches' && (
          <div className="flex gap-2 shrink-0">
            <Button onClick={fetchData} variant="secondary" icon={<RefreshCw className="w-4 h-4" />}>
              Refresh
            </Button>
            <Button onClick={openAddBranch} icon={<Plus className="w-4 h-4" />}>
              Register New Branch
            </Button>
          </div>
        )}
      </div>

      {/* Tab Switching */}
      <div className="flex gap-4 border-b border-slate-200 dark:border-slate-800 text-sm font-semibold mb-2">
        <button
          onClick={() => setActiveTab('branches')}
          className={`pb-3 px-1 border-b-2 transition-colors ${activeTab === 'branches' ? 'border-brand-500 text-brand-600 dark:text-white' : 'border-transparent text-slate-500 hover:text-slate-700'}`}
        >
          Branches & Performance
        </button>
        <button
          onClick={() => setActiveTab('settings')}
          className={`pb-3 px-1 border-b-2 transition-colors ${activeTab === 'settings' ? 'border-brand-500 text-brand-600 dark:text-white' : 'border-transparent text-slate-500 hover:text-slate-700'}`}
        >
          System Configurations
        </button>
      </div>

      {activeTab === 'branches' ? (
        <>
          {/* BRANCH STATS CARDS */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {branches.map(b => {
              const stats = branchStats[b.id] || { revenue: 0, transactions: 0 };
              const avgTicket = stats.transactions > 0 ? stats.revenue / stats.transactions : 0;
              return (
                <Card key={b.id} className="p-6 flex flex-col gap-4 relative overflow-hidden border-brand-500/20">
                  <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-800 pb-3">
                    <div className="flex items-center gap-2">
                      <Store className="w-5 h-5 text-brand-500" />
                      <span className="font-bold text-base text-slate-800 dark:text-white truncate max-w-[150px]">{b.name}</span>
                    </div>
                    <span className={`px-2 py-0.5 rounded text-[9px] font-bold uppercase tracking-wider ${
                      b.status === 'active' ? 'bg-emerald-500/10 text-emerald-500' : 'bg-amber-500/10 text-amber-500'
                    }`}>
                      {b.status}
                    </span>
                  </div>

                  {/* Stats Grid */}
                  <div className="grid grid-cols-2 gap-4">
                    <div className="flex flex-col">
                      <span className="text-[10px] text-slate-400 font-bold uppercase flex items-center gap-1">
                        <DollarSign className="w-3 h-3 text-brand-500" /> Total Revenue
                      </span>
                      <span className="text-lg font-extrabold text-slate-800 dark:text-white mt-1">
                        Rs. {stats.revenue.toLocaleString()}
                      </span>
                    </div>
                    <div className="flex flex-col">
                      <span className="text-[10px] text-slate-400 font-bold uppercase flex items-center gap-1">
                        <ShoppingBag className="w-3 h-3 text-emerald-500" /> Tx Count
                      </span>
                      <span className="text-lg font-extrabold text-slate-800 dark:text-white mt-1">
                        {stats.transactions} sales
                      </span>
                    </div>
                  </div>

                  {/* Average Order Size */}
                  <div className="flex items-center justify-between bg-slate-50 dark:bg-slate-900/60 p-2.5 rounded-xl text-xs">
                    <span className="text-slate-400 font-semibold">Average Basket Ticket:</span>
                    <span className="font-bold text-slate-700 dark:text-slate-200">
                      Rs. {avgTicket.toLocaleString(undefined, { maximumFractionDigits: 2 })}
                    </span>
                  </div>

                  {/* Address details */}
                  <div className="flex items-start gap-1.5 text-[11px] text-slate-400 mt-1 min-h-[32px]">
                    <MapPin className="w-3.5 h-3.5 shrink-0 text-slate-400" />
                    <span className="line-clamp-2 leading-relaxed">{b.address || 'No address specified'}</span>
                  </div>
                </Card>
              );
            })}
          </div>

          {/* BRANCH MANAGEMENT MATRIX */}
          <Card className="p-6">
            <div className="flex items-center gap-2 mb-4">
              <Store className="w-5 h-5 text-brand-500" />
              <h3 className="font-bold text-base text-slate-800 dark:text-white">Branches Directory Matrix</h3>
            </div>
            <Table
              headers={["Branch Name", "Contact Phone", "Contact Email", "Address", "Status", "Actions"]}
              rows={branches.map((b) => {
                const statusColors: any = {
                  active: 'bg-emerald-500/10 text-emerald-500',
                  inactive: 'bg-amber-500/10 text-amber-500',
                  archived: 'bg-red-500/10 text-red-500'
                };
                return [
                  <span key={1} className="font-bold text-slate-800 dark:text-white">{b.name}</span>,
                  <span key={2} className="text-xs">{b.phone || 'N/A'}</span>,
                  <span key={3} className="text-xs">{b.email || 'N/A'}</span>,
                  <span key={4} className="text-xs text-slate-400 max-w-xs block truncate">{b.address || 'N/A'}</span>,
                  <span key={5} className={`px-2 py-1.5 rounded-lg text-[10px] font-bold uppercase tracking-wider ${statusColors[b.status] || 'bg-slate-500/10 text-slate-500'}`}>
                    {b.status}
                  </span>,
                  <div key={6} className="flex gap-2">
                    <Button onClick={() => openEditBranch(b)} variant="ghost" className="min-h-0 py-1.5 px-2.5 text-xs text-brand-500" icon={<Edit className="w-3.5 h-3.5" />}>
                      Edit
                    </Button>
                    {branches.length > 1 && (
                      <Button onClick={() => handleDeleteBranch(b.id)} variant="ghost" className="min-h-0 py-1.5 px-2.5 text-xs text-red-500" icon={<Trash2 className="w-3.5 h-3.5" />}>
                        Archive
                      </Button>
                    )}
                  </div>
                ];
              })}
            />
          </Card>
        </>
      ) : (
        <div className="flex flex-col gap-6 animate-fade-in text-left">
          <Card className="max-w-4xl p-6 flex flex-col gap-4">
            <div className="flex items-center gap-2 mb-2">
              <Store className="w-5 h-5 text-brand-500" />
              <h3 className="font-bold text-base text-slate-800 dark:text-white font-sans">SaaS Global System Settings</h3>
            </div>
            
            <div className="flex flex-col gap-4 border-t border-slate-100 dark:border-slate-800 pt-5">
              <div className="flex items-start justify-between p-4.5 rounded-2xl border border-slate-100 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-900/40 gap-4">
                <div className="flex flex-col gap-1 text-left max-w-xl">
                  <span className="font-bold text-slate-850 dark:text-white text-sm">Order Prep Monitor (KDS Queue)</span>
                  <span className="text-[11px] text-slate-450 leading-relaxed font-medium">
                    Route checkouts to a real-time order preparation queue for kitchens, bars, or assembly desks. Enabling this KDS module displays the Order Prep Queue tab in the sidebar and sets new sales invoices to 'pending' prep status until processed.
                  </span>
                  {enableKDS && (
                    <div className="text-[11px] font-semibold text-brand-600 dark:text-brand-400 mt-2 flex items-center gap-1.5 bg-brand-500/5 dark:bg-brand-500/10 px-3 py-1.5 rounded-xl border border-brand-500/15 w-fit">
                      <span className="font-bold uppercase tracking-wider text-[9px] bg-brand-500 text-white px-1.5 py-0.5 rounded mr-1">Public TV URL:</span>
                      <a 
                        href={`/order-status?company_id=${activeCompany?.id || 2}`} 
                        target="_blank" 
                        rel="noopener noreferrer"
                        className="underline hover:text-brand-700 font-mono"
                      >
                        {typeof window !== 'undefined' 
                          ? `${window.location.origin}/order-status?company_id=${activeCompany?.id || 2}` 
                          : `/order-status?company_id=${activeCompany?.id || 2}`}
                      </a>
                    </div>
                  )}
                </div>
                <div className="flex items-center pt-1 shrink-0">
                  <input
                    type="checkbox"
                    id="enable-kds-checkbox"
                    checked={enableKDS}
                    onChange={async (e) => {
                      const val = e.target.checked;
                      await handleUpdateCompanySettings({ enable_kds: val });
                      setEnableKDS(val);
                    }}
                    className="w-5 h-5 rounded border-slate-350 text-brand-650 focus:ring-brand-500 cursor-pointer accent-brand-500"
                  />
                </div>
              </div>

              {/* Enable Recipe BOM Toggle */}
              <div className="flex items-start justify-between p-4.5 rounded-2xl border border-slate-100 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-900/40 gap-4">
                <div className="flex flex-col gap-1 text-left max-w-xl">
                  <span className="font-bold text-slate-850 dark:text-white text-sm">Recipe-based Inventory (Bill of Materials)</span>
                  <span className="text-[11px] text-slate-450 leading-relaxed font-medium">
                    Enable recipe definitions and ingredient depletions. When enabled, products configured with recipe components will deduct raw ingredients from inventory during sales.
                  </span>
                </div>
                <div className="flex items-center pt-1 shrink-0">
                  <input
                    type="checkbox"
                    id="enable-recipe-checkbox"
                    checked={enableRecipe}
                    onChange={async (e) => {
                      const val = e.target.checked;
                      await handleUpdateCompanySettings({ enable_recipe: val });
                      setEnableRecipe(val);
                    }}
                    className="w-5 h-5 rounded border-slate-350 text-brand-650 focus:ring-brand-500 cursor-pointer accent-brand-500"
                  />
                </div>
              </div>

              {/* Auto Email Toggle */}
              <div className="flex items-start justify-between p-4.5 rounded-2xl border border-slate-100 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-900/40 gap-4">
                <div className="flex flex-col gap-1 text-left max-w-xl">
                  <span className="font-bold text-slate-850 dark:text-white text-sm">Automated Email Receipts</span>
                  <span className="text-[11px] text-slate-450 leading-relaxed font-medium">
                    Automatically trigger mock invoice email dispatches when checking out transactions for registered customer accounts containing valid email addresses.
                  </span>
                </div>
                <div className="flex items-center pt-1 shrink-0">
                  <input
                    type="checkbox"
                    id="auto-email-checkbox"
                    checked={autoEmail}
                    onChange={async (e) => {
                      const val = e.target.checked;
                      await handleUpdateCompanySettings({ auto_email_receipts: val });
                      setAutoEmail(val);
                    }}
                    className="w-5 h-5 rounded border-slate-350 text-brand-650 focus:ring-brand-500 cursor-pointer accent-brand-500"
                  />
                </div>
              </div>

              {/* Auto WhatsApp Toggle */}
              <div className="flex items-start justify-between p-4.5 rounded-2xl border border-slate-100 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-900/40 gap-4">
                <div className="flex flex-col gap-1 text-left max-w-xl">
                  <span className="font-bold text-slate-850 dark:text-white text-sm">Automated WhatsApp Receipts</span>
                  <span className="text-[11px] text-slate-450 leading-relaxed font-medium">
                    Automatically trigger mock WhatsApp invoice message dispatches when checking out transactions for registered customer accounts containing mobile numbers.
                  </span>
                </div>
                <div className="flex items-center pt-1 shrink-0">
                  <input
                    type="checkbox"
                    id="auto-whatsapp-checkbox"
                    checked={autoWhatsApp}
                    onChange={async (e) => {
                      const val = e.target.checked;
                      await handleUpdateCompanySettings({ auto_whatsapp_receipts: val });
                      setAutoWhatsApp(val);
                    }}
                    className="w-5 h-5 rounded border-slate-350 text-brand-650 focus:ring-brand-500 cursor-pointer accent-brand-500"
                  />
                </div>
              </div>
            </div>
          </Card>

          <Card className="max-w-4xl p-6 flex flex-col gap-4">
            <div className="flex items-center gap-2 mb-2">
              <Store className="w-5 h-5 text-brand-500" />
              <h3 className="font-bold text-base text-slate-800 dark:text-white font-sans">🎨 Receipt Branding & KDS SLA Configuration</h3>
            </div>
            <div className="flex flex-col gap-4 border-t border-slate-100 dark:border-slate-800 pt-5">
              <Input 
                label="Receipt Custom Logo URL" 
                value={receiptLogoUrl} 
                onChange={(e) => setReceiptLogoUrl(e.target.value)} 
                placeholder="e.g. https://yourdomain.com/logo.png" 
              />
              <Input 
                label="Receipt Header Welcome Message" 
                value={receiptHeader} 
                onChange={(e) => setReceiptHeader(e.target.value)} 
                placeholder="e.g. Thanks for dining with us! Come back soon." 
              />
              <Input 
                label="Receipt Footer Promo Message" 
                value={receiptFooter} 
                onChange={(e) => setReceiptFooter(e.target.value)} 
                placeholder="e.g. Show this receipt on your next visit for 10% off!" 
              />
              <Input 
                label="KDS SLA Delayed Warning Limit (Minutes)" 
                type="number" 
                value={kdsSlaLimit} 
                onChange={(e) => setKdsSlaLimit(parseInt(e.target.value) || 10)} 
              />
              <Button 
                onClick={async () => {
                  await handleUpdateCompanySettings({
                    receipt_logo_url: receiptLogoUrl,
                    receipt_header: receiptHeader,
                    receipt_footer: receiptFooter,
                    kds_sla_limit: kdsSlaLimit
                  });
                }} 
                isLoading={isLoading}
                className="w-full sm:w-fit mt-2 font-bold"
              >
                Save Receipt & SLA Settings
              </Button>
            </div>
          </Card>

          {/* Logs table card */}
          <Card className="p-6 flex flex-col gap-4">
            <div className="flex items-center justify-between border-b pb-3 border-slate-100 dark:border-slate-800">
              <div className="flex items-center gap-2">
                <RefreshCw className="w-5 h-5 text-brand-500" />
                <h3 className="font-bold text-base text-slate-800 dark:text-white font-sans">Digital Receipt Dispatch Logs</h3>
              </div>
              <Button onClick={() => fetchDispatchLogs(dispatchPage)} variant="ghost" className="p-2 shrink-0 min-h-0 py-1 px-2.5 text-xs" isLoading={isDispatchLoading}>
                Refresh logs
              </Button>
            </div>

            {isDispatchLoading ? (
              <div className="flex flex-col gap-3 py-6">
                <Skeleton className="h-10 w-full" />
                <Skeleton className="h-10 w-full" />
                <Skeleton className="h-10 w-full" />
              </div>
            ) : dispatchLogs.length === 0 ? (
              <span className="text-sm text-slate-400 text-center py-10 font-sans">No dispatch log records found.</span>
            ) : (
              <>
                <Table
                  headers={["Dispatch Date", "Sale ID", "Channel", "Recipient Address", "Status", "Actions"]}
                  rows={dispatchLogs.map((log) => {
                    const statusColors: any = {
                      sent: 'bg-emerald-500/10 text-emerald-500 border-emerald-500/20',
                      failed: 'bg-red-500/10 text-red-500 border-red-500/20'
                    };
                    return [
                      <span key={1} className="text-xs font-mono font-semibold text-slate-500">{new Date(log.created_at).toLocaleString()}</span>,
                      <span key={2} className="text-xs font-bold font-mono">Sale #{log.sale_id}</span>,
                      <span key={3} className="text-xs uppercase font-bold text-indigo-500 bg-indigo-500/10 px-2 py-0.5 rounded-full border border-indigo-500/20 tracking-wider">{log.type}</span>,
                      <span key={4} className="text-xs font-mono text-slate-600 dark:text-slate-300 font-semibold">{log.recipient}</span>,
                      <span key={5} className={`px-2 py-0.5 border rounded-full text-[9px] font-black uppercase tracking-wider ${statusColors[log.dispatch_status] || 'bg-slate-500/10 text-slate-500'}`}>
                        {log.dispatch_status}
                      </span>,
                      <div key={6}>
                        <Button
                          onClick={() => handleSendReceipt(log.type, log.recipient, log.sale_id)}
                          variant="primary"
                          className="min-h-[auto] py-1.5 px-3 text-[10px] font-bold"
                          isLoading={isDispatchLoading}
                        >
                          Resend Copy
                        </Button>
                      </div>
                    ];
                  })}
                />

                <div className="flex items-center justify-between border-t border-slate-100 dark:border-slate-800 pt-4 mt-4 text-xs font-sans">
                  <Button 
                    onClick={() => setDispatchPage(p => Math.max(1, p - 1))}
                    disabled={dispatchPage === 1 || isDispatchLoading}
                    variant="secondary"
                    className="py-1.5 px-3 font-semibold"
                  >
                    Previous
                  </Button>
                  <span className="font-medium text-slate-500 dark:text-slate-400">
                    Page {dispatchPage} of {dispatchTotalPages}
                  </span>
                  <Button 
                    onClick={() => setDispatchPage(p => Math.min(dispatchTotalPages, p + 1))}
                    disabled={dispatchPage === dispatchTotalPages || isDispatchLoading}
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
      )}

      {/* MODAL: ADD BRANCH */}
      <Modal isOpen={isAddBranchOpen} onClose={() => setIsAddBranchOpen(false)} title="Register Store Branch">
        <div className="flex flex-col gap-4 text-left">
          <Input label="Branch Name" value={branchName} onChange={(e) => setBranchName(e.target.value)} placeholder="e.g. Kandy Outlet" />
          <Input label="Physical Address" value={branchAddress} onChange={(e) => setBranchAddress(e.target.value)} placeholder="Full street address" />
          <div className="grid grid-cols-2 gap-4">
            <Input label="Contact Phone" value={branchPhone} onChange={(e) => setBranchPhone(e.target.value)} placeholder="e.g. +94812234567" />
            <Input label="Contact Email" type="email" value={branchEmail} onChange={(e) => setBranchEmail(e.target.value)} placeholder="kandy@smartpos.com" />
          </div>

          <div className="flex justify-end gap-3 mt-4 border-t border-slate-100 dark:border-slate-800 pt-4">
            <Button onClick={() => setIsAddBranchOpen(false)} variant="secondary">Cancel</Button>
            <Button onClick={handleAddBranch} isLoading={isLoading}>Save Branch</Button>
          </div>
        </div>
      </Modal>

      {/* MODAL: EDIT BRANCH */}
      <Modal isOpen={isEditBranchOpen} onClose={() => setIsEditBranchOpen(false)} title="Update Branch Settings">
        <div className="flex flex-col gap-4 text-left">
          <Input label="Branch Name" value={branchName} onChange={(e) => setBranchName(e.target.value)} />
          <Input label="Physical Address" value={branchAddress} onChange={(e) => setBranchAddress(e.target.value)} />
          <div className="grid grid-cols-2 gap-4">
            <Input label="Contact Phone" value={branchPhone} onChange={(e) => setBranchPhone(e.target.value)} />
            <Input label="Contact Email" type="email" value={branchEmail} onChange={(e) => setBranchEmail(e.target.value)} />
          </div>
          <Select 
            label="Operational Status"
            value={branchStatus}
            onChange={(e) => setBranchStatus(e.target.value)}
            options={[
              { label: "Active Operations", value: "active" },
              { label: "Inactive/Temporarily Closed", value: "inactive" }
            ]}
          />

          <div className="flex justify-end gap-3 mt-4 border-t border-slate-100 dark:border-slate-800 pt-4">
            <Button onClick={() => setIsEditBranchOpen(false)} variant="secondary">Cancel</Button>
            <Button onClick={handleEditBranch} isLoading={isLoading}>Update Settings</Button>
          </div>
        </div>
      </Modal>

      {toastMsg && (
        <Toast
          message={toastMsg}
          onClose={() => setToastMsg('')}
          type={toastType}
        />
      )}

    </div>
  );
}
