'use client';

import React from 'react';
import { Tv, Clock, CheckCircle2, Flame, Inbox, Volume2, VolumeX, AlertTriangle, Sun, Moon, Maximize, Minimize } from 'lucide-react';
import axios from 'axios';

export default function PublicOrderStatusDisplay() {
  const [pendingOrders, setPendingOrders] = React.useState<any[]>([]);
  const [preparingOrders, setPreparingOrders] = React.useState<any[]>([]);
  const [readyOrders, setReadyOrders] = React.useState<any[]>([]);
  const [currentTime, setCurrentTime] = React.useState<string>('');
  const [companyId, setCompanyId] = React.useState<string>('2');
  const [branchId, setBranchId] = React.useState<string>('');
  const [branchName, setBranchName] = React.useState<string>('Main Display');
  const [soundEnabled, setSoundEnabled] = React.useState<boolean>(false);
  const [announcedTicket, setAnnouncedTicket] = React.useState<string | null>(null);
  const [loading, setLoading] = React.useState<boolean>(true);
  const [error, setError] = React.useState<string | null>(null);
  const [themeMode, setThemeMode] = React.useState<'dark' | 'light'>('dark');
  const [isFullscreen, setIsFullscreen] = React.useState<boolean>(false);
  const [voiceCalloutEnabled, setVoiceCalloutEnabled] = React.useState<boolean>(true);

  const speakTicket = (queueNo: string) => {
    if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
      window.speechSynthesis.cancel();
      const speakText = `Order number ${queueNo.replace('-', ' ')} is ready for pickup.`;
      const utterance = new SpeechSynthesisUtterance(speakText);
      utterance.rate = 0.85;
      utterance.pitch = 1.0;
      utterance.volume = 1.0;
      const voices = window.speechSynthesis.getVoices();
      const voice = voices.find(v => v.lang.startsWith('en')) || voices[0];
      if (voice) utterance.voice = voice;
      window.speechSynthesis.speak(utterance);
    }
  };

  React.useEffect(() => {
    const handleFullscreenChange = () => {
      setIsFullscreen(!!document.fullscreenElement);
    };
    document.addEventListener('fullscreenchange', handleFullscreenChange);
    return () => document.removeEventListener('fullscreenchange', handleFullscreenChange);
  }, []);

  const toggleFullscreen = () => {
    if (!document.fullscreenElement) {
      document.documentElement.requestFullscreen().catch(() => {});
    } else {
      if (document.exitFullscreen) {
        document.exitFullscreen();
      }
    }
  };

  // Store ready IDs to track transitions
  const prevReadyIdsRef = React.useRef<Set<number>>(new Set());

  // Web Audio API Synthesis for pleasant double-chime ding
  const playChime = () => {
    if (!soundEnabled) return;
    try {
      const AudioContextClass = window.AudioContext || (window as any).webkitAudioContext;
      if (!AudioContextClass) return;
      
      const audioCtx = new AudioContextClass();
      
      const playBellNote = (frequency: number, delay: number, duration: number, volume: number) => {
        const osc = audioCtx.createOscillator();
        const gainNode = audioCtx.createGain();
        const filter = audioCtx.createBiquadFilter();
        
        osc.connect(gainNode);
        gainNode.connect(filter);
        filter.connect(audioCtx.destination);
        
        osc.type = 'triangle';
        osc.frequency.value = frequency;
        
        filter.type = 'lowpass';
        filter.frequency.value = 1600;
        
        const startTime = audioCtx.currentTime + delay;
        
        gainNode.gain.setValueAtTime(0, audioCtx.currentTime);
        gainNode.gain.setValueAtTime(0, startTime);
        gainNode.gain.linearRampToValueAtTime(volume, startTime + 0.02);
        gainNode.gain.exponentialRampToValueAtTime(0.001, startTime + duration);
        
        osc.start(startTime);
        osc.stop(startTime + duration);
      };

      // C-Major warm luxury chime sequence
      playBellNote(261.63, 0.00, 0.8, 0.15); // C4 warmth
      playBellNote(523.25, 0.00, 0.6, 0.22); // C5
      playBellNote(659.25, 0.12, 0.6, 0.22); // E5
      playBellNote(783.99, 0.24, 0.8, 0.25); // G5
      playBellNote(1046.50, 0.36, 1.0, 0.15); // C6 bell
    } catch (e) {
      console.error('Audio synthesis failed', e);
    }
  };

  // Parse URL search params
  React.useEffect(() => {
    if (typeof window !== 'undefined') {
      const params = new URLSearchParams(window.location.search);
      const cId = params.get('company_id') || '2';
      const bId = params.get('branch_id') || '';
      setCompanyId(cId);
      setBranchId(bId);

      // Simple branch name mapping helper
      if (bId === '2') {
        setBranchName('Head Office');
      } else if (bId === '3') {
        setBranchName('Battaramulla Outlet');
      } else {
        setBranchName('Global Queue');
      }
    }
  }, []);

  // Update Clock
  React.useEffect(() => {
    const updateClock = () => {
      const now = new Date();
      setCurrentTime(now.toLocaleTimeString(undefined, { hour: '2-digit', minute: '2-digit', second: '2-digit' }));
    };
    updateClock();
    const interval = setInterval(updateClock, 1000);
    return () => clearInterval(interval);
  }, []);

  // Poll KDS orders & handle real-time SSE updates
  React.useEffect(() => {
    if (!companyId) return;

    const fetchOrderStatus = async () => {
      try {
        const queryParams = new URLSearchParams();
        queryParams.append('company_id', companyId);
        if (branchId) {
          queryParams.append('branch_id', branchId);
        }

        const res = await axios.get(`http://localhost:8000/api/v1/sales/kds/public`, {
          params: queryParams
        });

        if (res.data && res.data.success && res.data.data) {
          const allOrders = res.data.data;
          
          const pend = allOrders.filter((o: any) => o.preparation_status === 'pending');
          const prep = allOrders.filter((o: any) => o.preparation_status === 'preparing');
          const ready = allOrders.filter((o: any) => o.preparation_status === 'ready');

          setPendingOrders(pend);
          setPreparingOrders(prep);
          setReadyOrders(ready);
          setError(null);

          // Track ready transitions for announcement
          const currentReadyIds = new Set<number>(ready.map((o: any) => o.id));
          const prevReadyIds = prevReadyIdsRef.current;

          // Find if there is any order newly transitioned to ready
          let newlyReadyOrder: any = null;
          for (const o of ready) {
            if (!prevReadyIds.has(o.id)) {
              newlyReadyOrder = o;
              break;
            }
          }

          if (newlyReadyOrder) {
            setAnnouncedTicket(newlyReadyOrder.queue_number);
            playChime();
            if (voiceCalloutEnabled) {
              setTimeout(() => {
                speakTicket(newlyReadyOrder.queue_number);
              }, 800); // 800ms delay to let chime play first
            }
            
            // Auto hide announcement banner after 6 seconds
            setTimeout(() => {
              setAnnouncedTicket(null);
            }, 6000);
          }

          // Update ref
          prevReadyIdsRef.current = currentReadyIds;
        }
      } catch (err: any) {
        console.error('Failed to poll public orders', err);
        if (err.response?.status === 400) {
          setError(err.response?.data?.detail || 'Order Prep Monitor (KDS Queue) is currently disabled.');
        } else {
          setError('Connection to server lost. Retrying...');
        }
      } finally {
        setLoading(false);
      }
    };

    fetchOrderStatus();

    // Set up SSE Event Source for real-time push events
    const sseUrl = `http://localhost:8000/api/v1/sales/kds/events?company_id=${companyId}`;
    const eventSource = new EventSource(sseUrl);

    eventSource.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data);
        if (payload.event === 'refresh') {
          fetchOrderStatus();
        }
      } catch (err) {
        console.error('Failed to parse status board SSE payload', err);
      }
    };

    eventSource.onerror = (err) => {
      console.warn('Status board SSE connection error. Reconnecting...', err);
    };

    // Fallback slow poll every 20 seconds
    const fallbackInterval = setInterval(fetchOrderStatus, 20000);

    return () => {
      eventSource.close();
      clearInterval(fallbackInterval);
    };
  }, [companyId, branchId, soundEnabled, voiceCalloutEnabled]);

  // Locked display if KDS is disabled
  if (error && error.includes('disabled')) {
    return (
      <div className="min-h-screen bg-slate-950 text-white font-sans flex items-center justify-center p-6 select-none relative">
        <div className="absolute top-[-20%] left-[-20%] w-[60%] h-[60%] bg-red-650/10 rounded-full blur-[120px] pointer-events-none" />
        <div className="max-w-md w-full text-center flex flex-col items-center gap-6 bg-slate-900 border border-slate-800 p-10 rounded-[2.5rem] shadow-2xl relative overflow-hidden">
          <div className="absolute top-0 left-0 right-0 h-1.5 bg-red-500" />
          <div className="w-20 h-20 rounded-full bg-red-500/10 border border-red-500/20 text-red-400 flex items-center justify-center animate-bounce mb-2">
            <AlertTriangle className="w-10 h-10" />
          </div>
          <h2 className="text-2xl font-black text-slate-100 tracking-wide uppercase">KDS Display Disabled</h2>
          <p className="text-sm text-slate-400 leading-relaxed font-sans">
            {error}
          </p>
          <span className="text-[10px] text-slate-500 font-bold uppercase tracking-widest mt-2 border border-slate-850 px-3 py-1 rounded-full">
            Smart POS System
          </span>
        </div>
      </div>
    );
  }

  return (
    <div className={`min-h-screen font-sans overflow-hidden flex flex-col p-6 select-none relative transition-colors duration-300 ${
      themeMode === 'dark' ? 'bg-slate-950 text-white' : 'bg-slate-50 text-slate-900'
    }`}>
      
      {/* Root Sleek Custom Scrollbars */}
      <style dangerouslySetInnerHTML={{ __html: `
        .custom-scrollbar::-webkit-scrollbar {
          width: 5px;
        }
        .custom-scrollbar::-webkit-scrollbar-track {
          background: transparent;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb {
          background: ${themeMode === 'dark' ? 'rgba(255, 255, 255, 0.12)' : 'rgba(0, 0, 0, 0.08)'};
          border-radius: 999px;
          transition: background 0.2s ease;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb:hover {
          background: ${themeMode === 'dark' ? 'rgba(255, 255, 255, 0.25)' : 'rgba(0, 0, 0, 0.15)'};
        }
      `}} />
      
      {/* BACKGROUND GRAPHIC OR GLOWS */}
      <div className={`absolute top-[-20%] left-[-20%] w-[60%] h-[60%] rounded-full blur-[120px] pointer-events-none transition-colors duration-300 ${
        themeMode === 'dark' ? 'bg-violet-600/10' : 'bg-violet-400/5'
      }`} />
      <div className={`absolute bottom-[-20%] right-[-20%] w-[60%] h-[60%] rounded-full blur-[120px] pointer-events-none transition-colors duration-300 ${
        themeMode === 'dark' ? 'bg-emerald-600/10' : 'bg-emerald-400/5'
      }`} />

      {/* TOP HEADER */}
      <header className={`flex items-center justify-between border-b pb-5 z-10 shrink-0 transition-colors duration-300 ${
        themeMode === 'dark' ? 'border-slate-900' : 'border-slate-200'
      }`}>
        <div className="flex items-center gap-3">
          <div className="bg-brand-500 text-white p-2.5 rounded-2xl shadow-[0_0_15px_rgba(139,92,246,0.3)] animate-pulse">
            <Tv className="w-6 h-6" />
          </div>
          <div>
            <h1 className="text-xl font-black uppercase tracking-wider leading-none">Order Status Board</h1>
            <span className={`text-[10px] font-bold tracking-widest uppercase transition-colors duration-300 ${
              themeMode === 'dark' ? 'text-slate-400' : 'text-slate-500'
            }`}>{branchName} Display</span>
          </div>
        </div>

        {/* CONTROLS & TIMINGS */}
        <div className="flex items-center gap-4">
          <button 
            onClick={() => setThemeMode(themeMode === 'dark' ? 'light' : 'dark')}
            className={`p-2.5 rounded-xl border text-xs font-bold transition-all ${
              themeMode === 'dark'
                ? 'bg-slate-900 border-slate-800 text-slate-400 hover:text-white'
                : 'bg-white border-slate-200 text-slate-600 hover:text-slate-800 shadow-sm'
            }`}
            title="Toggle theme mode"
          >
            {themeMode === 'dark' ? <Sun className="w-4 h-4 text-amber-400" /> : <Moon className="w-4 h-4 text-indigo-500" />}
          </button>

          <button 
            onClick={toggleFullscreen}
            className={`p-2.5 rounded-xl border text-xs font-bold transition-all ${
              themeMode === 'dark'
                ? 'bg-slate-900 border-slate-800 text-slate-400 hover:text-white'
                : 'bg-white border-slate-200 text-slate-600 hover:text-slate-800 shadow-sm'
            }`}
            title="Toggle fullscreen mode"
          >
            {isFullscreen ? <Minimize className="w-4 h-4 text-brand-500" /> : <Maximize className="w-4 h-4 text-brand-500" />}
          </button>

          <button 
            onClick={() => setSoundEnabled(!soundEnabled)}
            className={`flex items-center gap-2 px-3 py-1.5 rounded-xl border text-xs font-bold transition-all ${
              soundEnabled 
                ? 'bg-brand-500/15 border-brand-500/30 text-brand-400 shadow-md shadow-brand-500/5' 
                : themeMode === 'dark'
                  ? 'bg-slate-900 border-slate-800 text-slate-400 hover:text-white'
                  : 'bg-white border-slate-200 text-slate-600 hover:text-slate-800 shadow-sm'
            }`}
          >
            {soundEnabled ? <Volume2 className="w-4 h-4 animate-bounce" /> : <VolumeX className="w-4 h-4" />}
            {soundEnabled ? 'Buzzer Enabled' : 'Tap to Enable Sound'}
          </button>

          <button 
            onClick={() => setVoiceCalloutEnabled(!voiceCalloutEnabled)}
            className={`flex items-center gap-2 px-3 py-1.5 rounded-xl border text-xs font-bold transition-all ${
              voiceCalloutEnabled 
                ? 'bg-indigo-500/15 border-indigo-500/30 text-indigo-400 shadow-md shadow-indigo-500/5' 
                : themeMode === 'dark'
                  ? 'bg-slate-900 border-slate-800 text-slate-400 hover:text-white'
                  : 'bg-white border-slate-200 text-slate-600 hover:text-slate-800 shadow-sm'
            }`}
          >
            <span className="relative flex h-2 w-2 shrink-0">
              {voiceCalloutEnabled && <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-indigo-400 opacity-75"></span>}
              <span className={`relative inline-flex rounded-full h-2 w-2 ${voiceCalloutEnabled ? 'bg-indigo-500' : 'bg-slate-400'}`}></span>
            </span>
            {voiceCalloutEnabled ? 'Voice Callout On' : 'Voice Callout Off'}
          </button>

          <div className={`flex items-center gap-2 px-4 py-1.5 rounded-xl shadow-inner border transition-colors duration-300 ${
            themeMode === 'dark' ? 'bg-slate-900 border-slate-800' : 'bg-white border-slate-200'
          }`}>
            <Clock className="w-4 h-4 text-brand-400" />
            <span className={`text-sm font-bold font-mono transition-colors duration-300 ${
              themeMode === 'dark' ? 'text-slate-350' : 'text-slate-700'
            }`}>{currentTime}</span>
          </div>
        </div>
      </header>

      {/* MAIN MONITOR SPLIT (3-COLUMN LAYOUT) */}
      <main className="flex-grow grid grid-cols-1 md:grid-cols-3 gap-6 py-8 z-10 min-h-0">
        
        {/* COLUMN 1: PENDING (QUEUED) */}
        <section className={`flex flex-col h-full rounded-[2rem] p-5 min-h-0 overflow-hidden shadow-inner backdrop-blur-md border transition-colors duration-300 ${
          themeMode === 'dark' ? 'bg-slate-900/20 border-slate-900/40' : 'bg-white border-slate-200'
        }`}>
          <div className={`flex items-center justify-between border-b pb-4 mb-4 shrink-0 transition-colors duration-300 ${
            themeMode === 'dark' ? 'border-slate-900' : 'border-slate-100'
          }`}>
            <div className="flex items-center gap-2">
              <Inbox className="w-4.5 h-4.5 text-indigo-500" />
              <h2 className={`text-sm font-black uppercase tracking-wide transition-colors duration-300 ${
                themeMode === 'dark' ? 'text-slate-400' : 'text-slate-600'
              }`}>New Orders</h2>
            </div>
            <span className={`border text-[10px] px-2.5 py-0.5 rounded-full font-bold transition-colors duration-300 ${
              themeMode === 'dark' ? 'bg-slate-900 border-slate-800 text-slate-400' : 'bg-slate-100 border-slate-200 text-slate-500'
            }`}>
              {pendingOrders.length}
            </span>
          </div>

          <div className="flex-grow overflow-y-auto pr-1 custom-scrollbar">
            {loading ? (
              <div className="grid grid-cols-2 gap-3 animate-pulse">
                {[1, 2, 4].map(i => (
                  <div key={i} className={`h-14 rounded-2xl border transition-colors duration-350 ${
                    themeMode === 'dark' ? 'bg-slate-900/50 border-slate-800' : 'bg-slate-200/50 border-slate-300/40'
                  }`} />
                ))}
              </div>
            ) : pendingOrders.length === 0 ? (
              <div className={`h-full flex items-center justify-center text-xs py-20 font-medium ${
                themeMode === 'dark' ? 'text-slate-600' : 'text-slate-400'
              }`}>
                No new orders queued.
              </div>
            ) : (
              <div className="grid grid-cols-2 gap-3 content-start">
                {pendingOrders.map((o) => (
                  <div 
                    key={o.id}
                    className={`font-mono text-xl font-bold py-3.5 px-2 rounded-2xl flex items-center justify-center shadow-md transition-all transform hover:scale-105 cursor-pointer duration-300 border-t-2 ${
                      themeMode === 'dark' 
                        ? 'bg-slate-900/40 border-slate-900 hover:border-slate-850 text-slate-400 border-t-indigo-500/40' 
                        : 'bg-slate-100 border-slate-250 hover:border-slate-200 text-slate-600 border-t-indigo-500/80'
                    }`}
                  >
                    {o.queue_number}
                  </div>
                ))}
              </div>
            )}
          </div>
        </section>

        {/* COLUMN 2: PREPARING (IN PROGRESS) */}
        <section className={`flex flex-col h-full rounded-[2rem] p-5 min-h-0 overflow-hidden shadow-inner backdrop-blur-md border transition-colors duration-300 ${
          themeMode === 'dark' ? 'bg-slate-900/30 border-slate-900/50' : 'bg-white border-slate-200'
        }`}>
          <div className={`flex items-center justify-between border-b pb-4 mb-4 shrink-0 transition-colors duration-300 ${
            themeMode === 'dark' ? 'border-slate-900' : 'border-slate-100'
          }`}>
            <div className="flex items-center gap-2">
              <Flame className="w-4.5 h-4.5 text-violet-500 animate-pulse" />
              <h2 className={`text-sm font-black uppercase tracking-wide transition-colors duration-300 ${
                themeMode === 'dark' ? 'text-slate-350' : 'text-slate-700'
              }`}>Preparing</h2>
            </div>
            <span className={`border text-[10px] px-2.5 py-0.5 rounded-full font-bold transition-colors duration-300 ${
              themeMode === 'dark' ? 'bg-slate-900 border-slate-800 text-slate-400' : 'bg-slate-100 border-slate-200 text-slate-500'
            }`}>
              {preparingOrders.length}
            </span>
          </div>

          <div className="flex-grow overflow-y-auto pr-1 custom-scrollbar">
            {loading ? (
              <div className="grid grid-cols-2 gap-3 animate-pulse">
                {[1, 2, 3, 4].map(i => (
                  <div key={i} className={`h-14 rounded-2xl border transition-colors duration-350 ${
                    themeMode === 'dark' ? 'bg-slate-900/50 border-slate-800' : 'bg-slate-200/50 border-slate-300/40'
                  }`} />
                ))}
              </div>
            ) : preparingOrders.length === 0 ? (
              <div className={`h-full flex items-center justify-center text-xs py-20 font-medium ${
                themeMode === 'dark' ? 'text-slate-650' : 'text-slate-400'
              }`}>
                No orders in preparation.
              </div>
            ) : (
              <div className="grid grid-cols-2 gap-3 content-start">
                {preparingOrders.map((o) => (
                  <div 
                    key={o.id}
                    className={`font-mono text-xl font-bold py-3.5 px-2 rounded-2xl flex items-center justify-center shadow-md transition-all transform hover:scale-105 cursor-pointer duration-300 border-t-2 ${
                      themeMode === 'dark' 
                        ? 'bg-slate-900/40 border-slate-900 hover:border-slate-850 text-slate-300 border-t-violet-500/40' 
                        : 'bg-slate-100 border-slate-250 hover:border-slate-200 text-slate-700 border-t-violet-500/80'
                    }`}
                  >
                    {o.queue_number}
                  </div>
                ))}
              </div>
            )}
          </div>
        </section>

        {/* COLUMN 3: READY FOR PICKUP (READY) */}
        <section className={`flex flex-col h-full rounded-[2rem] p-5 min-h-0 overflow-hidden shadow-inner backdrop-blur-md border transition-colors duration-300 ${
          themeMode === 'dark' ? 'bg-emerald-950/5 border-emerald-900/10' : 'bg-emerald-50/20 border-emerald-100/50'
        }`}>
          <div className={`flex items-center justify-between border-b pb-4 mb-4 shrink-0 transition-colors duration-300 ${
            themeMode === 'dark' ? 'border-emerald-900/10' : 'border-emerald-200/30'
          }`}>
            <div className="flex items-center gap-2">
              <CheckCircle2 className="w-4.5 h-4.5 text-emerald-500" />
              <h2 className="text-sm font-black uppercase tracking-wide text-emerald-500">Ready for Pickup</h2>
            </div>
            <span className="bg-emerald-500/10 border border-emerald-500/20 text-[10px] text-emerald-500 px-2.5 py-0.5 rounded-full font-bold">
              {readyOrders.length}
            </span>
          </div>

          <div className="flex-grow overflow-y-auto pr-1 custom-scrollbar">
            {loading ? (
              <div className="grid grid-cols-2 gap-3 animate-pulse">
                {[1, 2].map(i => (
                  <div key={i} className={`h-20 rounded-2xl border transition-colors duration-350 ${
                    themeMode === 'dark' ? 'bg-emerald-950/20 border-emerald-900/30' : 'bg-emerald-100/30 border-emerald-200/40'
                  }`} />
                ))}
              </div>
            ) : readyOrders.length === 0 ? (
              <div className={`h-full flex items-center justify-center text-xs py-20 font-medium ${
                themeMode === 'dark' ? 'text-slate-650' : 'text-slate-400'
              }`}>
                Waiting to serve next orders.
              </div>
            ) : (
              <div className="grid grid-cols-2 gap-4 content-start">
                {readyOrders.map((o) => (
                  <div 
                    key={o.id}
                    className={`font-mono text-3xl font-black py-5 px-2 rounded-2xl flex items-center justify-center shadow-lg transition-all transform hover:scale-105 cursor-pointer duration-300 animate-pulse ${
                      themeMode === 'dark'
                        ? 'bg-emerald-500/10 border-emerald-500/20 hover:border-emerald-500/40 text-emerald-400 shadow-emerald-500/5'
                        : 'bg-emerald-500/20 border-emerald-500/30 hover:border-emerald-500/50 text-emerald-600 shadow-emerald-500/10'
                    }`}
                  >
                    {o.queue_number}
                  </div>
                ))}
              </div>
            )}
          </div>
        </section>

      </main>

      {/* ERROR BANNER */}
      {error && !error.includes('disabled') && (
        <div className="fixed bottom-6 left-6 right-6 bg-red-500/10 border border-red-500/20 px-4 py-3 rounded-2xl flex items-center gap-3 z-50 text-xs text-red-400 backdrop-blur-md shadow-lg">
          <AlertTriangle className="w-4 h-4 text-red-500 shrink-0 animate-bounce" />
          <span className="font-semibold text-left">{error}</span>
        </div>
      )}

      {/* TRANSITION ALERT OVERLAY */}
      {announcedTicket && (
        <div className={`absolute inset-0 backdrop-blur-xl flex items-center justify-center z-50 animate-fade-in p-8 overflow-hidden transition-colors duration-300 ${
          themeMode === 'dark' ? 'bg-slate-950/92' : 'bg-white/92'
        }`}>
          <style dangerouslySetInnerHTML={{ __html: `
            @keyframes float-particle-green {
              0% { transform: translateY(100vh) translateX(0) rotate(0deg) scale(0.5); opacity: 0; }
              10% { opacity: 0.7; }
              90% { opacity: 0.7; }
              100% { transform: translateY(-10vh) translateX(120px) rotate(360deg) scale(1.5); opacity: 0; }
            }
            @keyframes pulse-ring-emerald {
              0% { transform: scale(0.9); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.5); }
              70% { transform: scale(1.05); box-shadow: 0 0 0 35px rgba(16, 185, 129, 0); }
              100% { transform: scale(0.9); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); }
            }
            .emerald-ring { animation: pulse-ring-emerald 2s infinite ease-in-out; }
            .particle-1 { animation: float-particle-green 7s infinite linear; left: 10%; }
            .particle-2 { animation: float-particle-green 5s infinite linear 1.2s; left: 25%; }
            .particle-3 { animation: float-particle-green 8s infinite linear 2.5s; left: 40%; }
            .particle-4 { animation: float-particle-green 6s infinite linear 0.5s; left: 60%; }
            .particle-5 { animation: float-particle-green 9s infinite linear 3.1s; left: 75%; }
            .particle-6 { animation: float-particle-green 4.5s infinite linear 1.8s; left: 85%; }
          `}} />

          {/* Floating light particles behind the modal */}
          <div className="absolute w-6 h-6 bg-emerald-500/20 rounded-full blur-[2px] pointer-events-none particle-1" />
          <div className="absolute w-8 h-8 bg-brand-500/20 rounded-full blur-[3px] pointer-events-none particle-2" />
          <div className="absolute w-4 h-4 bg-emerald-400/20 rounded-full blur-[1px] pointer-events-none particle-3" />
          <div className="absolute w-10 h-10 bg-indigo-500/20 rounded-full blur-[4px] pointer-events-none particle-4" />
          <div className="absolute w-5 h-5 bg-emerald-300/25 rounded-full blur-[2px] pointer-events-none particle-5" />
          <div className="absolute w-7 h-7 bg-brand-400/20 rounded-full blur-[3px] pointer-events-none particle-6" />

          {/* Announcement Card */}
          <div className={`max-w-2xl text-center flex flex-col items-center gap-6 p-12 rounded-[3rem] relative overflow-hidden z-10 transition-all transform hover:scale-[1.02] duration-300 border ${
            themeMode === 'dark' 
              ? 'bg-slate-900 border-slate-800 shadow-[0_0_80px_rgba(16,185,129,0.25)]' 
              : 'bg-white border-slate-200 shadow-[0_15px_50px_rgba(16,185,129,0.15)]'
          }`}>
            <div className="absolute top-0 left-0 right-0 h-1.5 bg-gradient-to-r from-emerald-500 via-brand-500 to-emerald-500" />
            <div className="w-24 h-24 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-500 flex items-center justify-center emerald-ring mb-2">
              <CheckCircle2 className="w-12 h-12" />
            </div>
            <h2 className={`text-3xl font-black tracking-wide uppercase ${
              themeMode === 'dark' ? 'text-slate-100' : 'text-slate-800'
            }`}>Order is Ready!</h2>
            <div className={`text-7xl xl:text-8xl font-black font-mono py-6 px-16 rounded-[2rem] shadow-inner tracking-wider border ${
              themeMode === 'dark' 
                ? 'text-emerald-400 bg-slate-950 border-slate-900' 
                : 'text-emerald-600 bg-slate-50 border-slate-100'
            }`}>
              {announcedTicket}
            </div>
            <p className={`text-sm max-w-sm mt-2 leading-relaxed ${
              themeMode === 'dark' ? 'text-slate-400' : 'text-slate-550'
            }`}>
              Please proceed to the pickup counter and present your invoice receipt.
            </p>
          </div>
        </div>
      )}

    </div>
  );
}
