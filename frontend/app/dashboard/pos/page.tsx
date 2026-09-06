'use client';

import React from 'react';
import { 
  Search, UserPlus, Trash2, CreditCard, Banknote, 
  Sparkles, Gift, Printer, Save, FolderOpen, Lock, Tag, ShoppingCart, ShieldAlert, History
} from 'lucide-react';
import { usePOSStore, CartItem } from '@/store/usePOSStore';
import { apiClient } from '@/services/api';
import { Button, Card, Input, Modal, Select, Toast } from '@/components/UI';
import { hasPermission } from '@/utils/permissions';
import axios from 'axios';

export default function POSPage() {
  const { 
    cart, customer, discount, discountType, payments, shift, 
    activeCompany, activeBranch, currentUser, addToCart, updateCartQuantity, 
    removeFromCart, clearCart, setCustomer, setDiscount, addPayment, 
    clearPayments, removePayment 
  } = usePOSStore();

  if (!currentUser || !hasPermission(currentUser, 'pos:checkout')) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] text-center p-6 bg-white dark:bg-slate-900 rounded-3xl border border-slate-100 dark:border-slate-800 shadow-sm text-left">
        <ShieldAlert className="w-16 h-16 text-red-500 mb-4 animate-bounce" />
        <h3 className="text-xl font-bold text-slate-800 dark:text-white mb-2">Access Denied</h3>
        <p className="text-sm text-slate-500 dark:text-slate-400 max-w-md">
          You do not have the required permissions (`pos:checkout`) to access the POS Touch Terminal billing screen. Please contact your company administrator.
        </p>
      </div>
    );
  }

  const isCurrentUserAdminOrManager = React.useMemo(() => {
    return currentUser?.is_superadmin || 
      (currentUser?.roles && currentUser.roles.some((r: any) => ['Company Admin', 'Branch Manager'].includes(r.name)));
  }, [currentUser]);

  // Component states
  const [products, setProducts] = React.useState<any[]>([]);
  const [categories, setCategories] = React.useState<any[]>([]);
  const [selectedCat, setSelectedCat] = React.useState<number | null>(null);
  const [search, setSearch] = React.useState('');
  
  const [customers, setCustomers] = React.useState<any[]>([]);
  const [searchCustomer, setSearchCustomer] = React.useState('');
  
  // Checkout Modals
  const [isPayModalOpen, setIsPayModalOpen] = React.useState(false);
  const [payMethod, setPayMethod] = React.useState('cash');
  const [payRef, setPayRef] = React.useState('');
  const [payAmount, setPayAmount] = React.useState('0');
  
  // Customer Auto-complete & Quick Add states
  const [custQuery, setCustQuery] = React.useState('');
  const [showCustDropdown, setShowCustDropdown] = React.useState(false);
  const [isQuickCustOpen, setIsQuickCustOpen] = React.useState(false);
  const [quickCustName, setQuickCustName] = React.useState('');
  const [quickCustPhone, setQuickCustPhone] = React.useState('');
  const [quickCustEmail, setQuickCustEmail] = React.useState('');

  const matchedCustomers = React.useMemo(() => {
    if (!custQuery) return [];
    return customers.filter(c => 
      (c.phone && c.phone.includes(custQuery)) ||
      (c.name && c.name.toLowerCase().includes(custQuery.toLowerCase()))
    );
  }, [customers, custQuery]);

  const handleQuickCustomerSubmit = async () => {
    if (!quickCustName) return;
    setIsLoading(true);
    try {
      const payload = {
        company_id: activeCompany.id,
        name: quickCustName,
        phone: quickCustPhone || null,
        email: quickCustEmail || null,
        credit_limit: 0
      };
      const res = await apiClient.post('/crm/customers', payload);
      if (res.data.success) {
        const newCust = res.data.data;
        setCustomers([...customers, newCust]);
        setCustomer(newCust);
        setToastType('success');
        setToastMsg('Customer registered and linked to bill!');
        setIsQuickCustOpen(false);
        setQuickCustName('');
        setQuickCustPhone('');
        setQuickCustEmail('');
      }
    } catch (err) {
      setToastType('error');
      setToastMsg('Failed to register quick customer.');
    } finally {
      setIsLoading(false);
    }
  };
  
  // Hold/Recall Modals
  const [isRecallModalOpen, setIsRecallModalOpen] = React.useState(false);
  const [heldInvoices, setHeldInvoices] = React.useState<any[]>([]);
  const [holdRefName, setHoldRefName] = React.useState('');

  // Sales History Modals/States
  const [isHistoryModalOpen, setIsHistoryModalOpen] = React.useState(false);
  const [pastSales, setPastSales] = React.useState<any[]>([]);

  // Cancellation / Override States
  const [isCancelModalOpen, setIsCancelModalOpen] = React.useState(false);
  const [selectedSaleToCancel, setSelectedSaleToCancel] = React.useState<any | null>(null);
  const [managerEmail, setManagerEmail] = React.useState('');
  const [managerPassword, setManagerPassword] = React.useState('');
  const [cancelReason, setCancelReason] = React.useState('');

  // EMV Card Terminal Simulator States
  const [isCardTerminalOpen, setIsCardTerminalOpen] = React.useState(false);
  const [cardTerminalAmount, setCardTerminalAmount] = React.useState(0);
  const [cardTerminalMsg, setCardTerminalMsg] = React.useState('');
  const [isCardProcessing, setIsCardProcessing] = React.useState(false);

  // Manager NFC Badge Override States
  const [authMethod, setAuthMethod] = React.useState<'nfc' | 'password'>('nfc');
  const [isNfcScanning, setIsNfcScanning] = React.useState(false);
  const [nfcAuthenticatedManager, setNfcAuthenticatedManager] = React.useState<string | null>(null);

  // Invoice display state after complete
  const [receiptSale, setReceiptSale] = React.useState<any | null>(null);
  
  const [toastMsg, setToastMsg] = React.useState('');
  const [toastType, setToastType] = React.useState<'success' | 'error'>('success');
  const [isLoading, setIsLoading] = React.useState(false);

  // Digital Receipt States
  const [dispatchEmail, setDispatchEmail] = React.useState('');
  const [dispatchPhone, setDispatchPhone] = React.useState('');
  const [isDispatchingEmail, setIsDispatchingEmail] = React.useState(false);
  const [isDispatchingPhone, setIsDispatchingPhone] = React.useState(false);

  const handleSendReceipt = async (type: 'email' | 'whatsapp', recipient: string) => {
    if (!receiptSale) return;
    if (type === 'email') setIsDispatchingEmail(true);
    else setIsDispatchingPhone(true);
    
    try {
      const res = await apiClient.post(`/sales/${receiptSale.id}/dispatch-receipt`, {
        type,
        recipient
      });
      if (res.data.success) {
        setToastType('success');
        setToastMsg(`Receipt sent successfully via ${type}!`);
      }
    } catch (e) {
      setToastType('error');
      setToastMsg('Failed to send receipt.');
    } finally {
      if (type === 'email') setIsDispatchingEmail(false);
      else setIsDispatchingPhone(false);
    }
  };


  // Loyalty & Promo & Voucher states
  const [loyaltyRule, setLoyaltyRule] = React.useState<any>(null);
  const [pointsToRedeem, setPointsToRedeem] = React.useState<number>(0);
  const [couponCode, setCouponCode] = React.useState<string>('');
  const [appliedCoupon, setAppliedCoupon] = React.useState<any>(null);
  const [couponError, setCouponError] = React.useState<string>('');
  const [voucherCode, setVoucherCode] = React.useState<string>('');
  const [verifiedVoucher, setVerifiedVoucher] = React.useState<any>(null);
  const [voucherError, setVoucherError] = React.useState<string>('');
  const [voucherPaymentAmount, setVoucherPaymentAmount] = React.useState<string>('0');

  // Fetch products & categories
  React.useEffect(() => {
    if (!shift) return;
    
    apiClient.get('/catalog/products')
      .then((res) => {
        if (res.data.success && res.data.data) {
          setProducts(res.data.data);
        }
      });
    
    apiClient.get('/catalog/categories')
      .then((res) => {
        if (res.data.success && res.data.data) {
          setCategories(res.data.data);
        }
      });

    apiClient.get('/crm/customers')
      .then((res) => {
        if (res.data.success && res.data.data) {
          setCustomers(res.data.data);
        }
      });

    apiClient.get('/crm/loyalty/rules')
      .then((res) => {
        if (res.data.success && res.data.data && res.data.data.length > 0) {
          const activeRule = res.data.data.find((r: any) => r.status === 'active') || res.data.data[0];
          setLoyaltyRule(activeRule);
        }
      })
      .catch(() => {});
  }, [shift]);

  React.useEffect(() => {
    setPointsToRedeem(0);
  }, [customer]);

  // Filtered Products
  const filteredProducts = React.useMemo(() => {
    return products.filter((p) => {
      const matchCat = selectedCat === null || p.category_id === selectedCat;
      const matchSearch = p.name.toLowerCase().includes(search.toLowerCase()) || 
                          (p.sku && p.sku.toLowerCase().includes(search.toLowerCase())) ||
                          (p.barcode && p.barcode.includes(search));
      return matchCat && matchSearch;
    });
  }, [products, selectedCat, search]);

  // Math Calculations
  const cartSubtotal = React.useMemo(() => {
    return cart.reduce((acc, item) => acc + (item.price * item.quantity), 0);
  }, [cart]);

  const cartTax = React.useMemo(() => {
    return cart.reduce((acc, item) => acc + (item.price * item.quantity * (item.taxRate / 100)), 0);
  }, [cart]);

  const cartDiscountAmount = React.useMemo(() => {
    if (discountType === 'percentage') {
      return cartSubtotal * (discount / 100);
    }
    return discount;
  }, [cartSubtotal, discount, discountType]);

  const getCouponDiscount = React.useCallback(() => {
    if (!appliedCoupon) return 0;
    const cartVal = cartSubtotal + cartTax - cartDiscountAmount;
    if (appliedCoupon.type === 'percentage') {
      return cartVal * (appliedCoupon.value / 100);
    }
    return Math.min(appliedCoupon.value, cartVal);
  }, [appliedCoupon, cartSubtotal, cartTax, cartDiscountAmount]);

  const pointsDiscount = React.useMemo(() => {
    const pointVal = loyaltyRule ? parseFloat(loyaltyRule.point_value) : 1;
    return pointsToRedeem * pointVal;
  }, [pointsToRedeem, loyaltyRule]);

  const cartNetTotal = React.useMemo(() => {
    const couponDiscount = getCouponDiscount();
    return Math.max(0, cartSubtotal + cartTax - cartDiscountAmount - couponDiscount - pointsDiscount);
  }, [cartSubtotal, cartTax, cartDiscountAmount, getCouponDiscount, pointsDiscount]);

  const totalPaidAmount = React.useMemo(() => {
    return payments.reduce((acc, p) => acc + p.amount, 0);
  }, [payments]);

  const remainingBalance = React.useMemo(() => {
    return Math.max(0, cartNetTotal - totalPaidAmount);
  }, [cartNetTotal, totalPaidAmount]);

  const changeDue = React.useMemo(() => {
    if (totalPaidAmount > cartNetTotal) {
      return totalPaidAmount - cartNetTotal;
    }
    return 0;
  }, [cartNetTotal, totalPaidAmount]);

  // Cart operations
  const handleAddVariant = (prod: any, variant: any) => {
    addToCart({
      variantId: variant.id,
      productId: prod.id,
      name: `${prod.name} (${variant.name})`,
      sku: variant.sku || prod.sku,
      barcode: variant.barcode || prod.barcode,
      price: parseFloat(variant.price),
      cost: parseFloat(variant.cost),
      taxRate: parseFloat(prod.tax_rate)
    });
  };

  // Setup dynamic payment value
  React.useEffect(() => {
    setPayAmount(remainingBalance.toString());
  }, [isPayModalOpen, remainingBalance]);

  const handlePointsChange = (val: number) => {
    if (!customer) return;
    const pointVal = loyaltyRule ? parseFloat(loyaltyRule.point_value) : 1;
    const maxVal = cartSubtotal + cartTax - cartDiscountAmount - getCouponDiscount();
    const maxPoints = Math.floor(maxVal / pointVal);
    const clamped = Math.max(0, Math.min(val, customer.points, maxPoints));
    setPointsToRedeem(clamped);
  };

  const handleApplyCoupon = async () => {
    if (!couponCode) return;
    setCouponError('');
    try {
      const cartVal = cartSubtotal + cartTax - cartDiscountAmount;
      const res = await apiClient.get('/marketing/coupons/validate', {
        params: { code: couponCode, cart_value: cartVal }
      });
      if (res.data.success) {
        setAppliedCoupon(res.data.data);
        setCouponCode('');
        setToastType('success');
        setToastMsg(`Coupon '${res.data.data.coupon_code}' applied!`);
      }
    } catch (err: any) {
      setCouponError(err.response?.data?.detail || 'Invalid coupon code');
    }
  };

  const handleRemoveCoupon = () => {
    setAppliedCoupon(null);
    setToastMsg('Coupon removed.');
  };

  const handleVerifyVoucher = async () => {
    if (!voucherCode) return;
    setVoucherError('');
    setVerifiedVoucher(null);
    try {
      const res = await apiClient.get('/marketing/vouchers/validate', {
        params: { code: voucherCode }
      });
      if (res.data.success) {
        setVerifiedVoucher(res.data.data);
        const maxCharge = Math.min(parseFloat(res.data.data.balance), remainingBalance);
        setVoucherPaymentAmount(maxCharge.toString());
      }
    } catch (err: any) {
      setVoucherError(err.response?.data?.detail || 'Invalid voucher code');
    }
  };

  const handleAddPaymentItem = () => {
    const amt = parseFloat(payAmount);
    
    if (payMethod === 'card') {
      if (isNaN(amt) || amt <= 0) return;
      setCardTerminalAmount(amt);
      setCardTerminalMsg('READY - PLEASE TAP OR SWIPE CARD');
      setIsCardProcessing(false);
      setIsCardTerminalOpen(true);
    } else if (payMethod === 'voucher') {
      if (!verifiedVoucher) {
        setToastType('error');
        setToastMsg('Please verify the gift voucher code first.');
        return;
      }
      const vAmt = parseFloat(voucherPaymentAmount);
      if (isNaN(vAmt) || vAmt <= 0) return;
      if (vAmt > parseFloat(verifiedVoucher.balance)) {
        setToastType('error');
        setToastMsg('Charging amount cannot exceed voucher active balance.');
        return;
      }
      addPayment({
        amount: vAmt,
        payment_method: 'voucher',
        transaction_reference: verifiedVoucher.code
      });
      setVoucherCode('');
      setVerifiedVoucher(null);
      setVoucherPaymentAmount('0');
    } else {
      if (isNaN(amt) || amt <= 0) return;
      addPayment({
        amount: amt,
        payment_method: payMethod,
        transaction_reference: payRef
      });
      setPayRef('');
    }
  };

  const handleSimulateCardSuccess = () => {
    setIsCardProcessing(true);
    setCardTerminalMsg('CONNECTING TO BANK SERVER...');
    
    setTimeout(() => {
      setCardTerminalMsg('AUTHORIZING TRANSACTION...');
      
      setTimeout(() => {
        const authCode = 'AUTH-' + Math.floor(Math.random() * 900000 + 100000);
        setCardTerminalMsg(`APPROVED! REF: ${authCode}`);
        
        setTimeout(() => {
          addPayment({
            amount: cardTerminalAmount,
            payment_method: 'card',
            transaction_reference: authCode
          });
          setIsCardTerminalOpen(false);
        }, 800);
        
      }, 1200);
      
    }, 1200);
  };

  // Complete Sale Checkout
  const handleCheckout = async () => {
    if (cart.length === 0) return;
    setIsLoading(true);
    try {
      const payload = {
        company_id: activeCompany.id,
        branch_id: activeBranch.id,
        customer_id: customer ? customer.id : null,
        sub_total: cartSubtotal,
        tax_amount: cartTax,
        discount_amount: cartDiscountAmount + getCouponDiscount(),
        loyalty_points_redeemed: pointsToRedeem,
        loyalty_discount: pointsDiscount,
        net_amount: cartNetTotal,
        amount_paid: totalPaidAmount,
        change_returned: changeDue,
        notes: "Checkout from POS Terminal screen",
        shift_id: shift.id,
        items: cart.map(c => ({
          product_variant_id: c.variantId,
          quantity: c.quantity,
          unit_price: c.price,
          discount_amount: c.discount,
          tax_amount: c.price * c.quantity * (c.taxRate / 100)
        })),
        payments: payments.map(p => ({
          amount: p.amount,
          payment_method: p.payment_method,
          transaction_reference: p.transaction_reference
        }))
      };

      const res = await apiClient.post('/sales/checkout', payload);
      if (res.data.success) {
        const completedSale = res.data.data;
        setReceiptSale(completedSale);
        if (customer) {
          setDispatchEmail(customer.email || '');
          setDispatchPhone(customer.phone || '');
        } else {
          setDispatchEmail('');
          setDispatchPhone('');
        }
        clearCart();
        clearPayments();
        setPointsToRedeem(0);
        setAppliedCoupon(null);
        setVoucherCode('');
        setVerifiedVoucher(null);
        setVoucherPaymentAmount('0');
        setIsPayModalOpen(false);
        setToastType('success');
        setToastMsg('Sale completed successfully!');
      }
    } catch (err: any) {
      setToastType('error');
      setToastMsg(err.response?.data?.error || 'Failed to complete transaction.');
    } finally {
      setIsLoading(false);
    }
  };

  // Hold transaction
  const handleHoldInvoice = async () => {
    if (cart.length === 0) return;
    const ref = holdRefName || `Ref-${Date.now().toString().slice(-4)}`;
    try {
      const payload = {
        company_id: activeCompany.id,
        branch_id: activeBranch.id,
        customer_id: customer ? customer.id : null,
        sub_total: cartSubtotal,
        tax_amount: cartTax,
        discount_amount: cartDiscountAmount,
        net_amount: cartNetTotal,
        amount_paid: 0,
        notes: "Held Bill",
        hold_reference: ref,
        shift_id: shift.id,
        items: cart.map(c => ({
          product_variant_id: c.variantId,
          quantity: c.quantity,
          unit_price: c.price,
          discount_amount: c.discount,
          tax_amount: c.price * c.quantity * (c.taxRate / 100)
        })),
        payments: []
      };

      const res = await apiClient.post('/sales/checkout', payload);
      if (res.data.success) {
        clearCart();
        setHoldRefName('');
        setToastType('success');
        setToastMsg(`Bill held with reference: ${ref}`);
      }
    } catch (err) {
      setToastType('error');
      setToastMsg('Failed to park bill.');
    }
  };

  // Recall held invoices list
  const handleOpenRecallList = async () => {
    try {
      const res = await apiClient.get('/sales/held');
      if (res.data.success) {
        setHeldInvoices(res.data.data);
        setIsRecallModalOpen(true);
      }
    } catch (err) {
      setToastMsg('Failed to fetch held invoices.');
    }
  };

  // Recall single invoice
  const handleRecallSingle = async (sale: any) => {
    clearCart();
    
    // Set customer
    if (sale.customer_id) {
      const custObj = customers.find(c => c.id === sale.customer_id);
      if (custObj) setCustomer(custObj);
    }

    // Set discount
    setDiscount(parseFloat(sale.discount_amount), 'flat');

    // Add items
    sale.items.forEach((item: any) => {
      const prodVar = products.flatMap(p => p.variants).find(v => v.id === item.product_variant_id);
      const prod = products.find(p => p.variants.some((v: any) => v.id === item.product_variant_id));
      if (prodVar && prod) {
        for (let i = 0; i < item.quantity; i++) {
          addToCart({
            variantId: prodVar.id,
            productId: prod.id,
            name: `${prod.name} (${prodVar.name})`,
            sku: prodVar.sku || prod.sku,
            barcode: prodVar.barcode || prod.barcode,
            price: parseFloat(item.unit_price),
            cost: parseFloat(prodVar.cost),
            taxRate: parseFloat(prod.tax_rate)
          });
        }
      }
    });

    // Cancel / Delete the held sale from backend
    await apiClient.put(`/sales/${sale.id}/cancel`, { cancel_reason: "Recalled to cart" });

    setIsRecallModalOpen(false);
    setToastMsg(`Recalled invoice ${sale.invoice_number}`);
  };

  const handleOpenHistoryList = async () => {
    try {
      setIsLoading(true);
      const res = await apiClient.get('/sales', {
        params: { branch_id: activeBranch?.id }
      });
      if (res.data.success) {
        // Filter completed and cancelled sales and sort recent first (highest ID)
        const completedSales = (res.data.data || [])
          .filter((sale: any) => sale.sale_status === 'completed' || sale.sale_status === 'cancelled')
          .sort((a: any, b: any) => b.id - a.id);
        setPastSales(completedSales);
        setIsHistoryModalOpen(true);
      }
    } catch (err) {
      setToastType('error');
      setToastMsg('Failed to fetch sales history.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleReprintReceipt = (sale: any) => {
    setReceiptSale(sale);
    if (sale.customer_id) {
      const cust = customers.find((c: any) => c.id === sale.customer_id);
      if (cust) {
        setDispatchEmail(cust.email || '');
        setDispatchPhone(cust.phone || '');
      } else {
        setDispatchEmail('');
        setDispatchPhone('');
      }
    } else {
      setDispatchEmail('');
      setDispatchPhone('');
    }
    setIsHistoryModalOpen(false);
  };

  const handleOpenCancelModal = (sale: any) => {
    setSelectedSaleToCancel(sale);
    setManagerEmail('');
    setManagerPassword('');
    setCancelReason('');
    setAuthMethod('nfc');
    setIsNfcScanning(false);
    setNfcAuthenticatedManager(null);
    setIsCancelModalOpen(true);
  };

  const handleSimulateNfcTap = async () => {
    if (isNfcScanning || nfcAuthenticatedManager) return;
    if (!cancelReason) {
      setToastType('error');
      setToastMsg('Please enter a cancellation reason first.');
      return;
    }

    setIsNfcScanning(true);
    
    // Simulate RFID scanning animation delay
    setTimeout(async () => {
      try {
        // Authenticate Manager using pre-seeded company admin credentials
        const params = new URLSearchParams();
        params.append('username', 'admin@smartpos.com');
        params.append('password', 'admin123');

        const API_BASE = 'http://localhost:8000/api/v1';
        const loginRes = await axios.post(`${API_BASE}/auth/login`, params, {
          headers: {
            'Content-Type': 'application/x-www-form-urlencoded'
          }
        });

        if (loginRes.data.success && loginRes.data.data?.access_token) {
          const managerToken = loginRes.data.data.access_token;
          
          // Verify role
          const meRes = await axios.get(`${API_BASE}/auth/me`, {
            headers: {
              Authorization: `Bearer ${managerToken}`
            }
          });
          
          if (meRes.data.success) {
            setNfcAuthenticatedManager(meRes.data.data.name || 'Administrator');
            
            // Auto trigger cancellation with manager token
            const cancelRes = await axios.put(`${API_BASE}/sales/${selectedSaleToCancel.id}/cancel`, 
              { cancel_reason: cancelReason || 'Manager override via NFC card tap' }, 
              {
                headers: {
                  Authorization: `Bearer ${managerToken}`
                }
              }
            );

            if (cancelRes.data.success) {
              setToastType('success');
              setToastMsg(`Invoice ${selectedSaleToCancel.invoice_number} cancelled & restocked via Manager NFC card.`);
              setIsCancelModalOpen(false);
              
              // Refresh sales history list
              const salesRes = await apiClient.get('/sales', {
                params: { branch_id: activeBranch?.id }
              });
              if (salesRes.data.success) {
                const completedSales = (salesRes.data.data || [])
                  .filter((sale: any) => sale.sale_status === 'completed' || sale.sale_status === 'cancelled')
                  .sort((a: any, b: any) => b.id - a.id);
                setPastSales(completedSales);
              }
            }
          }
        }
      } catch (err: any) {
        setToastType('error');
        setToastMsg(err.response?.data?.detail || err.response?.data?.error || err.message || 'NFC Badge Authorization Failed.');
      } finally {
        setIsNfcScanning(false);
      }
    }, 1200);
  };

  const handleCancelSubmit = async () => {
    if (!selectedSaleToCancel) return;
    if (!cancelReason) {
      setToastType('error');
      setToastMsg('Please enter a cancellation reason.');
      return;
    }

    setIsLoading(true);
    try {
      let authToken = localStorage.getItem('access_token');

      // If the active user is a cashier, they must authenticate a manager override
      if (!isCurrentUserAdminOrManager) {
        if (!managerEmail || !managerPassword) {
          setToastType('error');
          setToastMsg('Manager credentials are required to approve refunds/cancellations.');
          setIsLoading(false);
          return;
        }

        // Authenticate Manager credentials
        const params = new URLSearchParams();
        params.append('username', managerEmail);
        params.append('password', managerPassword);

        const API_BASE = 'http://localhost:8000/api/v1';
        const loginRes = await axios.post(`${API_BASE}/auth/login`, params, {
          headers: {
            'Content-Type': 'application/x-www-form-urlencoded'
          }
        });

        if (!loginRes.data.success || !loginRes.data.data?.access_token) {
          throw new Error('Incorrect manager credentials.');
        }

        const managerToken = loginRes.data.data.access_token;

        // Verify manager roles
        const meRes = await axios.get(`${API_BASE}/auth/me`, {
          headers: {
            Authorization: `Bearer ${managerToken}`
          }
        });

        const mgrUser = meRes.data.data;
        const hasManagerPrivileges = mgrUser?.is_superadmin || 
          (mgrUser?.roles && mgrUser.roles.some((r: any) => ['Company Admin', 'Branch Manager'].includes(r.name)));

        if (!hasManagerPrivileges) {
          throw new Error('This account does not have Manager or Administrator privileges.');
        }

        authToken = managerToken;
      }

      // Execute Cancellation API
      const API_BASE = 'http://localhost:8000/api/v1';
      const cancelRes = await axios.put(`${API_BASE}/sales/${selectedSaleToCancel.id}/cancel`, 
        { cancel_reason: cancelReason }, 
        {
          headers: {
            Authorization: `Bearer ${authToken}`
          }
        }
      );

      if (cancelRes.data.success) {
        setToastType('success');
        setToastMsg(`Invoice ${selectedSaleToCancel.invoice_number} successfully cancelled & inventory restocked.`);
        setIsCancelModalOpen(false);
        
        // Refresh sales history list
        const salesRes = await apiClient.get('/sales', {
          params: { branch_id: activeBranch?.id }
        });
        if (salesRes.data.success) {
          const completedSales = (salesRes.data.data || [])
            .filter((sale: any) => sale.sale_status === 'completed' || sale.sale_status === 'cancelled')
            .sort((a: any, b: any) => b.id - a.id);
          setPastSales(completedSales);
        }
      }
    } catch (err: any) {
      setToastType('error');
      setToastMsg(err.response?.data?.detail || err.response?.data?.error || err.message || 'Failed to cancel transaction.');
    } finally {
      setIsLoading(false);
    }
  };

  // Check if cashier shift is closed
  if (!shift) {
    return (
      <div className="h-full flex items-center justify-center p-6">
        <Card className="max-w-md w-full p-8 text-center flex flex-col items-center gap-4">
          <div className="p-4 rounded-2xl bg-amber-500/10 text-amber-500">
            <Lock className="w-8 h-8" />
          </div>
          <h2 className="text-xl font-bold dark:text-white">POS Terminal Locked</h2>
          <p className="text-xs text-slate-400 leading-normal">
            To register customer payments, you must open a cashier shift drawer. Use the "Open Cash Shift" trigger in the topbar panel above.
          </p>
        </Card>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 h-[calc(100vh-130px)]">
      
      {/* LEFT COLUMN: Catalog / Product Search */}
      <div className="lg:col-span-7 flex flex-col gap-4 overflow-hidden h-full">
        
        {/* Filters */}
        <div className="flex gap-3">
          <div className="relative flex-grow">
            <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-3.5" />
            <input
              type="text"
              placeholder="Search products by SKU, name, or barcode..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full min-h-[44px] pl-10 pr-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500/20"
            />
          </div>
          
          <button 
            onClick={() => setSelectedCat(null)}
            className={`px-4 rounded-xl text-xs font-bold transition-all min-h-[44px] ${
              selectedCat === null 
                ? 'bg-brand-500 text-white shadow-sm shadow-brand-500/20' 
                : 'bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-850 hover:bg-slate-50'
            }`}
          >
            All
          </button>
          
          {categories.slice(0, 3).map((cat, idx) => (
            <button
              key={idx}
              onClick={() => setSelectedCat(cat.id)}
              className={`px-4 rounded-xl text-xs font-bold transition-all min-h-[44px] ${
                selectedCat === cat.id 
                  ? 'bg-brand-500 text-white shadow-sm shadow-brand-500/20' 
                  : 'bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-850 hover:bg-slate-50'
              }`}
            >
              {cat.name}
            </button>
          ))}
        </div>

        {/* Product Grid */}
        <div className="flex-grow overflow-y-auto pr-1">
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
            {filteredProducts.map((prod, pIdx) => (
              <div key={pIdx} className="bg-white dark:bg-slate-900 border border-slate-100 dark:border-slate-800/80 rounded-2xl p-4 flex flex-col justify-between hover:shadow-md transition-all text-left">
                <div className="flex flex-col gap-1">
                  {prod.image_url ? (
                    <img src={prod.image_url} alt={prod.name} className="w-full h-24 object-cover rounded-xl mb-2" />
                  ) : (
                    <div className="w-full h-24 bg-slate-50 dark:bg-slate-850 rounded-xl mb-2 flex items-center justify-center text-slate-300">
                      No Image
                    </div>
                  )}
                  <h4 className="font-bold text-slate-800 dark:text-slate-200 text-xs line-clamp-2 leading-tight">{prod.name}</h4>
                  <span className="text-[10px] text-slate-400">SKU: {prod.sku || 'N/A'}</span>
                </div>

                {/* Variants Trigger List */}
                <div className="flex flex-col gap-1.5 mt-3 pt-3 border-t border-slate-50 dark:border-slate-850">
                  {prod.variants.map((v: any, vIdx: number) => (
                    <button
                      key={vIdx}
                      onClick={() => handleAddVariant(prod, v)}
                      className="w-full flex items-center justify-between p-1.5 rounded-lg bg-slate-50 hover:bg-brand-500/10 dark:bg-slate-850 dark:hover:bg-brand-500/10 text-[11px] font-bold text-slate-600 dark:text-slate-300 transition-colors"
                    >
                      <span className="truncate max-w-[80px]">{v.name}</span>
                      <span className="text-brand-500">Rs.{parseFloat(v.price).toLocaleString()}</span>
                    </button>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>

      </div>

      {/* RIGHT COLUMN: Active Cart Panel */}
      <div className="lg:col-span-5 flex flex-col justify-between bg-white dark:bg-slate-900 border border-slate-100 dark:border-slate-800/80 rounded-3xl overflow-hidden shadow-sm h-full">
        
        {/* Cart Header */}
        <div className="px-6 py-5 border-b border-slate-100 dark:border-slate-800/80 flex items-center justify-between">
          <div className="text-left">
            <h3 className="font-bold text-slate-800 dark:text-slate-100">Checkout Basket</h3>
            <p className="text-[10px] text-slate-400 uppercase tracking-widest font-semibold">{cart.length} unique items</p>
          </div>
          <button onClick={clearCart} className="p-2 rounded-xl bg-red-500/10 text-red-500 hover:bg-red-500/20 transition-colors">
            <Trash2 className="w-4 h-4" />
          </button>
        </div>

        {/* Cart Item Rows */}
        <div className="flex-grow overflow-y-auto p-6 flex flex-col gap-4">
          {cart.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center text-slate-400 dark:text-slate-500 gap-2">
              <ShoppingCart className="w-8 h-8 opacity-40" />
              <span className="text-xs">Add products from the left to start billing</span>
            </div>
          ) : (
            cart.map((item, idx) => (
              <div key={idx} className="flex items-center justify-between text-xs pb-3 border-b border-slate-50 dark:border-slate-850/60 gap-3 text-left">
                <div className="flex flex-col gap-0.5 min-w-0">
                  <span className="font-bold text-slate-700 dark:text-slate-200 truncate">{item.name}</span>
                  <span className="text-[10px] text-brand-500 font-bold">Rs. {item.price.toLocaleString()}</span>
                </div>
                
                {/* Quantity adjustments */}
                <div className="flex items-center gap-2 shrink-0">
                  <button 
                    onClick={() => updateCartQuantity(item.variantId, item.quantity - 1)}
                    className="w-7 h-7 rounded-lg bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 flex items-center justify-center font-bold"
                  >
                    -
                  </button>
                  <span className="w-6 text-center font-bold">{item.quantity}</span>
                  <button 
                    onClick={() => updateCartQuantity(item.variantId, item.quantity + 1)}
                    className="w-7 h-7 rounded-lg bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 flex items-center justify-center font-bold"
                  >
                    +
                  </button>
                </div>
              </div>
            ))
          )}
        </div>

        {/* Customer Select box & Total Recap */}
        <div className="p-6 border-t border-slate-100 dark:border-slate-800/80 bg-slate-50/50 dark:bg-slate-900/50 flex flex-col gap-4">
          
          {/* Customer CRM Selector */}
          <div className="relative">
            {customer ? (
              <div className="flex items-center justify-between p-3.5 rounded-2xl bg-brand-500/10 border border-brand-500/20 text-brand-700 dark:text-brand-400 text-xs">
                <div className="flex flex-col gap-0.5 text-left">
                  <span className="font-bold">{customer.name}</span>
                  <span className="text-[10px] text-slate-500 dark:text-slate-400">
                    Phone: {customer.phone || 'N/A'} | Loyalty Points: {customer.points || 0}
                  </span>
                </div>
                <button 
                  onClick={() => setCustomer(null)}
                  className="text-red-500 hover:text-red-600 font-bold hover:underline"
                >
                  Remove
                </button>
              </div>
            ) : (
              <div className="flex gap-2">
                <div className="relative flex-grow">
                  <input
                    type="text"
                    placeholder="Search customer by mobile / name..."
                    value={custQuery}
                    onFocus={() => setShowCustDropdown(true)}
                    onChange={(e) => {
                      setCustQuery(e.target.value);
                      setShowCustDropdown(true);
                    }}
                    className="w-full min-h-[44px] px-3.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 text-xs focus:outline-none focus:ring-2 focus:ring-brand-500/20 text-slate-800 dark:text-white"
                  />
                  
                  {/* Matches Dropdown list */}
                  {showCustDropdown && custQuery && (
                    <div className="absolute left-0 right-0 bottom-full mb-2 z-10 max-h-48 overflow-y-auto bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl shadow-lg flex flex-col">
                      {matchedCustomers.length === 0 ? (
                        <span className="text-[11px] text-slate-400 py-3 text-center">No customers found.</span>
                      ) : (
                        matchedCustomers.map((c, idx) => (
                          <button
                            key={idx}
                            type="button"
                            onClick={() => {
                              setCustomer(c);
                              setCustQuery('');
                              setShowCustDropdown(false);
                            }}
                            className="w-full text-left px-4 py-2.5 hover:bg-slate-50 dark:hover:bg-slate-800 text-xs flex justify-between border-b border-slate-50 dark:border-slate-850 last:border-b-0"
                          >
                            <span className="font-bold text-slate-700 dark:text-slate-200">{c.name}</span>
                            <span className="text-slate-400">{c.phone || 'No Mobile'}</span>
                          </button>
                        ))
                      )}
                    </div>
                  )}
                </div>
                
                <Button 
                  onClick={() => setIsQuickCustOpen(true)}
                  variant="secondary"
                  className="min-h-0 h-[44px] px-3"
                  title="Quick add customer"
                >
                  <UserPlus className="w-4 h-4" />
                </Button>
              </div>
            )}
          </div>

          {/* Loyalty points redemption panel */}
          {customer && (
            <div className="p-3 bg-slate-50 dark:bg-slate-900 border border-slate-100 dark:border-slate-850 rounded-2xl text-xs text-left flex flex-col gap-2">
              <div className="flex justify-between items-center">
                <span className="font-bold text-slate-500">Redeem Loyalty Points</span>
                <span className="text-[10px] bg-brand-500/10 text-brand-500 px-2 py-0.5 rounded-md font-bold">
                  Rule: 1 Pt = Rs. {loyaltyRule ? parseFloat(loyaltyRule.point_value) : 1}
                </span>
              </div>
              <div className="flex items-center gap-3">
                <input
                  type="number"
                  placeholder={`Max ${customer.points}`}
                  value={pointsToRedeem || ''}
                  onChange={(e) => handlePointsChange(parseInt(e.target.value) || 0)}
                  className="w-full min-h-[38px] px-3 rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 text-xs text-brand-500 font-bold focus:outline-none text-right"
                />
                <Button 
                  onClick={() => handlePointsChange(customer.points)}
                  variant="secondary"
                  className="min-h-0 py-1.5 text-[10px] shrink-0"
                >
                  Max
                </Button>
              </div>
              {pointsToRedeem > 0 && (
                <p className="text-[10px] text-emerald-500 font-bold">
                  ✔ Applied Rs. {pointsDiscount.toLocaleString()} discount from points.
                </p>
              )}
            </div>
          )}

          {/* Subtotal Recaps */}
          <div className="flex flex-col gap-2 text-xs border-b border-slate-200 dark:border-slate-800/80 pb-3">
            <div className="flex justify-between text-slate-500">
              <span>Subtotal</span>
              <span className="font-semibold text-slate-700 dark:text-slate-300">Rs. {cartSubtotal.toLocaleString()}</span>
            </div>
            <div className="flex justify-between text-slate-500">
              <span>Tax (VAT)</span>
              <span className="font-semibold text-slate-700 dark:text-slate-300">Rs. {cartTax.toLocaleString()}</span>
            </div>
            
            {/* Flat Discount Input wrapper */}
            <div className="flex justify-between items-center gap-4 text-slate-500">
              <span className="flex items-center gap-1"><Tag className="w-3.5 h-3.5" /> Discount</span>
              <div className="flex items-center gap-1.5">
                <input
                  type="number"
                  placeholder="0"
                  value={discount || ''}
                  onChange={(e) => setDiscount(parseFloat(e.target.value) || 0, 'flat')}
                  className="w-16 text-right border-b border-slate-300 dark:border-slate-800 focus:outline-none text-xs bg-transparent p-0.5 text-brand-500 font-bold"
                />
                <span className="font-semibold text-brand-500">LKR</span>
              </div>
            </div>

            {/* Promo Code Coupon Input row */}
            <div className="flex flex-col gap-1 text-slate-500 mt-1 pt-1 border-t border-dashed border-slate-100 dark:border-slate-850">
              {appliedCoupon ? (
                <div className="flex justify-between items-center text-xs">
                  <span className="flex items-center gap-1 text-emerald-500 font-semibold">
                    <Sparkles className="w-3.5 h-3.5 animate-pulse" /> Coupon: {appliedCoupon.coupon_code}
                  </span>
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-emerald-500">- Rs. {getCouponDiscount().toLocaleString()}</span>
                    <button 
                      type="button" 
                      onClick={handleRemoveCoupon} 
                      className="text-red-500 hover:text-red-650 font-bold hover:underline"
                    >
                      Delete
                    </button>
                  </div>
                </div>
              ) : (
                <div className="flex items-center gap-2">
                  <span className="flex items-center gap-1 text-slate-500 shrink-0"><Tag className="w-3.5 h-3.5" /> Coupon</span>
                  <div className="flex-grow flex gap-1.5 items-center">
                    <input
                      type="text"
                      placeholder="Enter promo code..."
                      value={couponCode}
                      onChange={(e) => setCouponCode(e.target.value.toUpperCase())}
                      className="flex-grow border-b border-slate-200 dark:border-slate-800 focus:outline-none text-[11px] bg-transparent p-0.5"
                    />
                    <Button onClick={handleApplyCoupon} variant="ghost" className="min-h-0 py-1 px-2.5 text-[10px] font-semibold text-brand-500">
                      Apply
                    </Button>
                  </div>
                </div>
              )}
              {couponError && <p className="text-[10px] text-red-500 font-semibold">{couponError}</p>}
            </div>

            {/* Displays points and coupon discount rows in the breakdown list if they are active */}
            {appliedCoupon && (
              <div className="flex justify-between text-emerald-500">
                <span>Coupon Discount ({appliedCoupon.coupon_code})</span>
                <span>- Rs. {getCouponDiscount().toLocaleString()}</span>
              </div>
            )}
            {pointsToRedeem > 0 && (
              <div className="flex justify-between text-emerald-500 font-medium">
                <span>Points Discount</span>
                <span>- Rs. {pointsDiscount.toLocaleString()}</span>
              </div>
            )}
          </div>

          {/* Net Total and Checkout Actions */}
          <div className="flex items-center justify-between">
            <div className="text-left">
              <span className="text-[10px] text-slate-400 uppercase tracking-widest font-bold">Total Payable</span>
              <h2 className="text-2xl font-extrabold text-slate-800 dark:text-white leading-tight">
                Rs. {cartNetTotal.toLocaleString()}
              </h2>
            </div>
            
            <div className="flex gap-2">
              <button 
                onClick={handleOpenHistoryList}
                className="p-3.5 rounded-xl bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-600 dark:text-slate-300 transition-colors"
                title="Sales History"
              >
                <History className="w-5 h-5" />
              </button>

              <button 
                onClick={handleOpenRecallList}
                className="p-3.5 rounded-xl bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-600 dark:text-slate-300 transition-colors"
                title="Recall held bills"
              >
                <FolderOpen className="w-5 h-5" />
              </button>
              
              <button 
                onClick={() => setIsPayModalOpen(true)}
                disabled={cart.length === 0}
                className="px-6 py-3 rounded-xl bg-brand-500 hover:bg-brand-600 text-white font-bold text-sm shadow-lg shadow-brand-500/20 active:scale-98 transition-all disabled:opacity-50 disabled:pointer-events-none"
              >
                Complete Sale
              </button>
            </div>
          </div>

        </div>

      </div>

      {/* CHECKOUT SPLIT PAYMENT MODAL */}
      <Modal isOpen={isPayModalOpen} onClose={() => setIsPayModalOpen(false)} title="Checkout split payments">
        <div className="flex flex-col gap-4 text-left">
          
          <div className="p-4 rounded-2xl bg-slate-50 dark:bg-slate-900 border border-slate-100 dark:border-slate-850 flex justify-between items-center text-sm font-bold">
            <span className="text-slate-400">Remaining Balance:</span>
            <span className="text-lg text-brand-500">Rs. {remainingBalance.toLocaleString()}</span>
          </div>

          <div className="grid grid-cols-3 gap-3 mt-1">
            <button 
              onClick={() => setPayMethod('cash')}
              className={`p-4 rounded-2xl border flex flex-col items-center gap-2 transition-all ${
                payMethod === 'cash' 
                  ? 'border-brand-500 bg-brand-500/5 text-brand-500' 
                  : 'border-slate-100 dark:border-slate-850 hover:bg-slate-50'
              }`}
            >
              <Banknote className="w-6 h-6" />
              <span className="text-xs font-bold">Cash</span>
            </button>
            <button 
              onClick={() => setPayMethod('card')}
              className={`p-4 rounded-2xl border flex flex-col items-center gap-2 transition-all ${
                payMethod === 'card' 
                  ? 'border-brand-500 bg-brand-500/5 text-brand-500' 
                  : 'border-slate-100 dark:border-slate-850 hover:bg-slate-50'
              }`}
            >
              <CreditCard className="w-6 h-6" />
              <span className="text-xs font-bold">Card Payment</span>
            </button>
            <button 
              onClick={() => setPayMethod('voucher')}
              className={`p-4 rounded-2xl border flex flex-col items-center gap-2 transition-all ${
                payMethod === 'voucher' 
                  ? 'border-brand-500 bg-brand-500/5 text-brand-500' 
                  : 'border-slate-100 dark:border-slate-850 hover:bg-slate-50'
              }`}
            >
              <Gift className="w-6 h-6" />
              <span className="text-xs font-bold">Voucher</span>
            </button>
          </div>

          {payMethod === 'voucher' && (
            <div className="flex flex-col gap-2.5 p-4 bg-slate-50 dark:bg-slate-900 border border-slate-100 dark:border-slate-850 rounded-2xl mt-1 text-xs">
              <div className="flex gap-2 items-end">
                <Input
                  label="Gift Voucher Code"
                  placeholder="e.g. GIFT500"
                  value={voucherCode}
                  onChange={(e) => setVoucherCode(e.target.value.toUpperCase())}
                />
                <Button onClick={handleVerifyVoucher} variant="secondary" className="min-h-0 py-2.5">Verify</Button>
              </div>
              {voucherError && <p className="text-red-500 font-semibold text-[11px]">{voucherError}</p>}
              {verifiedVoucher && (
                <div className="flex flex-col gap-1.5 mt-1 border-t border-slate-100 dark:border-slate-800/80 pt-2.5 text-left">
                  <p className="text-slate-500">Voucher Name: <strong className="text-slate-700 dark:text-white">{verifiedVoucher.name}</strong></p>
                  <p className="text-slate-500">Available Balance: <strong className="text-emerald-500 font-bold">Rs. {verifiedVoucher.balance.toLocaleString()}</strong></p>
                  
                  <div className="flex gap-2 items-end mt-1">
                    <Input
                      label="Amount to Charge (LKR)"
                      type="number"
                      value={voucherPaymentAmount}
                      onChange={(e) => setVoucherPaymentAmount(e.target.value)}
                    />
                  </div>
                </div>
              )}
            </div>
          )}

          <div className="flex gap-3 mt-2 items-end">
            <Input
              label="Paying Amount (LKR)"
              type="number"
              value={payMethod === 'voucher' ? voucherPaymentAmount : payAmount}
              onChange={(e) => payMethod === 'voucher' ? setVoucherPaymentAmount(e.target.value) : setPayAmount(e.target.value)}
            />
            <Button onClick={handleAddPaymentItem} variant="secondary" className="min-h-0 py-3">Add Payment</Button>
          </div>

          {/* Active payments list */}
          {payments.length > 0 && (
            <div className="flex flex-col gap-2 mt-2">
              <span className="text-xs font-semibold uppercase text-slate-400">Added Split Payments</span>
              {payments.map((p, i) => (
                <div key={i} className="flex justify-between items-center p-2 rounded-xl bg-slate-50 dark:bg-slate-900 border border-slate-100 dark:border-slate-800 text-xs">
                  <span className="font-semibold capitalize text-slate-700 dark:text-slate-300">{p.payment_method}</span>
                  <div className="flex items-center gap-2 font-bold">
                    <span>Rs. {p.amount.toLocaleString()}</span>
                    <button onClick={() => removePayment(i)} className="text-red-500 hover:text-red-600">Delete</button>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Footer controls: Hold, Pay */}
          <div className="flex justify-between items-center mt-6 pt-5 border-t border-slate-100 dark:border-slate-800/80">
            <div className="flex gap-2">
              <input 
                type="text" 
                placeholder="Hold ref name..." 
                value={holdRefName} 
                onChange={(e) => setHoldRefName(e.target.value)}
                className="w-32 text-xs px-3 py-2 rounded-xl border border-slate-200 dark:border-slate-800 focus:outline-none bg-transparent"
              />
              <Button onClick={handleHoldInvoice} variant="secondary" className="px-3 py-2 min-h-0">Hold Bill</Button>
            </div>
            
            <Button 
              onClick={handleCheckout} 
              isLoading={isLoading} 
              disabled={remainingBalance > 0 || cart.length === 0}
              className="px-6"
            >
              Post Payment
            </Button>
          </div>

        </div>
      </Modal>

      {/* RECALL MODAL */}
      <Modal isOpen={isRecallModalOpen} onClose={() => setIsRecallModalOpen(false)} title="Recall Parked Invoices">
        <div className="flex flex-col gap-4 text-left">
          <p className="text-xs text-slate-400">Select a held transaction to load it back into the checkout register.</p>
          
          <div className="flex flex-col gap-3 max-h-96 overflow-y-auto">
            {heldInvoices.length === 0 ? (
              <span className="text-xs text-center text-slate-400 py-6">No held bills found.</span>
            ) : (
              heldInvoices.map((sale, i) => (
                <div key={i} className="flex justify-between items-center p-3 rounded-xl border border-slate-100 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-900/40 text-xs">
                  <div className="flex flex-col gap-0.5">
                    <span className="font-bold text-slate-700 dark:text-slate-200">Ref: {sale.hold_reference}</span>
                    <span className="text-[10px] text-slate-400">{sale.invoice_number}</span>
                  </div>
                  <div className="flex items-center gap-3 font-bold">
                    <span>Rs. {parseFloat(sale.net_amount).toLocaleString()}</span>
                    <Button onClick={() => handleRecallSingle(sale)} className="min-h-0 py-1.5 px-3 text-xs rounded-lg">Recall</Button>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </Modal>

      {/* SALES HISTORY MODAL */}
      <Modal isOpen={isHistoryModalOpen} onClose={() => setIsHistoryModalOpen(false)} title="Recent Sales History">
        <div className="flex flex-col gap-4 text-left min-w-[320px] md:min-w-[500px]">
          <p className="text-xs text-slate-400">View recent completed transactions for {activeBranch?.name || 'this branch'} and reprint receipts.</p>
          
          <div className="flex flex-col gap-3 max-h-96 overflow-y-auto pr-1">
            {pastSales.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-8 text-slate-400 gap-2">
                <History className="w-8 h-8 opacity-30" />
                <span className="text-xs">No completed sales history found.</span>
              </div>
            ) : (
              pastSales.map((sale, i) => {
                const saleDate = new Date(sale.sale_date).toLocaleString();
                const custName = sale.customer_id 
                  ? (customers.find(c => c.id === sale.customer_id)?.name || 'Linked Customer') 
                  : 'Walk-in Customer';

                return (
                  <div key={i} className="flex justify-between items-center p-3 rounded-xl border border-slate-100 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-900/40 text-xs hover:border-brand-500/30 transition-all">
                    <div className="flex flex-col gap-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-slate-700 dark:text-slate-200 truncate">{sale.invoice_number}</span>
                        <span className="px-1.5 py-0.5 rounded text-[9px] font-bold bg-green-500/10 text-green-500 capitalize">{sale.payment_status}</span>
                      </div>
                      <div className="flex flex-col text-[10px] text-slate-400 gap-0.5">
                        <span>Date: {saleDate}</span>
                        <span className="truncate">Customer: {custName}</span>
                      </div>
                    </div>
                    <div className="flex items-center gap-2 font-bold shrink-0 ml-2">
                      <span className="text-slate-800 dark:text-white mr-1">Rs. {parseFloat(sale.net_amount).toLocaleString()}</span>
                      <Button 
                        onClick={() => handleReprintReceipt(sale)} 
                        variant="secondary" 
                        className="min-h-0 py-1.5 px-3 text-xs rounded-lg flex items-center gap-1 hover:bg-brand-500 hover:text-white transition-all"
                        icon={<Printer className="w-3.5 h-3.5" />}
                      >
                        Reprint
                      </Button>
                      {sale.sale_status !== 'cancelled' ? (
                        <button 
                          onClick={() => {
                            setIsHistoryModalOpen(false);
                            handleOpenCancelModal(sale);
                          }}
                          className="min-h-0 py-1.5 px-3 text-[11px] font-bold rounded-lg border border-red-500/30 text-red-500 hover:bg-red-500 hover:text-white transition-all"
                        >
                          Cancel
                        </button>
                      ) : (
                        <span className="px-2 py-1.5 rounded text-[10px] font-bold bg-red-500/10 text-red-500">
                          Cancelled
                        </span>
                      )}
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>
      </Modal>

      {/* CANCEL & REFUND OVERRIDE MODAL */}
      <Modal isOpen={isCancelModalOpen} onClose={() => setIsCancelModalOpen(false)} title="Cancel & Refund Transaction">
        <div className="flex flex-col gap-4 text-left min-w-[320px] md:min-w-[450px]">
          {selectedSaleToCancel && (
            <div className="p-4 rounded-2xl bg-red-500/5 border border-red-500/10 text-xs flex flex-col gap-1.5">
              <div className="flex justify-between items-center font-bold">
                <span className="text-red-700 dark:text-red-400">Void Invoice:</span>
                <span className="text-slate-700 dark:text-slate-355">{selectedSaleToCancel.invoice_number}</span>
              </div>
              <div className="flex justify-between items-center text-slate-500 font-semibold">
                <span>Net Total:</span>
                <span>Rs. {parseFloat(selectedSaleToCancel.net_amount).toLocaleString()}</span>
              </div>
              <div className="flex justify-between items-center text-slate-500 font-semibold">
                <span>Payment Method:</span>
                <span className="capitalize">{selectedSaleToCancel.payments?.[0]?.payment_method || 'Cash'}</span>
              </div>
            </div>
          )}

          {!isCurrentUserAdminOrManager ? (
            <div className="flex flex-col gap-3">
              {authMethod === 'nfc' ? (
                <div className="flex flex-col items-center justify-center p-6 bg-slate-50 dark:bg-slate-900 border border-dashed border-slate-200 dark:border-slate-800 rounded-2xl gap-4 text-center">
                  <div className="relative flex items-center justify-center">
                    <div className={`w-16 h-16 rounded-full bg-brand-500/10 flex items-center justify-center text-brand-500 ${isNfcScanning ? 'animate-pulse' : ''}`}>
                      <CreditCard className="w-8 h-8" />
                    </div>
                    {isNfcScanning && (
                      <div className="absolute -inset-2 rounded-full border-2 border-brand-500 animate-ping opacity-25" />
                    )}
                  </div>
                  
                  <div className="flex flex-col gap-1">
                    <span className="text-xs font-bold text-slate-700 dark:text-slate-200">
                      {isNfcScanning 
                        ? 'COMMUNICATING WITH STAFF CARD...' 
                        : nfcAuthenticatedManager 
                          ? `AUTHENTICATED: ${nfcAuthenticatedManager}` 
                          : 'AWAITING MANAGER NFC BADGE TAP...'}
                    </span>
                    <span className="text-[10px] text-slate-400">
                      Tap physical manager NFC staff card to authorize this cancellation.
                    </span>
                  </div>

                  {!nfcAuthenticatedManager ? (
                    <Button 
                      onClick={handleSimulateNfcTap}
                      disabled={isNfcScanning}
                      className="min-h-0 py-2 text-xs rounded-xl bg-brand-500 text-white"
                    >
                      {isNfcScanning ? 'Reading Badge...' : 'Simulate Manager NFC Card Tap'}
                    </Button>
                  ) : (
                    <div className="text-[11px] font-bold text-green-500 bg-green-500/10 px-3 py-1.5 rounded-lg">
                      ✔ Authorized Override Approved
                    </div>
                  )}

                  <button 
                    type="button"
                    onClick={() => setAuthMethod('password')} 
                    className="text-[10px] text-brand-500 font-bold hover:underline mt-1"
                  >
                    Or authorize with Manager Email & Password
                  </button>
                </div>
              ) : (
                <div className="flex flex-col gap-3">
                  <div className="p-3.5 rounded-xl bg-amber-500/10 border border-amber-500/20 text-amber-600 text-[11px] leading-normal font-medium flex justify-between items-start gap-2">
                    <div>
                      <strong>Manager Override Required:</strong> Cashier accounts are not authorized to cancel transactions. Please input manager credentials.
                    </div>
                    <button 
                      type="button"
                      onClick={() => setAuthMethod('nfc')}
                      className="text-brand-500 font-bold hover:underline shrink-0 text-[10px]"
                    >
                      Use NFC Tap
                    </button>
                  </div>
                  <Input
                    label="Manager Email Address"
                    type="email"
                    placeholder="manager@smartpos.com"
                    value={managerEmail}
                    onChange={(e) => setManagerEmail(e.target.value)}
                  />
                  <Input
                    label="Manager Password"
                    type="password"
                    placeholder="••••••••"
                    value={managerPassword}
                    onChange={(e) => setManagerPassword(e.target.value)}
                  />
                </div>
              )}
            </div>
          ) : (
            <div className="p-3.5 rounded-xl bg-green-500/10 border border-green-500/20 text-green-600 text-[11px] leading-normal font-medium">
              <strong>Direct Admin Access:</strong> You are logged in with administrative privileges. You can process this cancellation directly.
            </div>
          )}

          <div className="flex flex-col gap-1.5">
            <label className="text-xs font-bold text-slate-500 dark:text-slate-400">Reason for Cancellation</label>
            <textarea
              placeholder="e.g. Customer returned items / Cashier billing error"
              value={cancelReason}
              onChange={(e) => setCancelReason(e.target.value)}
              className="w-full min-h-[80px] p-3 text-xs rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 text-slate-800 dark:text-white focus:outline-none focus:ring-2 focus:ring-brand-500/20"
              rows={3}
            />
          </div>

          <div className="flex justify-end gap-3 mt-4 pt-4 border-t border-slate-100 dark:border-slate-800/80">
            <Button onClick={() => setIsCancelModalOpen(false)} variant="secondary">
              Go Back
            </Button>
            {(isCurrentUserAdminOrManager || authMethod === 'password') && (
              <Button 
                onClick={handleCancelSubmit} 
                isLoading={isLoading} 
                className="bg-red-500 hover:bg-red-600 shadow-lg shadow-red-500/20 text-white"
              >
                Confirm Cancellation
              </Button>
            )}
          </div>
        </div>
      </Modal>

      {/* EMV CARD TERMINAL SIMULATOR MODAL */}
      <Modal isOpen={isCardTerminalOpen} onClose={() => setIsCardTerminalOpen(false)} title="Integrated EMV Card Terminal">
        <div className="flex flex-col items-center justify-center p-6 text-center gap-6 min-w-[320px] md:min-w-[400px]">
          
          {/* Card Reader Physical Device Body */}
          <div className="w-full max-w-[280px] bg-slate-800 dark:bg-slate-950 p-5 rounded-3xl border border-slate-700/80 shadow-2xl flex flex-col gap-4 text-left font-sans text-slate-350">
            
            {/* LED Status Indicators */}
            <div className="flex gap-2 justify-center mb-1">
              <div className={`w-3.5 h-1.5 rounded-full ${isCardProcessing ? 'bg-amber-500 animate-pulse' : cardTerminalMsg.includes('APPROVED') ? 'bg-green-500' : 'bg-slate-600'}`} />
              <div className={`w-3.5 h-1.5 rounded-full ${isCardProcessing && !cardTerminalMsg.includes('CONNECTING') ? 'bg-amber-500 animate-pulse' : cardTerminalMsg.includes('APPROVED') ? 'bg-green-500' : 'bg-slate-600'}`} />
              <div className={`w-3.5 h-1.5 rounded-full ${cardTerminalMsg.includes('APPROVED') ? 'bg-green-500' : 'bg-slate-600'}`} />
              <div className={`w-3.5 h-1.5 rounded-full ${cardTerminalMsg.includes('APPROVED') ? 'bg-green-500' : 'bg-slate-600'}`} />
            </div>

            {/* Glowing Monospace Display Screen */}
            <div className="w-full h-32 bg-black border-2 border-slate-700 rounded-xl p-3.5 flex flex-col justify-between font-mono text-[11px] leading-tight text-emerald-400 select-none shadow-inner">
              <div className="flex justify-between border-b border-emerald-950 pb-1 text-[9px] text-emerald-600">
                <span>TERMINAL ID: SP-4938</span>
                <span>ONLINE</span>
              </div>
              <div className="flex flex-col gap-1 text-center py-1">
                <span className="text-emerald-500 uppercase tracking-wide font-bold">{cardTerminalMsg}</span>
                <span className="text-[14px] text-white font-extrabold tracking-wider mt-1">Rs. {cardTerminalAmount.toLocaleString(undefined, { minimumFractionDigits: 2 })}</span>
              </div>
              <div className="text-[9px] text-emerald-600 text-center border-t border-emerald-950 pt-1">
                INSERT, SWIPE OR TAP CARD
              </div>
            </div>

            {/* Tap Contactless Sensor Icon Area */}
            <div className="flex flex-col items-center justify-center p-3 border border-slate-700/50 rounded-2xl bg-slate-900/50 gap-2">
              <div className={`text-slate-400 ${!isCardProcessing ? 'animate-bounce text-brand-400' : ''}`}>
                <CreditCard className="w-8 h-8" />
              </div>
              <span className="text-[9px] uppercase tracking-widest text-slate-500 font-bold font-sans">NFC Contactless Field</span>
            </div>

          </div>

          {/* Checkout Controls */}
          <div className="flex flex-col gap-2.5 w-full max-w-[280px]">
            {!isCardProcessing ? (
              <Button 
                onClick={handleSimulateCardSuccess}
                className="w-full bg-emerald-600 hover:bg-emerald-700 shadow-lg shadow-emerald-500/20 text-white font-bold"
              >
                Simulate NFC Card Tap
              </Button>
            ) : (
              <div className="py-2.5 text-xs font-semibold text-slate-400 italic animate-pulse">
                Authorizing card payment...
              </div>
            )}
            <button 
              type="button"
              disabled={isCardProcessing}
              onClick={() => setIsCardTerminalOpen(false)}
              className="text-xs text-slate-500 hover:text-slate-650 font-bold hover:underline transition-all disabled:opacity-40"
            >
              Cancel Payment
            </button>
          </div>

        </div>
      </Modal>

      {/* SIMULATED THERMAL PRINT DIALOG */}
      {receiptSale && (
        <Modal isOpen={!!receiptSale} onClose={() => setReceiptSale(null)} title="Print Invoice Receipt">
          <div className="flex flex-col gap-4 text-center">
            
            {/* The Thermal Slip (80mm width design) */}
            <div className="border border-slate-200 dark:border-slate-800 bg-white text-slate-900 font-mono text-left text-xs p-6 max-w-sm mx-auto shadow-md rounded-2xl flex flex-col gap-4">
              <div className="text-center flex flex-col gap-1 border-b border-dashed border-slate-300 pb-4">
                <h3 className="font-bold text-sm tracking-tight uppercase">{activeCompany?.name || 'SMART POS CORP'}</h3>
                <p className="text-[10px] font-bold text-slate-500">{activeBranch?.name || 'Main Branch'}</p>
                {activeBranch?.address && <p className="text-[9px] text-slate-500 leading-normal">{activeBranch.address}</p>}
                {activeBranch?.phone && <p className="text-[9px] text-slate-400">Tel: {activeBranch.phone}</p>}
                {activeBranch?.email && <p className="text-[9px] text-slate-400">Email: {activeBranch.email}</p>}
              </div>

              <div className="flex flex-col gap-1 text-[10px] text-slate-600">
                <p>INVOICE : {receiptSale.invoice_number}</p>
                <p>DATE    : {new Date(receiptSale.sale_date).toLocaleString()}</p>
                <p>CASHIER : {currentUser?.name || 'Administrator'}</p>
              </div>

              {/* Items Table */}
              <div className="border-t border-b border-dashed border-slate-300 py-3 flex flex-col gap-2">
                {receiptSale.items.map((item: any, idx: number) => {
                  let name = `Variant #${item.product_variant_id}`;
                  const prodVar = products.flatMap(p => p.variants || []).find(v => v?.id === item.product_variant_id);
                  const prod = products.find(p => p.variants?.some((v: any) => v?.id === item.product_variant_id));
                  if (prodVar && prod) {
                    name = `${prod.name} - ${prodVar.name}`;
                  }
                  return (
                    <div key={idx} className="flex justify-between items-start text-[10px] gap-2">
                      <span className="truncate max-w-[160px]">{name}</span>
                      <span className="shrink-0">{item.quantity} x Rs.{parseFloat(item.unit_price).toLocaleString()}</span>
                    </div>
                  );
                })}
              </div>

              {/* Totals */}
              <div className="flex flex-col gap-1.5 text-right font-bold text-[10px] text-slate-700 border-b border-dashed border-slate-300 pb-3">
                <div className="flex justify-between">
                  <span>SUBTOTAL</span>
                  <span>Rs. {parseFloat(receiptSale.sub_total).toLocaleString()}</span>
                </div>
                <div className="flex justify-between text-red-500">
                  <span>DISCOUNT</span>
                  <span>-Rs. {parseFloat(receiptSale.discount_amount).toLocaleString()}</span>
                </div>
                <div className="flex justify-between text-xs font-extrabold text-slate-900 border-t border-dashed border-slate-300 pt-2">
                  <span>NET TOTAL</span>
                  <span>Rs. {parseFloat(receiptSale.net_amount).toLocaleString()}</span>
                </div>
              </div>

              {/* Payments breakdown */}
              {receiptSale.payments && receiptSale.payments.length > 0 && (
                <div className="flex flex-col gap-1 text-[10px] text-slate-600">
                  <span className="font-bold text-slate-700">PAYMENTS SUMMARY:</span>
                  {receiptSale.payments.map((p: any, idx: number) => (
                    <div key={idx} className="flex justify-between">
                      <span className="uppercase">{p.payment_method}</span>
                      <span>Rs. {parseFloat(p.amount).toLocaleString()}</span>
                    </div>
                  ))}
                  <div className="flex justify-between font-bold text-slate-800 mt-1 border-t border-dotted border-slate-300 pt-1">
                    <span>CHANGE RETURNED</span>
                    <span>Rs. {parseFloat(receiptSale.change_returned || 0).toLocaleString()}</span>
                  </div>
                </div>
              )}
            </div>

            {/* Digital Copy Dispatch Panel */}
            <div className="border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-900 p-4 rounded-2xl max-w-sm mx-auto w-full flex flex-col gap-3.5 text-left shadow-inner">
              <h4 className="text-[10px] font-extrabold uppercase tracking-wider text-slate-400 border-b border-slate-200 dark:border-slate-800 pb-1.5 flex items-center justify-between">
                <span>Send Digital Copy</span>
              </h4>

              {/* Email channel */}
              <div className="flex flex-col gap-1.5">
                <span className="text-[10px] font-bold text-slate-500">Email Customer Receipt</span>
                <div className="flex gap-2">
                  <input
                    type="email"
                    placeholder="e.g. customer@example.com"
                    value={dispatchEmail}
                    onChange={(e) => setDispatchEmail(e.target.value)}
                    className="flex-grow bg-white dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-xl px-3 py-2 text-xs focus:outline-none focus:ring-1 focus:ring-brand-500 text-slate-700 dark:text-slate-200 min-w-0"
                  />
                  <Button 
                    onClick={() => handleSendReceipt('email', dispatchEmail)}
                    isLoading={isDispatchingEmail}
                    disabled={!dispatchEmail}
                    variant="primary"
                    className="min-h-[auto] py-2 px-4 text-xs font-bold shrink-0"
                  >
                    Send Email
                  </Button>
                </div>
              </div>

              {/* WhatsApp channel */}
              <div className="flex flex-col gap-1.5">
                <span className="text-[10px] font-bold text-slate-500">WhatsApp Mobile Number</span>
                <div className="flex gap-2">
                  <input
                    type="tel"
                    placeholder="e.g. +94777123456"
                    value={dispatchPhone}
                    onChange={(e) => setDispatchPhone(e.target.value)}
                    className="flex-grow bg-white dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-xl px-3 py-2 text-xs focus:outline-none focus:ring-1 focus:ring-brand-500 text-slate-700 dark:text-slate-200 min-w-0"
                  />
                  <Button 
                    onClick={() => handleSendReceipt('whatsapp', dispatchPhone)}
                    isLoading={isDispatchingPhone}
                    disabled={!dispatchPhone}
                    variant="primary"
                    className="min-h-[auto] py-2 px-4 text-xs font-bold shrink-0"
                  >
                    Send WhatsApp
                  </Button>
                </div>
              </div>

              {/* Copy link */}
              <div className="border-t border-slate-200 dark:border-slate-800 pt-2.5 mt-1 flex justify-center">
                <button
                  onClick={() => {
                    const domain = window.location.origin;
                    navigator.clipboard.writeText(`${domain}/receipt/${receiptSale.invoice_number}`);
                    setToastType('success');
                    setToastMsg('Web Receipt URL copied to clipboard!');
                  }}
                  className="text-[10px] font-bold text-brand-500 hover:text-brand-600 transition-colors uppercase tracking-wider"
                >
                  Copy Customer Invoice Web Link
                </button>
              </div>
            </div>

            <div className="flex justify-center gap-3 mt-4">
              <Button onClick={() => window.print()} variant="secondary" icon={<Printer className="w-4 h-4" />}>
                Thermal Print
              </Button>
              <Button onClick={() => setReceiptSale(null)}>Done</Button>
            </div>

          </div>
        </Modal>
      )}

      {/* QUICK ADD CUSTOMER MODAL */}
      <Modal isOpen={isQuickCustOpen} onClose={() => setIsQuickCustOpen(false)} title="Register Customer Profile">
        <div className="flex flex-col gap-4 text-left">
          <Input 
            label="Customer Name" 
            value={quickCustName} 
            onChange={(e) => setQuickCustName(e.target.value)} 
            placeholder="e.g. Ruwan Perera" 
          />
          <Input 
            label="Mobile Number (Search Key)" 
            value={quickCustPhone} 
            onChange={(e) => setQuickCustPhone(e.target.value)} 
            placeholder="e.g. 0777123456" 
          />
          <Input 
            label="Email Address" 
            value={quickCustEmail} 
            onChange={(e) => setQuickCustEmail(e.target.value)} 
            placeholder="e.g. ruwan@gmail.com" 
          />
          
          <div className="flex justify-end gap-3 mt-4">
            <Button onClick={() => setIsQuickCustOpen(false)} variant="secondary">Cancel</Button>
            <Button onClick={handleQuickCustomerSubmit} isLoading={isLoading}>Save & Link to Bill</Button>
          </div>
        </div>
      </Modal>

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
