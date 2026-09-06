'use client';

import React from 'react';
import { 
  HelpCircle, Clock, ShoppingCart, ChefHat, 
  Tv, CreditCard, ShieldCheck, FileText, Search,
  ChevronDown, ChevronRight, CheckCircle, Info
} from 'lucide-react';
import { Card, Input } from '@/components/UI';

export default function UserSopPage() {
  const [searchQuery, setSearchQuery] = React.useState('');
  const [openSection, setOpenSection] = React.useState<number | null>(0);

  const toggleSection = (idx: number) => {
    setOpenSection(openSection === idx ? null : idx);
  };

  const sopSections = [
    {
      title: "1. Beginning of Day: Opening Cashier Shifts",
      icon: <Clock className="w-5 h-5 text-brand-500" />,
      content: (
        <div className="flex flex-col gap-3 text-xs leading-relaxed text-slate-650 dark:text-slate-300 text-left">
          <p>
            Before you can register sales or access the checkout workspace, cashiers must establish an active session using the shift manager:
          </p>
          <ol className="list-decimal pl-5 flex flex-col gap-2">
            <li>Tapping <strong>"POS Terminal"</strong> in the sidebar triggers the <strong>Shift Registration Drawer</strong> if locked.</li>
            <li>Count your drawer cash balance. Input the precise starting amount in the <strong>"Opening Cash Balance"</strong> field (standard default is <code>Rs. 5,000.00</code>).</li>
            <li>Tap <strong>"Unlock POS Terminal"</strong>. The session is registered with your employee ID, timestamped, and opens access to checkout.</li>
          </ol>
          <div className="bg-slate-50 dark:bg-slate-850 p-3.5 rounded-xl border-l-4 border-brand-500 flex items-start gap-2.5">
            <Info className="w-4 h-4 text-brand-500 shrink-0 mt-0.5" />
            <span>
              <strong>Note:</strong> Access to sales totals, held checkouts, and customer databases is restricted until the cashier shift is successfully unlocked.
            </span>
          </div>
        </div>
      )
    },
    {
      title: "2. Checkout Operations & Transaction Handling",
      icon: <ShoppingCart className="w-5 h-5 text-emerald-500" />,
      content: (
        <div className="flex flex-col gap-3 text-xs leading-relaxed text-slate-650 dark:text-slate-300 text-left">
          <p>
            The checkout terminal is a touchscreen-optimized interface for adding products, applying promotions, and collecting payments:
          </p>
          <ul className="list-disc pl-5 flex flex-col gap-2">
            <li><strong>Adding Items:</strong> Click on catalog category cards to filter products. Click a item to add it to the cart list.</li>
            <li><strong>Quantity Adjustments:</strong> Inside the active cart panel, tap positive <code>+</code> or negative <code>-</code> buttons to update product quantities.</li>
            <li><strong>Parking Carts (Hold/Recall):</strong> Click <strong>"Hold Bill"</strong> and enter a reference code (e.g. Table Number, Customer Name) to park the cart draft. Recall the draft later by tapping the <strong>"Recall Folder"</strong> icon next to POS history.</li>
            <li><strong>Promotions & Coupons:</strong> Enter promo codes (e.g. <code>WELCOME10</code>) in the discount box and tap apply to deduct Flat or Percentage totals.</li>
            <li><strong>Loyalty Redemptions:</strong> Link a CRM customer profile to the sale. If the customer holds loyalty credits, choose the amount of points to redeem to apply cash discount overrides.</li>
          </ul>
        </div>
      )
    },
    {
      title: "3. Simulated EMV Card payments & NFC Overrides",
      icon: <CreditCard className="w-5 h-5 text-indigo-500" />,
      content: (
        <div className="flex flex-col gap-3 text-xs leading-relaxed text-slate-650 dark:text-slate-300 text-left">
          <p>
            The terminal is equipped with visual device mockups to simulate card reader contacts and privilege authorization keys:
          </p>
          <ol className="list-decimal pl-5 flex flex-col gap-2">
            <li><strong>EMV Contactless Taps:</strong> Choosing "Card" checkout renders a countertop terminal simulator modal. Tap <strong>"Simulate Contactless NFC Tap"</strong> to authorize the checkout. It processes through the communication sequence: <code>CONNECTING...</code> ➔ <code>AUTHORIZING...</code> ➔ <code>APPROVED</code> before printing.</li>
            <li><strong>Manager RFID / NFC Overrides:</strong> Refunding a receipt or deleting history logs triggers an RFID scan interface: <em>"Awaiting Manager Contactless Badge..."</em>. Tap <strong>"Simulate Manager NFC Badge Tap"</strong> (or enter credentials manually) to bypass cashier gates.</li>
          </ol>
        </div>
      )
    },
    {
      title: "4. Kitchen Displays (KDS Queue) & SLA Tracking",
      icon: <ChefHat className="w-5 h-5 text-amber-500" />,
      content: (
        <div className="flex flex-col gap-3 text-xs leading-relaxed text-slate-650 dark:text-slate-300 text-left">
          <p>
            The Kitchen Display System coordinates prep lanes and alerts cooks to preparation speeds:
          </p>
          <ul className="list-disc pl-5 flex flex-col gap-2">
            <li><strong>Prep Columns:</strong> Tickets progress through three lanes: **New Tickets (Pending)** ➔ **In Assembly (Preparing)** ➔ **Ready for Pickup (Ready)**.</li>
            <li><strong>Action Progression:</strong> Tapping a ticket's primary CTA button transitions it to the next column. Tapping "Deliver & Clear" removes it from the display grid.</li>
            <li><strong>SLA Delayed Warning:</strong> If a ticket remains active longer than your KDS warning threshold (configured in global settings, default 10 minutes), the card pulses with a <strong>glowing red warning border</strong> and displays the overdue duration.</li>
          </ul>
        </div>
      )
    },
    {
      title: "5. Customer Widescreen Display TV Board",
      icon: <Tv className="w-5 h-5 text-violet-500" />,
      content: (
        <div className="flex flex-col gap-3 text-xs leading-relaxed text-slate-650 dark:text-slate-300 text-left">
          <p>
            Designed for public lobby screens, the TV Status Board displays order readiness stats in real-time:
          </p>
          <ul className="list-disc pl-5 flex flex-col gap-2">
            <li><strong>Instant Sync (SSE):</strong> Screen state refreshes automatically within milliseconds of a KDS update, removing the need for browser refreshes.</li>
            <li><strong>Chime & Voice TTS Callouts:</strong> Newly ready orders trigger a luxury 5-note Bell Chime, followed immediately by an automated speech announcement: <em>"Order number [XX] is ready for pickup!"</em>.</li>
            <li><strong>Display Controls:</strong> Use the header buttons to toggle audio chimes, enable/disable spoken voice callouts, switch color themes (Light/Dark), or maximize the view to Fullscreen.</li>
          </ul>
        </div>
      )
    },
    {
      title: "6. Digital Receipts & CSAT Customer Feedback",
      icon: <FileText className="w-5 h-5 text-teal-500" />,
      content: (
        <div className="flex flex-col gap-3 text-xs leading-relaxed text-slate-650 dark:text-slate-300 text-left">
          <p>
            Digital receipt routes provide clean checkout invoice printouts and CSAT survey forms:
          </p>
          <ul className="list-disc pl-5 flex flex-col gap-2">
            <li><strong>QR Code Mobile Downloads:</strong> Receipts render a zero-dependency QR code. Customers can scan the QR code using their phone to download and save the digital receipt instantly.</li>
            <li><strong>Branding customization:</strong> Custom logos, welcome greetings (header), and promotional disclaimers (footer) configured by managers render dynamically on receipt sheets.</li>
            <li><strong>CSAT Rating Widget:</strong> Customers can select smiley ratings (😠 to 😊) and submit reviews. These scores feed directly back to the **Customer Feedback (CSAT)** ledger inside the manager's analytics tab.</li>
          </ul>
        </div>
      )
    },
    {
      title: "7. Shift Closure & Financial Reconciliation",
      icon: <ShieldCheck className="w-5 h-5 text-brand-600" />,
      content: (
        <div className="flex flex-col gap-3 text-xs leading-relaxed text-slate-650 dark:text-slate-300 text-left">
          <p>
            At the end of your shift or store hours, cashiers must close out their registers for audit tracking:
          </p>
          <ol className="list-decimal pl-5 flex flex-col gap-2">
            <li>Tap the active user shift indicator in the top navbar and choose <strong>"Close Cashier Shift"</strong>.</li>
            <li>Perform a physical count of all cash in the drawer. Input the total cash in the closure modal.</li>
            <li>The system cross-references this with opening balance + POS cash sales to calculate expected drawer balances.</li>
            <li>Tap <strong>"Confirm Shift Reconciliation"</strong>. Shift states are locked, drawers are closed, and cashier discrepancy logs (variances) are recorded in analytics.</li>
          </ol>
        </div>
      )
    }
  ];

  const filteredSections = sopSections.filter(section => 
    section.title.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="flex flex-col gap-6 text-left pb-10 max-w-4xl">
      
      {/* Page Header */}
      <div className="flex flex-col gap-1.5 border-b border-slate-100 dark:border-slate-800 pb-4">
        <h2 className="text-2xl font-bold dark:text-white flex items-center gap-2">
          <HelpCircle className="w-6 h-6 text-brand-500" />
          Standard Operating Procedures (SOP) & User Guide
        </h2>
        <p className="text-xs text-slate-400">
          Step-by-step training manuals and procedures for cashiers, cooks, and store administrators.
        </p>
      </div>

      {/* Search Filter Bar */}
      <div className="flex flex-col md:flex-row gap-4 items-start md:items-center justify-between">
        <div className="flex items-center gap-3 bg-white dark:bg-slate-900 p-2.5 rounded-2xl border border-slate-105 dark:border-slate-800/80 shadow-sm w-full max-w-md">
          <Search className="w-4 h-4 text-slate-400 shrink-0 ml-1.5" />
          <input 
            type="text" 
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search manuals (e.g. shift, checkout, KDS)..." 
            className="w-full text-xs bg-transparent focus:outline-none text-slate-850 dark:text-white"
          />
        </div>
      </div>

      {/* Quick Reference Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        
        <Card className="p-4 border-slate-105 dark:border-slate-850 bg-white/60 dark:bg-slate-900/40 hover:border-brand-500/20 transition-all duration-200">
          <h3 className="text-[10px] font-extrabold text-slate-400 dark:text-slate-500 uppercase tracking-wider mb-2 flex items-center gap-1.5">
            <Info className="w-3.5 h-3.5 text-brand-500" />
            System Web Links
          </h3>
          <div className="flex flex-col gap-1.5 text-xs text-slate-650 dark:text-slate-350">
            <div className="flex justify-between items-center border-b border-slate-50 dark:border-slate-800/50 pb-1">
              <span>Swagger API Docs:</span>
              <a href="http://localhost:8000/docs" target="_blank" rel="noreferrer" className="text-brand-500 hover:underline font-bold text-[10px]">
                /docs
              </a>
            </div>
            <div className="flex justify-between items-center pt-0.5">
              <span>TV Wait Lobby:</span>
              <a href="/order-status" target="_blank" rel="noreferrer" className="text-brand-500 hover:underline font-bold text-[10px]">
                /order-status
              </a>
            </div>
          </div>
        </Card>
        
        <Card className="p-4 border-slate-105 dark:border-slate-850 bg-white/60 dark:bg-slate-900/40 hover:border-emerald-500/20 transition-all duration-200">
          <h3 className="text-[10px] font-extrabold text-slate-400 dark:text-slate-500 uppercase tracking-wider mb-2 flex items-center gap-1.5">
            <Clock className="w-3.5 h-3.5 text-emerald-500" />
            Default Float & Limits
          </h3>
          <div className="flex flex-col gap-1.5 text-xs text-slate-650 dark:text-slate-350">
            <div className="flex justify-between items-center border-b border-slate-50 dark:border-slate-800/50 pb-1">
              <span>Opening Cash Float:</span>
              <span className="font-bold text-slate-800 dark:text-slate-200">Rs. 5,000.00</span>
            </div>
            <div className="flex justify-between items-center pt-0.5">
              <span>KDS SLA Alert:</span>
              <span className="font-bold text-slate-800 dark:text-slate-200">10 Minutes Max</span>
            </div>
          </div>
        </Card>

        <Card className="p-4 border-slate-105 dark:border-slate-850 bg-white/60 dark:bg-slate-900/40 hover:border-indigo-500/20 transition-all duration-200">
          <h3 className="text-[10px] font-extrabold text-slate-400 dark:text-slate-500 uppercase tracking-wider mb-2 flex items-center gap-1.5">
            <CreditCard className="w-3.5 h-3.5 text-indigo-500" />
            Coupons & Vouchers
          </h3>
          <div className="flex flex-col gap-1.5 text-xs text-slate-650 dark:text-slate-350">
            <div className="flex justify-between items-center border-b border-slate-50 dark:border-slate-800/50 pb-1">
              <span>Promo Coupons:</span>
              <span className="font-bold text-slate-800 dark:text-slate-200">WELCOME10, FLAT200</span>
            </div>
            <div className="flex justify-between items-center pt-0.5">
              <span>Voucher Cards:</span>
              <span className="font-bold text-slate-800 dark:text-slate-200">GIFT500, GIFT1000</span>
            </div>
          </div>
        </Card>

      </div>

      {/* Manuals Accordion Wrapper */}
      <div className="flex flex-col gap-4">
        {filteredSections.length === 0 ? (
          <span className="text-sm text-slate-400 text-center py-10 font-sans">No matching manual sections found.</span>
        ) : (
          filteredSections.map((section, idx) => {
            const isSectionOpen = openSection === idx;
            return (
              <Card key={idx} className="p-0 overflow-hidden border-slate-100 dark:border-slate-850">
                
                {/* Accordion Trigger Header */}
                <button
                  onClick={() => toggleSection(idx)}
                  className={`w-full p-5 flex items-center justify-between text-left transition-colors duration-200 ${
                    isSectionOpen 
                      ? 'bg-slate-50/50 dark:bg-slate-900/40 border-b border-slate-100 dark:border-slate-850' 
                      : 'hover:bg-slate-50/20 dark:hover:bg-slate-900/10'
                  }`}
                >
                  <div className="flex items-center gap-3">
                    {section.icon}
                    <span className="font-bold text-sm text-slate-850 dark:text-slate-100 font-sans">
                      {section.title}
                    </span>
                  </div>
                  {isSectionOpen ? (
                    <ChevronDown className="w-4 h-4 text-slate-400" />
                  ) : (
                    <ChevronRight className="w-4 h-4 text-slate-400" />
                  )}
                </button>

                {/* Content Block */}
                {isSectionOpen && (
                  <div className="p-5 bg-white dark:bg-slate-950/20 animate-fade-in border-t border-slate-50 dark:border-slate-850/30">
                    {section.content}
                  </div>
                )}

              </Card>
            );
          })
        )}
      </div>

      {/* Interactive Quick Tip Footer */}
      <div className="bg-brand-500/5 dark:bg-brand-500/10 border border-brand-500/15 p-5 rounded-2xl flex items-start gap-3 mt-4">
        <CheckCircle className="w-5 h-5 text-brand-500 shrink-0 mt-0.5" />
        <div className="flex flex-col gap-1 text-left text-xs leading-relaxed text-slate-650 dark:text-slate-350">
          <span className="font-bold text-brand-700 dark:text-brand-400">Need immediate technical assistance?</span>
          <span>
            If the cash terminal drawer discrepancies do not balance, or the real-time TV displays fail to connect, restart the server stack using Docker Compose or contact the system administrator.
          </span>
        </div>
      </div>

    </div>
  );
}
