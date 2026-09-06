'use client';

import React from 'react';
import { useParams } from 'next/navigation';
import { 
  Printer, CheckCircle2, AlertCircle, ShoppingBag, 
  MapPin, Phone, Mail, Calendar, User, Clock, CreditCard
} from 'lucide-react';
import { apiClient } from '@/services/api';
import { Skeleton } from '@/components/UI';

export default function PublicReceiptPage() {
  const params = useParams();
  const invoiceNumber = params?.invoiceNumber as string;

  const [sale, setSale] = React.useState<any>(null);
  const [isLoading, setIsLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);

  // CSAT states
  const [rating, setRating] = React.useState<number>(0);
  const [feedbackText, setFeedbackText] = React.useState<string>('');
  const [csatSubmitted, setCsatSubmitted] = React.useState<boolean>(false);
  const [isCsatSubmitting, setIsCsatSubmitting] = React.useState<boolean>(false);

  React.useEffect(() => {
    if (!invoiceNumber) return;
    setIsLoading(true);
    apiClient.get(`/sales/public/receipt/${invoiceNumber}`)
      .then((res) => {
        if (res.data.success && res.data.data) {
          const saleData = res.data.data;
          setSale(saleData);
          if (saleData.csat_feedback) {
            setRating(saleData.csat_feedback.rating);
            setFeedbackText(saleData.csat_feedback.feedback_text || '');
            setCsatSubmitted(true);
          }
        } else {
          setError('Could not find the requested receipt.');
        }
      })
      .catch((err) => {
        setError(err.response?.data?.detail || 'Error loading receipt.');
      })
      .finally(() => {
        setIsLoading(false);
      });
  }, [invoiceNumber]);

  const handlePrint = () => {
    window.print();
  };

  const handleSubmitCSAT = async () => {
    if (rating < 1 || rating > 5) return;
    setIsCsatSubmitting(true);
    try {
      const res = await apiClient.post(`/sales/public/receipt/${invoiceNumber}/feedback`, {
        rating,
        feedback_text: feedbackText || null
      });
      if (res.data.success) {
        setCsatSubmitted(true);
      }
    } catch (err: any) {
      alert(err.response?.data?.detail || "Failed to submit feedback. Please try again.");
    } finally {
      setIsCsatSubmitting(false);
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-white dark:bg-slate-950 flex items-center justify-center p-6 text-left">
        <div className="bg-white dark:bg-slate-950 border border-slate-100 dark:border-slate-850 rounded-3xl p-8 max-w-md w-full shadow-lg flex flex-col gap-4">
          <Skeleton className="h-10 w-2/3 mx-auto" />
          <Skeleton className="h-6 w-1/2 mx-auto" />
          <div className="border-t border-b border-dashed border-slate-200 dark:border-slate-800 py-6 my-2 flex flex-col gap-3">
            <Skeleton className="h-5 w-full" />
            <Skeleton className="h-5 w-5/6" />
            <Skeleton className="h-5 w-full" />
          </div>
          <Skeleton className="h-12 w-full rounded-2xl" />
        </div>
      </div>
    );
  }

  if (error || !sale) {
    return (
      <div className="min-h-screen bg-white dark:bg-slate-950 flex items-center justify-center p-6 text-left">
        <div className="bg-white dark:bg-slate-950 border border-slate-100 dark:border-slate-850 rounded-3xl p-8 max-w-md w-full shadow-lg text-center flex flex-col items-center gap-4">
          <AlertCircle className="w-16 h-16 text-red-500 animate-bounce" />
          <h3 className="text-xl font-bold text-slate-800 dark:text-white">Receipt Not Found</h3>
          <p className="text-sm text-slate-550 dark:text-slate-400">
            {error || 'This receipt might have been archived or does not exist.'}
          </p>
        </div>
      </div>
    );
  }

  const items = sale.items || [];
  const payments = sale.payments || [];
  const company = sale.company || {};
  const branch = sale.branch || {};
  const cashierName = sale.cashier_name || 'Cashier';

  return (
    <div className="min-h-screen bg-white dark:bg-slate-950 flex flex-col items-center justify-center p-4 sm:p-6 print:bg-white print:p-0 text-left">
      
      {/* Receipt Card Wrapper */}
      <div className="bg-white dark:bg-slate-950 border border-slate-200/60 dark:border-slate-850 rounded-3xl max-w-lg w-full shadow-xl overflow-hidden print:shadow-none print:border-none print:my-0 my-8">
        
        {/* Decorative Top Accent */}
        <div className="h-2 bg-gradient-to-r from-brand-500 via-indigo-500 to-emerald-500 print:hidden" />

        {/* Content Body */}
        <div className="p-6 sm:p-8 flex flex-col gap-6 print:p-4">
          
          {/* Header Store Branding */}
          <div className="flex flex-col items-center text-center gap-2 border-b border-dashed border-slate-200 dark:border-slate-800 pb-5">
            {(company.settings?.receipt_logo_url || company.logo_url) && (
              <img 
                src={company.settings?.receipt_logo_url || company.logo_url} 
                alt={company.name || 'Store Logo'} 
                className="w-16 h-16 rounded-2xl object-cover shadow-sm mb-1 print:w-12 print:h-12"
              />
            )}
            <h1 className="text-xl font-extrabold text-slate-850 dark:text-white">{company.name || 'Smart POS Store'}</h1>
            <p className="text-xs font-bold text-brand-600 dark:text-brand-400 bg-brand-500/10 px-2.5 py-0.5 rounded-full uppercase tracking-wider">
              {branch.name || 'Branch'}
            </p>
            
            {/* Store Contact details */}
            <div className="flex flex-col gap-1 text-[10px] text-slate-450 mt-1 max-w-xs font-medium">
              {branch.address && (
                <span className="flex items-center justify-center gap-1">
                  <MapPin className="w-3 h-3 shrink-0" /> {branch.address}
                </span>
              )}
              <div className="flex items-center justify-center gap-3">
                {branch.phone && (
                  <span className="flex items-center gap-0.5">
                    <Phone className="w-3 h-3 shrink-0" /> {branch.phone}
                  </span>
                )}
                {branch.email && (
                  <span className="flex items-center gap-0.5">
                    <Mail className="w-3 h-3 shrink-0" /> {branch.email}
                  </span>
                )}
              </div>
            </div>
          </div>

          {/* Transaction Metadata Grid */}
          <div className="grid grid-cols-2 gap-4 text-xs bg-slate-50 dark:bg-slate-900/50 p-4 rounded-2xl border border-slate-100 dark:border-slate-850 print:bg-white print:border-none print:p-0">
            <div className="flex flex-col gap-1.5">
              <span className="text-[10px] uppercase font-bold tracking-wider text-slate-400">Invoice Number</span>
              <span className="font-mono font-black text-slate-700 dark:text-slate-200 text-[11px] truncate" title={sale.invoice_number}>
                {sale.invoice_number}
              </span>
            </div>
            <div className="flex flex-col gap-1.5 text-right">
              <span className="text-[10px] uppercase font-bold tracking-wider text-slate-400">Payment Status</span>
              <div>
                <span className={`px-2 py-0.5 rounded-full text-[9px] font-black uppercase tracking-wider border ${
                  sale.payment_status === 'paid' 
                    ? 'bg-emerald-500/15 text-emerald-600 border-emerald-500/20' 
                    : 'bg-amber-500/15 text-amber-600 border-amber-500/20'
                }`}>
                  {sale.payment_status}
                </span>
              </div>
            </div>
            <div className="flex flex-col gap-1.5">
              <span className="text-[10px] uppercase font-bold tracking-wider text-slate-400">Date & Time</span>
              <span className="font-semibold text-slate-600 dark:text-slate-350 flex items-center gap-1">
                <Calendar className="w-3.5 h-3.5 text-slate-400" />
                {new Date(sale.sale_date).toLocaleDateString()} {new Date(sale.sale_date).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
              </span>
            </div>
            <div className="flex flex-col gap-1.5 text-right">
              <span className="text-[10px] uppercase font-bold tracking-wider text-slate-400">Cashier Operating</span>
              <span className="font-semibold text-slate-600 dark:text-slate-350 inline-flex items-center justify-end gap-1">
                <User className="w-3.5 h-3.5 text-slate-400" />
                {cashierName}
              </span>
            </div>
          </div>

          {/* Line Items List */}
          <div className="flex flex-col gap-3">
            <h3 className="text-xs uppercase font-extrabold tracking-wider text-slate-400 border-b border-slate-100 dark:border-slate-800 pb-1.5">
              Items Purchased
            </h3>
            <div className="flex flex-col gap-3">
              {items.map((item: any, idx: number) => {
                const productName = item.variant?.product?.name || 'Product Item';
                const variantName = item.variant?.name || 'Standard';
                return (
                  <div key={idx} className="flex justify-between items-start text-xs border-b border-dashed border-slate-100 dark:border-slate-850 pb-2 last:border-none last:pb-0">
                    <div className="flex flex-col gap-0.5 min-w-0 pr-4">
                      <span className="font-bold text-slate-850 dark:text-slate-200 truncate">{productName}</span>
                      <span className="text-[10px] text-slate-450 font-medium">
                        Qty: {item.quantity} × Rs. {parseFloat(item.unit_price).toLocaleString()}
                        {variantName !== 'Standard' && ` | Variant: ${variantName}`}
                      </span>
                    </div>
                    <span className="font-black text-slate-800 dark:text-white shrink-0 font-mono">
                      Rs. {parseFloat(item.total_amount).toLocaleString(undefined, { minimumFractionDigits: 2 })}
                    </span>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Totals & Discounts Section */}
          <div className="flex flex-col gap-2.5 border-t border-dashed border-slate-250 dark:border-slate-800 pt-4 bg-slate-50/50 dark:bg-slate-900/20 p-4 rounded-2xl print:bg-white print:border-t print:p-0">
            
            <div className="flex justify-between items-center text-xs text-slate-600 dark:text-slate-400">
              <span className="font-medium">Sub-Total</span>
              <span className="font-mono font-bold">Rs. {parseFloat(sale.sub_total).toLocaleString(undefined, { minimumFractionDigits: 2 })}</span>
            </div>

            {parseFloat(sale.tax_amount) > 0 && (
              <div className="flex justify-between items-center text-xs text-slate-600 dark:text-slate-400">
                <span className="font-medium">Tax / VAT</span>
                <span className="font-mono font-bold">Rs. {parseFloat(sale.tax_amount).toLocaleString(undefined, { minimumFractionDigits: 2 })}</span>
              </div>
            )}

            {parseFloat(sale.discount_amount) > 0 && (
              <div className="flex justify-between items-center text-xs text-red-500">
                <span className="font-medium">Discounts / Promo Code</span>
                <span className="font-mono font-bold">- Rs. {parseFloat(sale.discount_amount).toLocaleString(undefined, { minimumFractionDigits: 2 })}</span>
              </div>
            )}

            {parseFloat(sale.loyalty_discount) > 0 && (
              <div className="flex justify-between items-center text-xs text-red-500">
                <span className="font-medium">Loyalty Redeemed ({sale.loyalty_points_redeemed} pts)</span>
                <span className="font-mono font-bold">- Rs. {parseFloat(sale.loyalty_discount).toLocaleString(undefined, { minimumFractionDigits: 2 })}</span>
              </div>
            )}

            <div className="flex justify-between items-center border-t border-dashed border-slate-200 dark:border-slate-800 pt-3 mt-1">
              <span className="text-sm font-extrabold text-slate-850 dark:text-white">Grand Net Amount</span>
              <span className="text-base font-extrabold text-slate-950 dark:text-white font-mono">
                Rs. {parseFloat(sale.net_amount).toLocaleString(undefined, { minimumFractionDigits: 2 })}
              </span>
            </div>
          </div>

          {/* Payment Methods Breakdown */}
          <div className="flex flex-col gap-2 bg-slate-50 dark:bg-slate-900/35 p-3 rounded-2xl border border-slate-100 dark:border-slate-850 print:bg-white print:border-none print:p-0">
            <h4 className="text-[10px] uppercase font-bold text-slate-400 tracking-wider">Settled Settle Shares</h4>
            <div className="flex flex-col gap-1.5 text-xs">
              {payments.map((p: any, idx: number) => (
                <div key={idx} className="flex justify-between items-center">
                  <span className="capitalize font-semibold text-slate-650 dark:text-slate-400 flex items-center gap-1">
                    <CreditCard className="w-3.5 h-3.5 text-brand-500 shrink-0" />
                    {p.payment_method === 'qr_payment' ? 'QR Code' : p.payment_method}
                    {p.transaction_reference && <span className="text-[9px] font-mono text-slate-400">({p.transaction_reference})</span>}
                  </span>
                  <span className="font-mono font-bold text-slate-800 dark:text-slate-200">
                    Rs. {parseFloat(p.amount).toLocaleString(undefined, { minimumFractionDigits: 2 })}
                  </span>
                </div>
              ))}
              
              {parseFloat(sale.change_returned) > 0 && (
                <div className="flex justify-between items-center border-t border-dashed border-slate-200 dark:border-slate-800 pt-1.5 mt-0.5 text-slate-500">
                  <span className="font-medium">Change Returned</span>
                  <span className="font-mono font-bold">
                    Rs. {parseFloat(sale.change_returned).toLocaleString(undefined, { minimumFractionDigits: 2 })}
                  </span>
                </div>
              )}
            </div>
          </div>

          {/* Dynamic QR Code for Mobile Access */}
          {typeof window !== 'undefined' && (
            <div className="flex flex-col items-center gap-1.5 py-3.5 bg-slate-50 dark:bg-slate-900/20 border border-slate-100 dark:border-slate-850 rounded-2xl print:hidden">
              <img 
                src={`https://api.qrserver.com/v1/create-qr-code/?size=100x100&data=${encodeURIComponent(window.location.href)}`} 
                alt="Receipt QR Code"
                className="w-20 h-20 bg-white p-1 rounded-lg border border-slate-200 dark:border-slate-800"
              />
              <span className="text-[9px] font-bold text-slate-405 dark:text-slate-500 uppercase tracking-widest">Scan to view on mobile</span>
            </div>
          )}

          {/* Customer Satisfaction Rating (CSAT) Widget */}
          <div className="flex flex-col gap-3.5 bg-slate-50/50 dark:bg-slate-900/30 p-5 rounded-2xl border border-slate-100 dark:border-slate-850 print:hidden text-center items-center">
            <h4 className="text-xs uppercase font-extrabold tracking-wider text-slate-400">Rate Your Experience</h4>
            
            {csatSubmitted ? (
              <div className="flex flex-col items-center gap-1.5 py-1 w-full text-center">
                <div className="flex justify-center gap-1 text-lg mb-1">
                  {[1, 2, 3, 4, 5].map((star) => (
                    <span 
                      key={star} 
                      className={`text-xl transition-all ${star <= rating ? 'opacity-100 scale-110' : 'opacity-20 grayscale'}`}
                    >
                      {['😠', '🙁', '😐', '🙂', '😊'][star - 1]}
                    </span>
                  ))}
                </div>
                <span className="text-xs font-bold text-emerald-600 dark:text-emerald-400">Thank you! Your rating has been recorded.</span>
                {feedbackText && (
                  <p className="text-[11px] text-slate-500 italic max-w-xs mt-1 border-t border-slate-100 dark:border-slate-850 pt-2 w-full text-center">
                    "{feedbackText}"
                  </p>
                )}
              </div>
            ) : (
              <div className="flex flex-col gap-3 w-full">
                <div className="flex justify-center gap-2.5">
                  {[1, 2, 3, 4, 5].map((num) => {
                    const smileys = ['😠', '🙁', '😐', '🙂', '😊'];
                    const labels = ['Very Poor', 'Poor', 'Average', 'Good', 'Excellent'];
                    return (
                      <button
                        key={num}
                        type="button"
                        onClick={() => setRating(num)}
                        className={`text-2xl p-1.5 rounded-xl transition-all duration-200 hover:scale-125 focus:outline-none ${
                          rating === num 
                            ? 'bg-brand-500/10 scale-120 border border-brand-500/20' 
                            : 'opacity-40 hover:opacity-100 grayscale hover:grayscale-0'
                        }`}
                        title={labels[num - 1]}
                      >
                        {smileys[num - 1]}
                      </button>
                    );
                  })}
                </div>
                
                {rating > 0 && (
                  <div className="flex flex-col gap-2 w-full">
                    <span className="text-[10px] text-slate-400 font-bold uppercase">
                      {['Very Poor 😠', 'Poor 🙁', 'Average 😐', 'Good 🙂', 'Excellent 😊'][rating - 1]}
                    </span>
                    <textarea
                      value={feedbackText}
                      onChange={(e) => setFeedbackText(e.target.value.slice(0, 200))}
                      placeholder="Tell us what we did well or how we can improve... (Optional)"
                      className="w-full text-xs p-3 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950 focus:outline-none focus:ring-1 focus:ring-brand-500 text-slate-800 dark:text-slate-200 min-h-[60px] resize-none"
                    />
                    <button
                      type="button"
                      disabled={isCsatSubmitting}
                      onClick={handleSubmitCSAT}
                      className="w-full bg-brand-500 hover:bg-brand-600 disabled:bg-slate-300 text-white font-bold text-xs py-2 rounded-xl transition-colors shadow-sm focus:outline-none"
                    >
                      {isCsatSubmitting ? 'Submitting...' : 'Submit Review'}
                    </button>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Footer Receipt Message */}
          <div className="flex flex-col items-center text-center gap-1 border-t border-dashed border-slate-200 dark:border-slate-800 pt-5 mt-2">
            <CheckCircle2 className="w-6 h-6 text-emerald-500" />
            <p className="text-xs font-bold text-slate-800 dark:text-white">
              {company.settings?.receipt_header || "Thank you for your purchase!"}
            </p>
            <p className="text-[10px] text-slate-450 leading-relaxed max-w-xs font-medium">
              {company.settings?.receipt_footer || "This is a digital copy of your invoice. If you need any assistance, please contact store support."}
            </p>
          </div>

        </div>

        {/* Action Button Row */}
        <div className="bg-slate-50 dark:bg-slate-900/50 p-4 border-t border-slate-100 dark:border-slate-850/80 flex items-center justify-center print:hidden">
          <button
            onClick={handlePrint}
            className="flex items-center justify-center gap-2 bg-brand-500 hover:bg-brand-600 text-white font-bold text-xs px-5 py-3 rounded-2xl shadow-sm transition-all focus:outline-none focus:ring-2 focus:ring-brand-500/50 active:scale-95"
          >
            <Printer className="w-4 h-4" />
            Print / Save Receipt PDF
          </button>
        </div>

      </div>
      
      {/* Small copyright footer */}
      <span className="text-[10px] text-slate-400 print:hidden font-medium mb-6">
        Powered by XerexLabs Smart POS Suite
      </span>

    </div>
  );
}
