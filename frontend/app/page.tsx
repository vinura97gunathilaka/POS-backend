'use client';

import React from 'react';
import Link from 'next/link';
import { motion } from 'framer-motion';
import { Store, Shield, ArrowRight, Activity, Terminal } from 'lucide-react';
import { Button, Card } from '@/components/UI';

export default function LandingPage() {
  return (
    <div className="relative min-h-screen overflow-hidden flex flex-col justify-between bg-gradient-to-br from-slate-50 via-white to-violet-50 dark:from-slate-950 dark:via-slate-900 dark:to-zinc-950">
      
      {/* Background radial glow */}
      <div className="absolute top-[-20%] left-[-20%] w-[60%] h-[60%] rounded-full bg-violet-400/10 blur-[120px] pointer-events-none" />
      <div className="absolute bottom-[-20%] right-[-20%] w-[60%] h-[60%] rounded-full bg-brand-500/10 blur-[120px] pointer-events-none" />

      {/* Top Header */}
      <header className="max-w-7xl w-full mx-auto px-6 py-6 flex items-center justify-between z-10">
        <div className="flex items-center gap-3">
          <div className="bg-brand-500 text-white p-2.5 rounded-2xl shadow-lg shadow-brand-500/20">
            <Store className="w-6 h-6" />
          </div>
          <div>
            <h1 className="font-extrabold text-xl tracking-tight bg-gradient-to-r from-slate-900 to-violet-950 dark:from-white dark:to-violet-200 bg-clip-text text-transparent">
              Smart POS
            </h1>
            <p className="text-[10px] text-brand-500 font-bold uppercase tracking-widest">XerexLabs</p>
          </div>
        </div>
        <div className="flex items-center gap-4">
          <Link href="/auth/login">
            <Button variant="ghost">Sign In</Button>
          </Link>
          <Link href="/auth/login?setup=true">
            <Button variant="secondary" icon={<Terminal className="w-4 h-4" />}>
              Initial Setup
            </Button>
          </Link>
        </div>
      </header>

      {/* Hero Body */}
      <main className="max-w-7xl w-full mx-auto px-6 py-12 grid grid-cols-1 lg:grid-cols-12 items-center gap-12 z-10 flex-grow">
        
        {/* Left Intro Column */}
        <div className="lg:col-span-6 flex flex-col gap-6 text-left">
          <motion.div
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4 }}
            className="inline-flex items-center gap-2 bg-brand-50 dark:bg-brand-950/40 border border-brand-100 dark:border-brand-900/30 px-3 py-1.5 rounded-full text-brand-600 dark:text-brand-400 text-xs font-semibold w-fit"
          >
            <Activity className="w-3.5 h-3.5 animate-pulse" />
            Next-Gen Cloud POS Engine v1.0
          </motion.div>

          <motion.h2
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.1 }}
            className="text-4xl sm:text-5xl lg:text-6xl font-extrabold tracking-tight text-slate-900 dark:text-white leading-[1.1]"
          >
            One Platform.<br />
            Every Sale.<br />
            <span className="bg-gradient-to-r from-brand-500 to-violet-400 bg-clip-text text-transparent">
              Complete Control.
            </span>
          </motion.h2>

          <motion.p
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.2 }}
            className="text-slate-500 dark:text-slate-400 max-w-lg text-base sm:text-lg leading-relaxed"
          >
            Empower your retail business with multi-company multi-branch support, lightning-fast touch billing, dynamic loyalty systems, and real-time inventory synchronization.
          </motion.p>

          <motion.div
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.3 }}
            className="flex flex-wrap gap-4 mt-2"
          >
            <Link href="/auth/login">
              <Button variant="primary" icon={<ArrowRight className="w-5 h-5" />} className="px-6 py-6 text-base rounded-2xl">
                Enter Terminal
              </Button>
            </Link>
          </motion.div>
        </div>

        {/* Right Preview Column */}
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.6, delay: 0.2 }}
          className="lg:col-span-6 flex justify-center"
        >
          <div className="relative w-full max-w-md">
            {/* Visual background card decorations */}
            <div className="absolute inset-0 bg-brand-500/10 rounded-3xl blur-2xl transform rotate-6 scale-95" />
            
            <Card className="relative shadow-2xl bg-white/80 dark:bg-slate-900/80 backdrop-blur-md border border-slate-100 dark:border-slate-800 rounded-3xl overflow-hidden p-8 flex flex-col gap-6">
              
              {/* Feature summary cards */}
              <div className="flex items-center gap-4 border-b border-slate-100 dark:border-slate-800 pb-5">
                <div className="bg-brand-500/10 p-3 rounded-2xl text-brand-500">
                  <Shield className="w-6 h-6" />
                </div>
                <div>
                  <h4 className="font-semibold text-slate-800 dark:text-slate-100">Enterprise Security</h4>
                  <p className="text-xs text-slate-400">JWT Token rotation & strict RBAC authorization</p>
                </div>
              </div>

              <div className="flex items-center gap-4 border-b border-slate-100 dark:border-slate-800 pb-5">
                <div className="bg-emerald-500/10 p-3 rounded-2xl text-emerald-500">
                  <Store className="w-6 h-6" />
                </div>
                <div>
                  <h4 className="font-semibold text-slate-800 dark:text-slate-100">Multi-Branch Sync</h4>
                  <p className="text-xs text-slate-400">Real-time inventory levels & cross-branch transfers</p>
                </div>
              </div>

              <div className="flex items-center gap-4">
                <div className="bg-violet-500/10 p-3 rounded-2xl text-violet-500">
                  <Activity className="w-6 h-6" />
                </div>
                <div>
                  <h4 className="font-semibold text-slate-800 dark:text-slate-100">AI-Ready Insights</h4>
                  <p className="text-xs text-slate-400">Advanced sales trend reporting & performance cards</p>
                </div>
              </div>

            </Card>
          </div>
        </motion.div>

      </main>

      {/* Bottom Footer */}
      <footer className="w-full text-center py-6 text-xs text-slate-400 dark:text-slate-500 border-t border-slate-100 dark:border-slate-900 z-10 bg-white/20 dark:bg-slate-950/20 backdrop-blur-sm">
        © 2026 XerexLabs. All rights reserved. Smart POS is a registered trademark of XerexLabs.
      </footer>

    </div>
  );
}
