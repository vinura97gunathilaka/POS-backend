'use client';

import React from 'react';
import { useRouter, usePathname } from 'next/navigation';
import Link from 'next/link';
import { 
  Store, LayoutDashboard, ShoppingCart, Package, 
  Users, CreditCard, LogOut, Sun, Moon, AlertCircle, 
  Terminal, ShieldCheck, HelpCircle, Loader2, BarChart2
} from 'lucide-react';
import { usePOSStore } from '@/store/usePOSStore';
import { apiClient } from '@/services/api';
import { Button, Toast, Modal, Input } from '@/components/UI';
import { hasPermission } from '@/utils/permissions';

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  
  const { 
    currentUser, activeCompany, activeBranch, shift, darkMode, 
    toggleDarkMode, setAuthContext, setShift, logout 
  } = usePOSStore();

  const [isShiftModalOpen, setIsShiftModalOpen] = React.useState(false);
  const [isCloseShiftModalOpen, setIsCloseShiftModalOpen] = React.useState(false);
  const [openingBalance, setOpeningBalance] = React.useState('5000');
  const [actualCash, setActualCash] = React.useState('5000');
  const [closingNotes, setClosingNotes] = React.useState('');
  const [isLoading, setIsLoading] = React.useState(false);
  const [toastMsg, setToastMsg] = React.useState('');

  React.useEffect(() => {
    // Restore session on reload
    if (!currentUser) {
      apiClient.get('/auth/me')
        .then((res) => {
          if (res.data.success && res.data.data) {
            const user = res.data.data;
            setAuthContext(
              user,
              user.company || { id: user.company_id, name: "Smart POS Corp" },
              user.branches?.[0] || null
            );
          } else {
            router.push('/auth/login');
          }
        })
        .catch(() => {
          router.push('/auth/login');
        });
    }
  }, [currentUser]);

  // Check active shift on load
  React.useEffect(() => {
    if (currentUser) {
      apiClient.get('/finance/shifts')
        .then((res) => {
          if (res.data.success && res.data.data) {
            const active = res.data.data.find((s: any) => s.status === 'open' && s.user_id === currentUser.id);
            if (active) {
              setShift(active);
            }
          }
        });
    }
  }, [currentUser]);

  const handleOpenShift = async () => {
    setIsLoading(true);
    try {
      const res = await apiClient.post('/finance/shifts', {
        company_id: activeCompany.id,
        branch_id: activeBranch.id,
        cash_drawer_id: 1, // Default cash drawer
        opening_balance: parseFloat(openingBalance),
        notes: "Shift opened from web terminal"
      });
      if (res.data.success) {
        setShift(res.data.data);
        setIsShiftModalOpen(false);
        setToastMsg('Shift opened successfully. POS terminal unlocked.');
      }
    } catch (err: any) {
      setToastMsg('Failed to open shift.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleCloseShift = async () => {
    if (!shift) return;
    setIsLoading(true);
    try {
      const res = await apiClient.put(`/finance/shifts/${shift.id}/close`, {
        actual_cash: parseFloat(actualCash),
        notes: closingNotes
      });
      if (res.data.success) {
        const closedShift = res.data.data;
        setShift(null);
        setIsCloseShiftModalOpen(false);
        setToastMsg(`Shift closed successfully. Expected: Rs. ${closedShift.expected_cash}, Actual: Rs. ${closedShift.actual_cash}, Variance: Rs. ${closedShift.variance}. Terminal Locked.`);
      }
    } catch (err: any) {
      setToastMsg('Failed to close shift.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleLogout = () => {
    logout();
    router.push('/auth/login');
  };

  const menuItems = [
    { name: 'Dashboard', icon: <LayoutDashboard className="w-5 h-5" />, path: '/dashboard' },
    { name: 'Analytics & Reports', icon: <BarChart2 className="w-5 h-5" />, path: '/dashboard/analytics', permission: 'finance:manage' },
    { name: 'POS Terminal', icon: <ShoppingCart className="w-5 h-5" />, path: '/dashboard/pos', permission: 'pos:checkout' },
    { name: 'Order Prep Queue', icon: <Terminal className="w-5 h-5" />, path: '/dashboard/kds', condition: (company: any) => company?.settings?.enable_kds === true },
    { name: 'Inventory & GRN', icon: <Package className="w-5 h-5" />, path: '/dashboard/inventory', permission: 'inventory:read' },
    { name: 'CRM & Loyalty', icon: <Users className="w-5 h-5" />, path: '/dashboard/crm', permission: 'crm:manage' },
    { name: 'Branches & Stats', icon: <Store className="w-5 h-5" />, path: '/dashboard/branches', permission: 'finance:manage' },
    { name: 'Users & Roles', icon: <ShieldCheck className="w-5 h-5" />, path: '/dashboard/users', permission: 'users:manage' },
    { name: 'Audit Trail', icon: <Terminal className="w-5 h-5" />, path: '/dashboard/audit', permission: 'audit:read' },
    { name: 'SOP & User Guide', icon: <HelpCircle className="w-5 h-5" />, path: '/dashboard/sop' },
  ];

  const filteredMenuItems = menuItems.filter(item => 
    (!item.permission || hasPermission(currentUser, item.permission)) &&
    (!item.condition || item.condition(activeCompany))
  );

  if (!currentUser) {
    return (
      <div className="min-h-screen flex items-center justify-center dark:bg-slate-950">
        <Loader2 className="w-8 h-8 animate-spin text-brand-500" />
      </div>
    );
  }

  return (
    <div className="min-h-screen flex bg-slate-50 dark:bg-slate-950 transition-colors duration-200">
      
      {/* SIDEBAR */}
      <aside className="w-64 border-r border-slate-100 dark:border-slate-900 bg-white dark:bg-slate-900/60 flex flex-col justify-between shrink-0">
        <div className="flex flex-col gap-8 py-6 px-4">
          
          {/* Logo Header */}
          <div className="flex items-center gap-3 px-2">
            <div className="bg-brand-500 text-white p-2 rounded-xl shadow-md">
              <Store className="w-5 h-5" />
            </div>
            <div className="text-left">
              <h2 className="font-extrabold text-sm dark:text-white leading-none">Smart POS</h2>
              <span className="text-[9px] text-slate-400 font-bold uppercase tracking-widest">XerexLabs</span>
            </div>
          </div>

          {/* Navigation Links */}
          <nav className="flex flex-col gap-1">
            {filteredMenuItems.map((item, idx) => {
              const active = pathname === item.path;
              return (
                <Link key={idx} href={item.path}>
                  <div className={`flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-colors ${
                    active 
                      ? 'bg-brand-500/10 text-brand-600 dark:text-brand-400 font-bold' 
                      : 'text-slate-600 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-800/40'
                  }`}>
                    {item.icon}
                    {item.name}
                  </div>
                </Link>
              );
            })}
          </nav>
        </div>

        {/* User Context Footer */}
        <div className="p-4 border-t border-slate-100 dark:border-slate-900 flex flex-col gap-3">
          <div className="flex items-center gap-3 px-2">
            <div className="w-9 h-9 rounded-full bg-brand-500/10 border border-brand-500/20 text-brand-500 flex items-center justify-center font-bold text-sm uppercase">
              {currentUser.name[0]}
            </div>
            <div className="text-left min-w-0">
              <p className="text-xs font-bold text-slate-700 dark:text-slate-200 truncate">{currentUser.name}</p>
              <p className="text-[10px] text-slate-400 truncate">{currentUser.email}</p>
            </div>
          </div>
          <div className="flex flex-col gap-2">
            <Link href="/dashboard/sop">
              <div className="flex items-center justify-center gap-2 px-3 py-2.5 rounded-xl text-xs font-semibold text-slate-650 dark:text-slate-350 bg-slate-50 dark:bg-slate-800/40 hover:bg-slate-100 dark:hover:bg-slate-800 border border-slate-100 dark:border-slate-800 transition-colors w-full cursor-pointer">
                <HelpCircle className="w-4 h-4 text-brand-500 animate-pulse" />
                SOP & User Guide
              </div>
            </Link>
            <Button onClick={handleLogout} variant="ghost" icon={<LogOut className="w-4 h-4" />} className="w-full text-xs">
              Sign Out
            </Button>
          </div>
        </div>
      </aside>

      {/* PRIMARY PANEL CONTAINER */}
      <div className="flex-grow flex flex-col overflow-hidden">
        
        {/* TOPBAR */}
        <header className="h-16 border-b border-slate-100 dark:border-slate-900 bg-white dark:bg-slate-900/60 px-6 flex items-center justify-between shrink-0">
          
          {/* Left Context Info */}
          <div className="flex items-center gap-4 text-xs">
            <span className="font-semibold text-slate-400 uppercase tracking-widest">{activeCompany?.name}</span>
            <div className="w-1 h-1 bg-slate-300 rounded-full" />
            <span className="text-slate-500 dark:text-slate-400 font-medium bg-slate-100 dark:bg-slate-800 px-2.5 py-1 rounded-lg">
              Branch: {activeBranch?.name || "Global"}
            </span>
          </div>

          {/* Right Controls */}
          <div className="flex items-center gap-4">
            
            {/* Shift Tracker Badging */}
            {shift ? (
              <div className="flex items-center gap-3">
                <div className="flex items-center gap-2 bg-emerald-50 dark:bg-emerald-950/20 border border-emerald-100 dark:border-emerald-900/30 text-emerald-600 dark:text-emerald-400 px-3 py-1.5 rounded-full text-xs font-bold shadow-sm">
                  <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                  Shift Active
                </div>
                <Button 
                  onClick={() => {
                    setActualCash(shift.opening_balance?.toString() || '0');
                    setClosingNotes('');
                    setIsCloseShiftModalOpen(true);
                  }} 
                  variant="ghost" 
                  className="min-h-0 py-1.5 px-3 text-xs font-bold rounded-lg text-red-600 dark:text-red-400 bg-red-500/5 hover:bg-red-500/10 hover:text-red-700 transition-colors"
                >
                  Close Shift
                </Button>
              </div>
            ) : (
              <div className="flex items-center gap-2">
                <span className="text-xs text-slate-400 flex items-center gap-1">
                  <AlertCircle className="w-3.5 h-3.5 text-amber-500" />
                  Terminal Locked
                </span>
                <Button onClick={() => setIsShiftModalOpen(true)} variant="secondary" className="min-h-0 py-1.5 px-3 text-xs font-bold rounded-lg">
                  Open Cash Shift
                </Button>
              </div>
            )}

            {/* Dark Mode Toggle */}
            <button 
              onClick={toggleDarkMode} 
              className="p-2 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 hover:bg-slate-50 dark:hover:bg-slate-800 text-slate-500 dark:text-slate-400"
            >
              {darkMode ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
            </button>
          </div>

        </header>

        {/* Dynamic Main Body Content */}
        <main className="flex-grow p-6 overflow-y-auto">
          {children}
        </main>
      </div>

      {/* SHIFT OPENING MODAL */}
      <Modal isOpen={isShiftModalOpen} onClose={() => setIsShiftModalOpen(false)} title="Open Cash Shift Ledger">
        <div className="flex flex-col gap-4 text-left">
          <p className="text-xs text-slate-400">
            Verify the cash drawer opening balance. Opening a shift unlocks the POS Terminal checkout billing modules.
          </p>
          <Input
            label="Drawer Opening Balance (LKR)"
            type="number"
            value={openingBalance}
            onChange={(e) => setOpeningBalance(e.target.value)}
          />
          <div className="flex justify-end gap-3 mt-2">
            <Button onClick={() => setIsShiftModalOpen(false)} variant="secondary">Cancel</Button>
            <Button onClick={handleOpenShift} isLoading={isLoading}>Unlock Terminal</Button>
          </div>
        </div>
      </Modal>

      {/* SHIFT CLOSING MODAL */}
      <Modal isOpen={isCloseShiftModalOpen} onClose={() => setIsCloseShiftModalOpen(false)} title="Reconcile & Close Shift Drawer">
        <div className="flex flex-col gap-4 text-left">
          <p className="text-xs text-slate-400">
            Count the physical cash in the drawer at the end of the shift. The system will calculate any shortage or overage automatically.
          </p>
          <Input
            label="Actual Cash in Drawer (LKR)"
            type="number"
            value={actualCash}
            onChange={(e) => setActualCash(e.target.value)}
            placeholder="e.g. 6500"
            required
          />
          <Input
            label="Drawer Reconciliation Notes"
            value={closingNotes}
            onChange={(e) => setClosingNotes(e.target.value)}
            placeholder="Describe any drawer discrepancy reason"
          />
          <div className="flex justify-end gap-3 mt-2">
            <Button onClick={() => setIsCloseShiftModalOpen(false)} variant="secondary">Cancel</Button>
            <Button onClick={handleCloseShift} isLoading={isLoading} className="bg-red-500 hover:bg-red-600 text-white border-transparent">
              Lock Terminal & Close
            </Button>
          </div>
        </div>
      </Modal>

      {toastMsg && (
        <Toast
          message={toastMsg}
          onClose={() => setToastMsg('')}
        />
      )}

    </div>
  );
}
