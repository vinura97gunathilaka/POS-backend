'use client';

import React from 'react';
import { 
  Users, Award, UserPlus, ShieldAlert, BookOpen, 
  Layers, Gift, Tag, Calendar, Plus, Sparkles, RefreshCw
} from 'lucide-react';
import { usePOSStore } from '@/store/usePOSStore';
import { apiClient } from '@/services/api';
import { Button, Card, Input, Modal, Table, Toast, Select } from '@/components/UI';
import { hasPermission } from '@/utils/permissions';

export default function CRMPage() {
  const { activeCompany, currentUser } = usePOSStore();

  const [activeTab, setActiveTab] = React.useState<'directories' | 'marketing'>('directories');

  if (!currentUser || !hasPermission(currentUser, 'crm:manage')) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] text-center p-6 bg-white dark:bg-slate-900 rounded-3xl border border-slate-100 dark:border-slate-800 shadow-sm text-left">
        <ShieldAlert className="w-16 h-16 text-red-500 mb-4 animate-bounce" />
        <h3 className="text-xl font-bold text-slate-800 dark:text-white mb-2">Access Denied</h3>
        <p className="text-sm text-slate-500 dark:text-slate-400 max-w-md">
          You do not have the required permissions (`crm:manage`) to access the CRM & Loyalty settings dashboard. Please contact your company administrator.
        </p>
      </div>
    );
  }
  
  const [customers, setCustomers] = React.useState<any[]>([]);
  const [suppliers, setSuppliers] = React.useState<any[]>([]);
  const [promotions, setPromotions] = React.useState<any[]>([]);
  const [vouchers, setVouchers] = React.useState<any[]>([]);
  
  const [isAddCustomerOpen, setIsAddCustomerOpen] = React.useState(false);
  const [isAddSupplierOpen, setIsAddSupplierOpen] = React.useState(false);
  const [isAddPromoOpen, setIsAddPromoOpen] = React.useState(false);
  const [isAddVoucherOpen, setIsAddVoucherOpen] = React.useState(false);

  // Customer/Supplier forms
  const [custName, setCustName] = React.useState('');
  const [custEmail, setCustEmail] = React.useState('');
  const [custPhone, setCustPhone] = React.useState('');
  
  const [supName, setSupName] = React.useState('');
  const [supContact, setSupContact] = React.useState('');
  const [supPhone, setSupPhone] = React.useState('');

  // Promo/Voucher forms
  const [promoName, setPromoName] = React.useState('');
  const [promoType, setPromoType] = React.useState('percentage');
  const [promoValue, setPromoValue] = React.useState('');
  const [promoMinSpend, setPromoMinSpend] = React.useState('0');
  const [promoCode, setPromoCode] = React.useState('');
  const [promoStart, setPromoStart] = React.useState('');
  const [promoEnd, setPromoEnd] = React.useState('');

  const [voucherCode, setVoucherCode] = React.useState('');
  const [voucherName, setVoucherName] = React.useState('');
  const [voucherValue, setVoucherValue] = React.useState('');
  const [voucherExpiry, setVoucherExpiry] = React.useState('');

  const [toastMsg, setToastMsg] = React.useState('');
  const [isLoading, setIsLoading] = React.useState(false);

  const fetchData = async () => {
    try {
      const res = await apiClient.get('/crm/customers');
      if (res.data.success && res.data.data) {
        setCustomers(res.data.data);
      }
      const supRes = await apiClient.get('/crm/suppliers');
      if (supRes.data.success && supRes.data.data) {
        setSuppliers(supRes.data.data);
      }
      const res1 = await apiClient.get('/marketing/promotions');
      if (res1.data.success) {
        setPromotions(res1.data.data);
      }
      const res2 = await apiClient.get('/marketing/vouchers');
      if (res2.data.success) {
        setVouchers(res2.data.data);
      }
    } catch (err) {}
  };

  React.useEffect(() => {
    fetchData();
  }, []);

  const handleAddCustomer = async () => {
    setIsLoading(true);
    try {
      const res = await apiClient.post('/crm/customers', {
        company_id: activeCompany.id,
        name: custName,
        email: custEmail,
        phone: custPhone,
        credit_limit: 10000.00
      });
      if (res.data.success) {
        setToastMsg('Customer enrolled successfully.');
        setIsAddCustomerOpen(false);
        setCustName('');
        setCustEmail('');
        setCustPhone('');
        fetchData();
      }
    } catch (err) {
      setToastMsg('Failed to enroll customer.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleAddSupplier = async () => {
    setIsLoading(true);
    try {
      const res = await apiClient.post('/crm/suppliers', {
        company_id: activeCompany.id,
        name: supName,
        contact_person: supContact,
        phone: supPhone
      });
      if (res.data.success) {
        setToastMsg('Supplier registered successfully.');
        setIsAddSupplierOpen(false);
        setSupName('');
        setSupContact('');
        setSupPhone('');
        fetchData();
      }
    } catch (err) {
      setToastMsg('Failed to register supplier.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleAddPromotion = async () => {
    if (!promoName || !promoCode || !promoValue) return;
    setIsLoading(true);
    try {
      const payload = {
        name: promoName,
        type: promoType,
        value: parseFloat(promoValue),
        min_cart_value: parseFloat(promoMinSpend) || 0.0,
        coupon_code: promoCode.toUpperCase(),
        start_date: promoStart ? new Date(promoStart).toISOString() : new Date().toISOString(),
        end_date: promoEnd ? new Date(promoEnd).toISOString() : new Date(Date.now() + 365*24*60*60*1000).toISOString()
      };
      const res = await apiClient.post('/marketing/promotions', payload);
      if (res.data.success) {
        setToastMsg('Promo coupon added successfully!');
        setIsAddPromoOpen(false);
        setPromoName('');
        setPromoCode('');
        setPromoValue('');
        setPromoMinSpend('0');
        setPromoStart('');
        setPromoEnd('');
        fetchData();
      }
    } catch (err: any) {
      setToastMsg(err.response?.data?.detail || 'Failed to add promotion coupon.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleAddVoucher = async () => {
    if (!voucherCode || !voucherValue) return;
    setIsLoading(true);
    try {
      const payload = {
        code: voucherCode.toUpperCase(),
        name: voucherName || `${voucherCode.toUpperCase()} Voucher`,
        initial_value: parseFloat(voucherValue),
        expiry_date: voucherExpiry ? new Date(voucherExpiry).toISOString() : null
      };
      const res = await apiClient.post('/marketing/vouchers', payload);
      if (res.data.success) {
        setToastMsg('Gift Voucher added successfully!');
        setIsAddVoucherOpen(false);
        setVoucherCode('');
        setVoucherName('');
        setVoucherValue('');
        setVoucherExpiry('');
        fetchData();
      }
    } catch (err: any) {
      setToastMsg(err.response?.data?.detail || 'Failed to create gift voucher.');
    } finally {
      setIsLoading(false);
    }
  };

  const getLoyaltyTier = (points: number) => {
    if (points >= 1000) return { label: 'Platinum Member', color: 'bg-indigo-500/10 text-indigo-500' };
    if (points >= 500) return { label: 'Gold Member', color: 'bg-amber-500/10 text-amber-500' };
    return { label: 'Silver Member', color: 'bg-slate-400/10 text-slate-400' };
  };

  return (
    <div className="flex flex-col gap-6 text-left pb-10">
      
      {/* Banner */}
      <div className="flex items-center justify-between">
        <div className="flex flex-col gap-1">
          <h2 className="text-2xl font-bold dark:text-white">CRM & CRM Directories</h2>
          <p className="text-xs text-slate-400">Track and manage your consumer loyalty rules, promo coupons, and gift vouchers.</p>
        </div>
        
        {activeTab === 'directories' ? (
          <div className="flex gap-2">
            <Button onClick={() => setIsAddSupplierOpen(true)} variant="secondary" icon={<BookOpen className="w-4 h-4" />}>
              Register Supplier
            </Button>
            <Button onClick={() => setIsAddCustomerOpen(true)} icon={<UserPlus className="w-4 h-4" />}>
              Enroll Customer
            </Button>
          </div>
        ) : (
          <div className="flex gap-2">
            <Button onClick={() => setIsAddPromoOpen(true)} variant="secondary" icon={<Sparkles className="w-4 h-4" />}>
              Add Coupon
            </Button>
            <Button onClick={() => setIsAddVoucherOpen(true)} icon={<Gift className="w-4 h-4" />}>
              Add Gift Voucher
            </Button>
          </div>
        )}
      </div>

      {/* Tab Switching */}
      <div className="flex gap-4 border-b border-slate-200 dark:border-slate-800 text-sm font-semibold mb-2">
        <button
          onClick={() => setActiveTab('directories')}
          className={`pb-3 px-1 border-b-2 transition-colors ${activeTab === 'directories' ? 'border-brand-500 text-brand-600 dark:text-white' : 'border-transparent text-slate-500 hover:text-slate-700'}`}
        >
          Customer & Supplier Directories
        </button>
        <button
          onClick={() => setActiveTab('marketing')}
          className={`pb-3 px-1 border-b-2 transition-colors ${activeTab === 'marketing' ? 'border-brand-500 text-brand-600 dark:text-white' : 'border-transparent text-slate-500 hover:text-slate-700'}`}
        >
          Promotions & Gift Vouchers
        </button>
      </div>

      {activeTab === 'directories' ? (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 animate-fade-in">
          
          {/* Customer Table */}
          <Card className="lg:col-span-8 p-6 flex flex-col gap-4">
            <div className="flex items-center gap-2">
              <Users className="w-5 h-5 text-brand-500" />
              <h3 className="font-bold text-base text-slate-800 dark:text-white">Customer Database</h3>
            </div>

            <Table
              headers={["Name", "Contact", "Loyalty Points", "Tier"]}
              rows={customers.map((c, i) => {
                const tier = getLoyaltyTier(c.points || 0);
                return [
                  <span key={1}>{c.name}</span>,
                  <span key={2}>{c.phone || c.email || 'N/A'}</span>,
                  <span key={3} className="font-bold text-slate-800 dark:text-white">{c.points || 0} pts</span>,
                  <span key={4} className={`px-2.5 py-1.5 rounded-lg text-[9px] font-bold uppercase tracking-wider ${tier.color}`}>
                    {tier.label}
                  </span>
                ];
              })}
            />
          </Card>

          {/* Suppliers Table */}
          <Card className="lg:col-span-4 p-6 flex flex-col gap-4">
            <div className="flex items-center gap-2">
              <Layers className="w-5 h-5 text-brand-500" />
              <h3 className="font-bold text-base text-slate-800 dark:text-white">Supplier Master Profiles</h3>
            </div>

            <Table
              headers={["Name", "Contact"]}
              rows={suppliers.map((s, i) => [
                <span key={1}>{s.name}</span>,
                <span key={2}>{s.phone || s.contact_person || 'N/A'}</span>
              ])}
            />
          </Card>

        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 animate-fade-in">
          
          {/* Promotions / Coupon Table */}
          <Card className="lg:col-span-7 p-6 flex flex-col gap-4">
            <div className="flex items-center gap-2">
              <Tag className="w-5 h-5 text-brand-500" />
              <h3 className="font-bold text-base text-slate-800 dark:text-white">Active Promo Coupons</h3>
            </div>

            <Table
              headers={["Code", "Description", "Discount Value", "Min Spend", "Expiry Date"]}
              rows={promotions.map((p, i) => [
                <span key={1} className="font-bold font-mono text-brand-500">{p.coupon_code}</span>,
                <span key={2} className="text-slate-600 dark:text-slate-350">{p.name}</span>,
                <span key={3} className="font-bold text-slate-800 dark:text-white">
                  {p.type === 'percentage' ? `${p.value}% Off` : `Rs. ${p.value}`}
                </span>,
                <span key={4} className="font-medium text-slate-500">Rs. {p.min_cart_value || 0}</span>,
                <span key={5} className="text-[11px] text-slate-400">
                  {p.end_date ? new Date(p.end_date).toLocaleDateString() : 'N/A'}
                </span>
              ])}
            />
          </Card>

          {/* Gift Vouchers Table */}
          <Card className="lg:col-span-5 p-6 flex flex-col gap-4">
            <div className="flex items-center gap-2">
              <Gift className="w-5 h-5 text-brand-500" />
              <h3 className="font-bold text-base text-slate-800 dark:text-white">Gift Card Vouchers</h3>
            </div>

            <Table
              headers={["Voucher Code", "Initial Value", "Current Balance", "Expiry"]}
              rows={vouchers.map((v, i) => [
                <span key={1} className="font-bold font-mono text-brand-500">{v.code}</span>,
                <span key={2} className="font-semibold text-slate-500">Rs. {v.initial_value}</span>,
                <span key={3} className="font-bold text-emerald-500">Rs. {v.balance}</span>,
                <span key={4} className="text-[11px] text-slate-400">
                  {v.expiry_date ? new Date(v.expiry_date).toLocaleDateString() : 'No Expiry'}
                </span>
              ])}
            />
          </Card>

        </div>
      )}

      {/* ENROLL CUSTOMER MODAL */}
      <Modal isOpen={isAddCustomerOpen} onClose={() => setIsAddCustomerOpen(false)} title="Enroll New Customer CRM">
        <div className="flex flex-col gap-4 text-left">
          <Input
            label="Full Name"
            value={custName}
            onChange={(e) => setCustName(e.target.value)}
            placeholder="e.g. John Doe"
            required
          />
          <Input
            label="Email Address"
            type="email"
            value={custEmail}
            onChange={(e) => setCustEmail(e.target.value)}
            placeholder="e.g. john@example.com"
          />
          <Input
            label="Phone Number"
            value={custPhone}
            onChange={(e) => setCustPhone(e.target.value)}
            placeholder="e.g. +94777123456"
          />
          <div className="flex justify-end gap-3 mt-4">
            <Button onClick={() => setIsAddCustomerOpen(false)} variant="secondary">Cancel</Button>
            <Button onClick={handleAddCustomer} isLoading={isLoading}>Save Customer</Button>
          </div>
        </div>
      </Modal>

      {/* REGISTER SUPPLIER MODAL */}
      <Modal isOpen={isAddSupplierOpen} onClose={() => setIsAddSupplierOpen(false)} title="Register Supplier Profile">
        <div className="flex flex-col gap-4 text-left">
          <Input
            label="Company / Supplier Name"
            value={supName}
            onChange={(e) => setSupName(e.target.value)}
            placeholder="e.g. Keells Distributors"
            required
          />
          <Input
            label="Contact Person"
            value={supContact}
            onChange={(e) => setSupContact(e.target.value)}
            placeholder="e.g. Mr. Perera"
          />
          <Input
            label="Phone Number"
            value={supPhone}
            onChange={(e) => setSupPhone(e.target.value)}
            placeholder="e.g. +94112555666"
          />
          <div className="flex justify-end gap-3 mt-4">
            <Button onClick={() => setIsAddSupplierOpen(false)} variant="secondary">Cancel</Button>
            <Button onClick={handleAddSupplier} isLoading={isLoading}>Save Supplier</Button>
          </div>
        </div>
      </Modal>

      {/* ADD PROMOTION / COUPON MODAL */}
      <Modal isOpen={isAddPromoOpen} onClose={() => setIsAddPromoOpen(false)} title="Create Promotion Coupon">
        <div className="flex flex-col gap-4 text-left">
          <Input
            label="Coupon Code (Unique)"
            value={promoCode}
            onChange={(e) => setPromoCode(e.target.value)}
            placeholder="e.g. HAPPYHOUR20"
            required
          />
          <Input
            label="Promotion Name / Description"
            value={promoName}
            onChange={(e) => setPromoName(e.target.value)}
            placeholder="e.g. 20% off Happy Hour Discount"
            required
          />
          <Select
            label="Discount Method"
            value={promoType}
            onChange={(e) => setPromoType(e.target.value)}
            options={[
              { label: "Percentage Off (%)", value: "percentage" },
              { label: "Flat Amount Off (Rs.)", value: "flat_discount" }
            ]}
          />
          <Input
            label="Discount Value"
            type="number"
            value={promoValue}
            onChange={(e) => setPromoValue(e.target.value)}
            placeholder="e.g. 20"
            required
          />
          <Input
            label="Minimum Cart Spend required (Rs.)"
            type="number"
            value={promoMinSpend}
            onChange={(e) => setPromoMinSpend(e.target.value)}
            placeholder="e.g. 1000"
          />
          <div className="grid grid-cols-2 gap-4">
            <Input
              label="Start Date"
              type="date"
              value={promoStart}
              onChange={(e) => setPromoStart(e.target.value)}
            />
            <Input
              label="End Date"
              type="date"
              value={promoEnd}
              onChange={(e) => setPromoEnd(e.target.value)}
            />
          </div>
          <div className="flex justify-end gap-3 mt-4 pt-3 border-t border-slate-100 dark:border-slate-800">
            <Button onClick={() => setIsAddPromoOpen(false)} variant="secondary">Cancel</Button>
            <Button onClick={handleAddPromotion} isLoading={isLoading}>Create Coupon</Button>
          </div>
        </div>
      </Modal>

      {/* ADD GIFT VOUCHER MODAL */}
      <Modal isOpen={isAddVoucherOpen} onClose={() => setIsAddVoucherOpen(false)} title="Issue New Gift Voucher">
        <div className="flex flex-col gap-4 text-left">
          <Input
            label="Voucher Code (Unique)"
            value={voucherCode}
            onChange={(e) => setVoucherCode(e.target.value)}
            placeholder="e.g. CEYLONVOUCH50"
            required
          />
          <Input
            label="Voucher Name / Label"
            value={voucherName}
            onChange={(e) => setVoucherName(e.target.value)}
            placeholder="e.g. Birthday Gift Voucher"
          />
          <Input
            label="Voucher Balance / Value (Rs.)"
            type="number"
            value={voucherValue}
            onChange={(e) => setVoucherValue(e.target.value)}
            placeholder="e.g. 1000"
            required
          />
          <Input
            label="Expiry Date"
            type="date"
            value={voucherExpiry}
            onChange={(e) => setVoucherExpiry(e.target.value)}
          />
          <div className="flex justify-end gap-3 mt-4 pt-3 border-t border-slate-100 dark:border-slate-800">
            <Button onClick={() => setIsAddVoucherOpen(false)} variant="secondary">Cancel</Button>
            <Button onClick={handleAddVoucher} isLoading={isLoading}>Issue Gift Card</Button>
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
