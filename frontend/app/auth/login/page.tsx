'use client';

import React from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { Store, Loader2, Info } from 'lucide-react';
import { usePOSStore } from '@/store/usePOSStore';
import { apiClient } from '@/services/api';
import { Button, Input, Card, Toast } from '@/components/UI';

function LoginForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  
  const [email, setEmail] = React.useState('admin@smartpos.com');
  const [password, setPassword] = React.useState('admin123');
  const [isLoading, setIsLoading] = React.useState(false);
  
  const [toastMsg, setToastMsg] = React.useState('');
  const [toastType, setToastType] = React.useState<'success' | 'error'>('success');
  const setAuthContext = usePOSStore((state) => state.setAuthContext);

  // Check if setup is requested
  React.useEffect(() => {
    if (searchParams.get('setup') === 'true') {
      handleInitialSetup();
    }
  }, [searchParams]);

  const handleInitialSetup = async () => {
    setIsLoading(true);
    try {
      const res = await apiClient.post('/auth/setup-initial-admin');
      if (res.data.success) {
        setToastType('success');
        setToastMsg(res.data.data.message);
      } else {
        setToastType('error');
        setToastMsg(res.data.error || 'Setup already done.');
      }
    } catch (err: any) {
      setToastType('error');
      setToastMsg('Failed to run setup initialization.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    try {
      const params = new URLSearchParams();
      params.append('username', email);
      params.append('password', password);

      const response = await apiClient.post('/auth/login', params, {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded'
        }
      });

      if (response.data.success && response.data.data) {
        const { access_token, refresh_token } = response.data.data;
        localStorage.setItem('access_token', access_token);
        localStorage.setItem('refresh_token', refresh_token);

        // Fetch User Info
        const userRes = await apiClient.get('/auth/me');
        if (userRes.data.success && userRes.data.data) {
          const user = userRes.data.data;
          
          // Seed store
          setAuthContext(
            user,
            user.company || { id: user.company_id, name: "Smart POS Corp" },
            user.branches?.[0] || null
          );

          setToastType('success');
          setToastMsg('Successfully logged in. Entering POS System...');
          
          setTimeout(() => {
            // Redirect to dashboard or POS billing screen
            router.push('/dashboard');
          }, 1500);
        }
      } else {
        setToastType('error');
        setToastMsg(response.data.error || 'Invalid credentials.');
      }
    } catch (err: any) {
      setToastType('error');
      setToastMsg(err.response?.data?.error || 'Authentication failed. Please check connection.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-6 bg-gradient-to-br from-slate-50 to-violet-50 dark:from-slate-950 dark:to-zinc-950">
      
      <div className="w-full max-w-md flex flex-col gap-6">
        
        {/* Logo */}
        <div className="flex items-center gap-3 justify-center">
          <div className="bg-brand-500 text-white p-2.5 rounded-2xl shadow-lg">
            <Store className="w-6 h-6" />
          </div>
          <div className="text-left">
            <h1 className="font-extrabold text-xl dark:text-white leading-none">Smart POS</h1>
            <span className="text-[10px] text-brand-500 font-bold uppercase tracking-widest">XerexLabs</span>
          </div>
        </div>

        <Card className="p-8">
          <div className="flex flex-col gap-2 mb-6">
            <h2 className="text-xl font-bold dark:text-white">Sign In to Dashboard</h2>
            <p className="text-sm text-slate-400">Enter your credentials to manage your store.</p>
          </div>

          <form onSubmit={handleLogin} className="flex flex-col gap-4">
            <Input
              label="Email Address"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="e.g. admin@smartpos.com"
              required
            />
            
            <Input
              label="Password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              required
            />

            <Button type="submit" isLoading={isLoading} className="w-full mt-2">
              Sign In
            </Button>
          </form>

          {/* Quick Helper for fresh databases */}
          <div className="mt-6 p-4 rounded-xl bg-violet-50/50 dark:bg-violet-950/20 border border-violet-100/50 dark:border-brand-900/10 flex gap-3 text-left">
            <Info className="w-5 h-5 text-brand-500 shrink-0 mt-0.5" />
            <div className="flex flex-col gap-1">
              <span className="text-xs font-semibold text-brand-700 dark:text-brand-400">First Time Deploying?</span>
              <p className="text-[11px] text-slate-500 dark:text-slate-400 leading-normal">
                Click "Initial Setup" at the top right, or click below to automatically seed default admin credentials (`admin@smartpos.com` / `admin123`).
              </p>
              <button 
                onClick={handleInitialSetup} 
                className="text-[11px] font-bold text-brand-600 dark:text-brand-400 hover:underline text-left mt-1.5 flex items-center gap-1"
                disabled={isLoading}
              >
                {isLoading && <Loader2 className="w-3 h-3 animate-spin" />}
                Run Database Initial Seed
              </button>
            </div>
          </div>

        </Card>
      </div>

      {toastMsg && (
        <Toast
          message={toastMsg}
          type={toastType}
          onClose={() => setToastMsg('')}
        />
      )}

    </div>
  );
}

export default function LoginPage() {
  return (
    <React.Suspense fallback={
      <div className="min-h-screen flex items-center justify-center bg-slate-50 dark:bg-slate-950 text-slate-400">
        <Loader2 className="w-6 h-6 animate-spin text-brand-500" />
      </div>
    }>
      <LoginForm />
    </React.Suspense>
  );
}

