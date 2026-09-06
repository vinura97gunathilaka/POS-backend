'use client';

import React from 'react';
import { 
  Package, Plus, ArrowRightLeft, AlertTriangle, 
  Trash2, ClipboardList, ShieldAlert, Truck, Layers, Eye
} from 'lucide-react';
import { usePOSStore } from '@/store/usePOSStore';
import { apiClient } from '@/services/api';
import { Button, Card, Input, Modal, Table, Toast, Select } from '@/components/UI';
import { hasPermission } from '@/utils/permissions';

export default function InventoryPage() {
  const { activeBranch, activeCompany, currentUser } = usePOSStore();

  if (!currentUser || !hasPermission(currentUser, 'inventory:read')) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] text-center p-6 bg-white dark:bg-slate-900 rounded-3xl border border-slate-100 dark:border-slate-800 shadow-sm text-left">
        <ShieldAlert className="w-16 h-16 text-red-500 mb-4 animate-bounce" />
        <h3 className="text-xl font-bold text-slate-800 dark:text-white mb-2">Access Denied</h3>
        <p className="text-sm text-slate-500 dark:text-slate-400 max-w-md">
          You do not have the required permissions (`inventory:read`) to access the Inventory Controls dashboard. Please contact your company administrator.
        </p>
      </div>
    );
  }
  
  // Navigation Tabs: 'ledger' | 'catalog' | 'procurement'
  const [activeTab, setActiveTab] = React.useState<'ledger' | 'catalog' | 'procurement'>('ledger');
  
  // Data lists
  const [inventories, setInventories] = React.useState<any[]>([]);
  const [products, setProducts] = React.useState<any[]>([]);
  const [categories, setCategories] = React.useState<any[]>([]);
  const [suppliers, setSuppliers] = React.useState<any[]>([]);
  const [grns, setGrns] = React.useState<any[]>([]);
  
  // Modals state
  const [isAdjustOpen, setIsAdjustOpen] = React.useState(false);
  const [isTransferOpen, setIsTransferOpen] = React.useState(false);
  const [isProductOpen, setIsProductOpen] = React.useState(false);
  const [isSupplierOpen, setIsSupplierOpen] = React.useState(false);
  const [isGrnOpen, setIsGrnOpen] = React.useState(false);
  const [isGrnDetailOpen, setIsGrnDetailOpen] = React.useState(false);
  const [selectedGrn, setSelectedGrn] = React.useState<any>(null);

  // Form: Manual Adjustment
  const [adjustQty, setAdjustQty] = React.useState('10');
  const [adjustType, setAdjustType] = React.useState('adjustment');
  const [selectedVariant, setSelectedVariant] = React.useState<number | null>(null);
  
  // Form: Stock Transfer
  const [transferTargetBranch, setTransferTargetBranch] = React.useState('');
  const [transferQty, setTransferQty] = React.useState('5');
  const [transferVariant, setTransferVariant] = React.useState('');

  // Form: Product & Variants Creation
  const [newProdName, setNewProdName] = React.useState('');
  const [newProdDesc, setNewProdDesc] = React.useState('');
  const [newProdCat, setNewProdCat] = React.useState('');
  const [newProdTax, setNewProdTax] = React.useState('8.00');
  const [newProdReorder, setNewProdReorder] = React.useState('10');
  const [newProdVariants, setNewProdVariants] = React.useState<any[]>([]);
  // Temp variant input fields
  const [tempVarName, setTempVarName] = React.useState('Regular');
  const [tempVarPrice, setTempVarPrice] = React.useState('500');
  const [tempVarCost, setTempVarCost] = React.useState('150');
  const [tempVarSku, setTempVarSku] = React.useState('');
  const [tempVarBarcode, setTempVarBarcode] = React.useState('');

  // Form: Supplier Creation
  const [newSuppName, setNewSuppName] = React.useState('');
  const [newSuppContact, setNewSuppContact] = React.useState('');
  const [newSuppEmail, setNewSuppEmail] = React.useState('');
  const [newSuppPhone, setNewSuppPhone] = React.useState('');
  const [newSuppAddress, setNewSuppAddress] = React.useState('');

  // Form: Record GRN Receipt
  const [grnSupplierId, setGrnSupplierId] = React.useState('');
  const [grnInvoiceNumber, setGrnInvoiceNumber] = React.useState('');
  const [grnNotes, setGrnNotes] = React.useState('');
  const [grnItems, setGrnItems] = React.useState<any[]>([]);
  // Temp GRN item inputs
  const [tempGrnVarId, setTempGrnVarId] = React.useState('');
  const [tempGrnQty, setTempGrnQty] = React.useState('10');
  const [tempGrnCost, setTempGrnCost] = React.useState('150');
  const [tempGrnBatch, setTempGrnBatch] = React.useState('');
  const [tempGrnExpiry, setTempGrnExpiry] = React.useState('');

  // Form: Recipe Components Configuration (BOM)
  const [isRecipeOpen, setIsRecipeOpen] = React.useState(false);
  const [selectedProductForRecipe, setSelectedProductForRecipe] = React.useState<any>(null);
  const [selectedVariantIdForRecipe, setSelectedVariantIdForRecipe] = React.useState<number | string>('');
  const [recipeComponents, setRecipeComponents] = React.useState<any[]>([]);
  const [newIngredientId, setNewIngredientId] = React.useState<number | string>('');
  const [newIngredientQty, setNewIngredientQty] = React.useState<string>('1');

  const [toastMsg, setToastMsg] = React.useState('');
  const [toastType, setToastType] = React.useState<'success' | 'error'>('success');
  const [isLoading, setIsLoading] = React.useState(false);

  // Fetch all necessary data
  const fetchData = async () => {
    try {
      const invRes = await apiClient.get('/inventory');
      if (invRes.data.success && invRes.data.data) {
        setInventories(invRes.data.data);
      }
      
      const prodRes = await apiClient.get('/catalog/products');
      if (prodRes.data.success && prodRes.data.data) {
        setProducts(prodRes.data.data);
      }

      const catRes = await apiClient.get('/catalog/categories');
      if (catRes.data.success && catRes.data.data) {
        setCategories(catRes.data.data);
        if (catRes.data.data.length > 0 && !newProdCat) {
          setNewProdCat(catRes.data.data[0].id.toString());
        }
      }

      const suppRes = await apiClient.get('/crm/suppliers');
      if (suppRes.data.success && suppRes.data.data) {
        setSuppliers(suppRes.data.data);
        if (suppRes.data.data.length > 0 && !grnSupplierId) {
          setGrnSupplierId(suppRes.data.data[0].id.toString());
        }
      }

      const grnRes = await apiClient.get('/procurement/grns');
      if (grnRes.data.success && grnRes.data.data) {
        setGrns(grnRes.data.data);
      }
    } catch (err) {}
  };

  React.useEffect(() => {
    fetchData();
  }, []);

  const triggerToast = (msg: string, type: 'success' | 'error' = 'success') => {
    setToastMsg(msg);
    setToastType(type);
  };

  const fetchRecipeForVariant = (variantId: number) => {
    setIsLoading(true);
    apiClient.get(`/catalog/variants/${variantId}/recipe`)
      .then((res) => {
        if (res.data.success && res.data.data) {
          const fetched = res.data.data.map((c: any) => ({
            component_variant_id: c.component_variant_id,
            quantity: c.quantity,
            component_variant: {
              id: c.component_variant?.id,
              name: c.component_variant?.name,
              sku: c.component_variant?.sku,
              price: c.component_variant?.price,
              cost: c.component_variant?.cost,
              product_name: c.component_variant?.product?.name || 'Item'
            }
          }));
          setRecipeComponents(fetched);
        }
      })
      .catch((err) => {
        triggerToast(err.response?.data?.detail || 'Failed to load recipe components.', 'error');
      })
      .finally(() => {
        setIsLoading(false);
      });
  };

  const handleOpenRecipe = (product: any) => {
    setSelectedProductForRecipe(product);
    if (product.variants && product.variants.length > 0) {
      const defaultVarId = product.variants[0].id;
      setSelectedVariantIdForRecipe(defaultVarId);
      fetchRecipeForVariant(defaultVarId);
    } else {
      setRecipeComponents([]);
    }
    setNewIngredientId('');
    setNewIngredientQty('1');
    setIsRecipeOpen(true);
  };

  const addRecipeIngredient = () => {
    if (!newIngredientId) {
      triggerToast('Please select an ingredient variant first.', 'error');
      return;
    }
    const qty = parseInt(newIngredientQty);
    if (isNaN(qty) || qty <= 0) {
      triggerToast('Please enter a valid ingredient quantity greater than 0.', 'error');
      return;
    }

    const exists = recipeComponents.some(c => c.component_variant_id === parseInt(newIngredientId.toString()));
    if (exists) {
      triggerToast('This ingredient component is already in the list.', 'error');
      return;
    }

    let foundVar: any = null;
    products.forEach((p: any) => {
      p.variants?.forEach((v: any) => {
        if (v.id === parseInt(newIngredientId.toString())) {
          foundVar = {
            id: v.id,
            name: v.name,
            sku: v.sku,
            price: v.price,
            cost: v.cost,
            product_name: p.name
          };
        }
      });
    });

    if (!foundVar) {
      triggerToast('Ingredient variant not found.', 'error');
      return;
    }

    setRecipeComponents([...recipeComponents, {
      component_variant_id: parseInt(newIngredientId.toString()),
      quantity: qty,
      component_variant: foundVar
    }]);

    setNewIngredientId('');
    setNewIngredientQty('1');
  };

  const removeRecipeIngredient = (idx: number) => {
    setRecipeComponents(recipeComponents.filter((_, i) => i !== idx));
  };

  const saveRecipeComponents = () => {
    setIsLoading(true);
    const payload = recipeComponents.map(c => ({
      component_variant_id: c.component_variant_id,
      quantity: c.quantity
    }));

    apiClient.put(`/catalog/variants/${selectedVariantIdForRecipe}/recipe`, payload)
      .then((res) => {
        if (res.data.success) {
          triggerToast('Bill of Materials (BOM) saved successfully!', 'success');
          setIsRecipeOpen(false);
          fetchData();
        }
      })
      .catch((err) => {
        triggerToast(err.response?.data?.detail || 'Failed to save recipe components.', 'error');
      })
      .finally(() => {
        setIsLoading(false);
      });
  };

  // Submit Manual Stock Adjustment
  const handleAdjustSubmit = async () => {
    if (!selectedVariant) return;
    setIsLoading(true);
    try {
      const res = await apiClient.post('/inventory/adjust', {
        branch_id: activeBranch ? activeBranch.id : 1,
        product_variant_id: selectedVariant,
        quantity: parseInt(adjustQty),
        type: adjustType,
        notes: "Manual adjustment logged from web portal"
      });
      if (res.data.success) {
        triggerToast('Inventory adjusted successfully.');
        setIsAdjustOpen(false);
        fetchData();
      }
    } catch (err: any) {
      triggerToast(err.response?.data?.error || 'Adjustment failed.', 'error');
    } finally {
      setIsLoading(false);
    }
  };

  // Submit Stock Transfer
  const handleTransferSubmit = async () => {
    setIsLoading(true);
    try {
      const payload = {
        company_id: activeCompany.id,
        from_branch_id: activeBranch.id,
        to_branch_id: parseInt(transferTargetBranch),
        transfer_date: new Date().toISOString(),
        notes: "Cross branch transfer",
        items: [
          {
            product_variant_id: parseInt(transferVariant),
            quantity_transferred: parseInt(transferQty)
          }
        ]
      };
      
      const res = await apiClient.post('/inventory/transfers', payload);
      if (res.data.success) {
        triggerToast('Stock transfer request created successfully.');
        setIsTransferOpen(false);
        fetchData();
      }
    } catch (err: any) {
      triggerToast('Failed to process stock transfer request.', 'error');
    } finally {
      setIsLoading(false);
    }
  };

  // Add temp variant to Product Creation Form
  const addTempVariant = () => {
    if (!tempVarName) {
      triggerToast('Variant name is required', 'error');
      return;
    }
    const newVar = {
      name: tempVarName,
      price: parseFloat(tempVarPrice) || 0,
      cost: parseFloat(tempVarCost) || 0,
      sku: tempVarSku || `SKU-${Date.now()}-${newProdVariants.length}`,
      barcode: tempVarBarcode || `BAR-${Date.now()}-${newProdVariants.length}`,
      attributes: { size: tempVarName }
    };
    setNewProdVariants([...newProdVariants, newVar]);
    setTempVarName('Regular');
    setTempVarSku('');
    setTempVarBarcode('');
  };

  // Remove variant from Product Creation Form
  const removeTempVariant = (idx: number) => {
    setNewProdVariants(newProdVariants.filter((_, i) => i !== idx));
  };

  // Submit Product Creation
  const handleProductSubmit = async () => {
    if (!newProdName) {
      triggerToast('Product name is required.', 'error');
      return;
    }
    if (newProdVariants.length === 0) {
      triggerToast('Add at least one product variant.', 'error');
      return;
    }
    setIsLoading(true);
    try {
      const payload = {
        company_id: activeCompany.id,
        category_id: newProdCat ? parseInt(newProdCat) : null,
        name: newProdName,
        description: newProdDesc,
        tax_rate: parseFloat(newProdTax) || 0,
        type: 'product',
        track_inventory: true,
        reorder_level: parseInt(newProdReorder) || 10,
        variants: newProdVariants
      };

      const res = await apiClient.post('/catalog/products', payload);
      if (res.data.success) {
        triggerToast('Product & variants created successfully.');
        setIsProductOpen(false);
        // Reset state
        setNewProdName('');
        setNewProdDesc('');
        setNewProdVariants([]);
        fetchData();
      }
    } catch (err) {
      triggerToast('Failed to create product catalog item.', 'error');
    } finally {
      setIsLoading(false);
    }
  };

  // Submit Supplier Creation
  const handleSupplierSubmit = async () => {
    if (!newSuppName) {
      triggerToast('Supplier name is required.', 'error');
      return;
    }
    setIsLoading(true);
    try {
      const payload = {
        company_id: activeCompany.id,
        name: newSuppName,
        contact_person: newSuppContact,
        email: newSuppEmail || null,
        phone: newSuppPhone || null,
        address: newSuppAddress || null
      };

      const res = await apiClient.post('/crm/suppliers', payload);
      if (res.data.success) {
        triggerToast('Supplier registered successfully.');
        setIsSupplierOpen(false);
        setNewSuppName('');
        setNewSuppContact('');
        setNewSuppEmail('');
        setNewSuppPhone('');
        setNewSuppAddress('');
        fetchData();
      }
    } catch (err) {
      triggerToast('Failed to create supplier profile.', 'error');
    } finally {
      setIsLoading(false);
    }
  };

  // Add temp item to GRN list
  const addTempGrnItem = () => {
    if (!tempGrnVarId) {
      triggerToast('Select a variant first.', 'error');
      return;
    }
    
    // Find name of variant for local rendering list
    let name = 'Unknown Variant';
    products.forEach(p => {
      p.variants?.forEach((v: any) => {
        if (v.id.toString() === tempGrnVarId) {
          name = `${p.name} - ${v.name}`;
        }
      });
    });

    const newItem = {
      product_variant_id: parseInt(tempGrnVarId),
      variantName: name,
      quantity_received: parseInt(tempGrnQty) || 1,
      unit_cost: parseFloat(tempGrnCost) || 0,
      batch_number: tempGrnBatch || null,
      expiry_date: tempGrnExpiry ? tempGrnExpiry : null
    };

    setGrnItems([...grnItems, newItem]);
    setTempGrnQty('10');
    setTempGrnBatch('');
    setTempGrnExpiry('');
  };

  const removeGrnItem = (idx: number) => {
    setGrnItems(grnItems.filter((_, i) => i !== idx));
  };

  // Submit GRN Receipt
  const handleGrnSubmit = async () => {
    if (!grnSupplierId) {
      triggerToast('Supplier is required.', 'error');
      return;
    }
    if (grnItems.length === 0) {
      triggerToast('Add at least one item to receive.', 'error');
      return;
    }
    setIsLoading(true);
    try {
      const payload = {
        company_id: activeCompany.id,
        branch_id: activeBranch.id,
        supplier_id: parseInt(grnSupplierId),
        receive_date: new Date().toISOString(),
        invoice_number: grnInvoiceNumber || null,
        notes: grnNotes || null,
        items: grnItems.map(item => ({
          product_variant_id: item.product_variant_id,
          quantity_received: item.quantity_received,
          unit_cost: item.unit_cost,
          batch_number: item.batch_number,
          expiry_date: item.expiry_date
        }))
      };

      const res = await apiClient.post('/procurement/grns', payload);
      if (res.data.success) {
        triggerToast('Goods Received Note recorded. Inventory levels adjusted.');
        setIsGrnOpen(false);
        setGrnInvoiceNumber('');
        setGrnNotes('');
        setGrnItems([]);
        fetchData();
      }
    } catch (err) {
      triggerToast('Failed to record stock GRN receipt.', 'error');
    } finally {
      setIsLoading(false);
    }
  };

  // Setup options for select dropdowns
  const variantOptions = inventories.map((i) => ({
    label: `${i.variant?.product?.name || 'Product'} - ${i.variant?.name || `Variant #${i.product_variant_id}`} (Current: ${i.quantity})`,
    value: i.product_variant_id
  }));

  const categoryOptions = categories.map((c) => ({
    label: c.name,
    value: c.id
  }));

  const supplierOptions = suppliers.map((s) => ({
    label: s.name,
    value: s.id
  }));

  // Flatten catalog variant options for receiving GRN
  const allCatalogVariantOptions: { label: string; value: any }[] = [{ label: '-- Select Variant --', value: '' }];
  products.forEach((p) => {
    if (p.variants) {
      p.variants.forEach((v: any) => {
        allCatalogVariantOptions.push({
          label: `${p.name} - ${v.name} (${v.sku || 'No SKU'})`,
          value: v.id.toString()
        });
      });
    }
  });

  return (
    <div className="flex flex-col gap-6 text-left">
      
      {/* Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex flex-col gap-1">
          <h2 className="text-2xl font-bold dark:text-white">Inventory Controls</h2>
          <p className="text-xs text-slate-400">Track stock levels, configure catalog items, and manage vendor shipments.</p>
        </div>
        
        {/* Dynamic header button actions based on active Tab */}
        <div className="flex gap-2 shrink-0">
          {activeTab === 'ledger' && hasPermission(currentUser, 'inventory:write') && (
            <>
              <Button onClick={() => setIsTransferOpen(true)} variant="secondary" icon={<ArrowRightLeft className="w-4 h-4" />}>
                New Stock Transfer
              </Button>
              <Button onClick={() => {
                if (inventories.length > 0) {
                  setSelectedVariant(inventories[0].product_variant_id);
                }
                setIsAdjustOpen(true);
              }} icon={<Plus className="w-4 h-4" />}>
                Manual Adjustment
              </Button>
            </>
          )}
          {activeTab === 'catalog' && hasPermission(currentUser, 'inventory:write') && (
            <Button onClick={() => setIsProductOpen(true)} icon={<Plus className="w-4 h-4" />}>
              Add Product
            </Button>
          )}
          {activeTab === 'procurement' && hasPermission(currentUser, 'procurement:grn') && (
            <>
              <Button onClick={() => setIsSupplierOpen(true)} variant="secondary" icon={<Plus className="w-4 h-4" />}>
                Add Supplier
              </Button>
              <Button onClick={() => {
                if (allCatalogVariantOptions.length > 1) {
                  setTempGrnVarId(allCatalogVariantOptions[1].value);
                }
                setIsGrnOpen(true);
              }} icon={<Truck className="w-4 h-4" />}>
                Record GRN Shipment
              </Button>
            </>
          )}
        </div>
      </div>

      {/* Tabs Selector Header */}
      <div className="flex border-b border-slate-100 dark:border-slate-800 gap-6">
        <button 
          onClick={() => setActiveTab('ledger')}
          className={`pb-3 text-sm font-bold border-b-2 transition-colors ${
            activeTab === 'ledger' 
              ? 'border-brand-500 text-brand-600 dark:text-brand-400' 
              : 'border-transparent text-slate-400 hover:text-slate-600 dark:hover:text-slate-300'
          }`}
        >
          Branch Stock Ledger
        </button>
        <button 
          onClick={() => setActiveTab('catalog')}
          className={`pb-3 text-sm font-bold border-b-2 transition-colors ${
            activeTab === 'catalog' 
              ? 'border-brand-500 text-brand-600 dark:text-brand-400' 
              : 'border-transparent text-slate-400 hover:text-slate-600 dark:hover:text-slate-300'
          }`}
        >
          Product Catalog Matrix
        </button>
        {hasPermission(currentUser, 'procurement:grn') && (
          <button 
            onClick={() => setActiveTab('procurement')}
            className={`pb-3 text-sm font-bold border-b-2 transition-colors ${
              activeTab === 'procurement' 
                ? 'border-brand-500 text-brand-600 dark:text-brand-400' 
                : 'border-transparent text-slate-400 hover:text-slate-600 dark:hover:text-slate-300'
            }`}
          >
            Procurement & Suppliers
          </button>
        )}
      </div>

      {/* TAB CONTENT 1: STOCK LEDGER */}
      {activeTab === 'ledger' && (
        <Card className="p-6">
          <div className="flex items-center gap-2 mb-4">
            <Package className="w-5 h-5 text-brand-500" />
            <h3 className="font-bold text-base text-slate-800 dark:text-white">Active Branch Inventory levels</h3>
          </div>
          <Table
            headers={["Product / Variant", "Average Cost", "Stock Level", "Status"]}
            rows={inventories.map((item) => {
              const isLow = item.quantity <= (item.variant?.product?.reorder_level || 10);
              return [
                <div key={1} className="flex flex-col">
                  <span className="font-semibold text-slate-800 dark:text-white">
                    {item.variant?.product?.name || 'Product'}
                  </span>
                  <span className="text-[10px] text-slate-400">
                    {item.variant?.name || `Variant #${item.product_variant_id}`} {item.variant?.sku ? `(${item.variant.sku})` : ''}
                  </span>
                </div>,
                <span key={2}>Rs. {parseFloat(item.avg_cost).toLocaleString()}</span>,
                <span key={3} className={`font-bold ${isLow ? 'text-red-500' : 'text-slate-700 dark:text-slate-200'}`}>
                  {item.quantity} units
                </span>,
                <span key={4} className={`px-2 py-1.5 rounded-lg text-[10px] font-bold ${
                  isLow ? 'bg-red-500/10 text-red-500' : 'bg-emerald-500/10 text-emerald-500'
                }`}>
                  {isLow ? 'Low Stock Warning' : 'Healthy'}
                </span>
              ];
            })}
          />
        </Card>
      )}

      {/* TAB CONTENT 2: PRODUCT CATALOG */}
      {activeTab === 'catalog' && (
        <Card className="p-6">
          <div className="flex items-center gap-2 mb-4">
            <Layers className="w-5 h-5 text-brand-500" />
            <h3 className="font-bold text-base text-slate-800 dark:text-white">Master Product Catalog Matrix</h3>
          </div>
          <Table
            headers={
              activeCompany?.settings?.enable_recipe
                ? ["Product Name", "Category", "Tax Rate", "Reorder Level", "Active Variants", "Status", "Actions"]
                : ["Product Name", "Category", "Tax Rate", "Reorder Level", "Active Variants", "Status"]
            }
            rows={products.map((item) => {
              const variantNames = item.variants?.map((v: any) => v.name).join(', ') || 'Default';
              const row = [
                <div key={1} className="flex flex-col">
                  <span className="font-semibold text-slate-800 dark:text-white">{item.name}</span>
                  <span className="text-[10px] text-slate-400 truncate max-w-xs">{item.description}</span>
                </div>,
                <span key={2}>{item.category?.name || 'Beverages'}</span>,
                <span key={3}>{item.tax_rate}%</span>,
                <span key={4}>{item.reorder_level} units</span>,
                <span key={5} className="text-xs text-slate-400">{variantNames}</span>,
                <span key={6} className={`px-2 py-1 rounded text-[10px] font-bold uppercase ${
                  item.status === 'active' ? 'bg-emerald-500/10 text-emerald-500' : 'bg-slate-500/10 text-slate-500'
                }`}>{item.status}</span>
              ];

              if (activeCompany?.settings?.enable_recipe) {
                row.push(
                  <div key={7} className="flex gap-2">
                    <Button
                      onClick={() => handleOpenRecipe(item)}
                      variant="ghost"
                      className="min-h-[auto] py-1.5 px-2.5 text-xs text-brand-500 font-bold"
                      icon={<Layers className="w-3.5 h-3.5" />}
                    >
                      BOM / Recipe
                    </Button>
                  </div>
                );
              }

              return row;
            })}
          />
        </Card>
      )}

      {/* TAB CONTENT 3: PROCUREMENT */}
      {activeTab === 'procurement' && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Suppliers Table */}
          <div className="lg:col-span-5 flex flex-col gap-4">
            <Card className="p-6 flex flex-col gap-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Truck className="w-5 h-5 text-brand-500" />
                  <h3 className="font-bold text-base text-slate-800 dark:text-white">Registered Vendors</h3>
                </div>
              </div>
              <Table
                headers={["Supplier", "Contact", "Outstanding Bal."]}
                rows={suppliers.map((item) => [
                  <div key={1} className="flex flex-col">
                    <span className="font-bold text-slate-800 dark:text-white">{item.name}</span>
                    <span className="text-[10px] text-slate-400">{item.contact_person}</span>
                  </div>,
                  <div key={2} className="flex flex-col text-xs text-slate-400">
                    <span>{item.phone}</span>
                    <span>{item.email}</span>
                  </div>,
                  <span key={3} className="font-semibold text-slate-700 dark:text-slate-200">
                    Rs. {parseFloat(item.ledger_balance).toLocaleString()}
                  </span>
                ])}
              />
            </Card>
          </div>

          {/* GRN History Table */}
          <div className="lg:col-span-7 flex flex-col gap-4">
            <Card className="p-6 flex flex-col gap-4">
              <div className="flex items-center gap-2">
                <ClipboardList className="w-5 h-5 text-brand-500" />
                <h3 className="font-bold text-base text-slate-800 dark:text-white">Goods Received History (GRN)</h3>
              </div>
              <Table
                headers={["GRN Invoice", "Vendor", "Receive Date", "Total Cost", "Actions"]}
                rows={grns.map((item) => [
                  <div key={1} className="flex flex-col">
                    <span className="font-bold text-slate-800 dark:text-white">{item.invoice_number || `GRN #${item.id}`}</span>
                    <span className="text-[10px] text-slate-400 truncate max-w-[120px]">{item.notes || 'Routine restock'}</span>
                  </div>,
                  <span key={2}>{item.supplier?.name}</span>,
                  <span key={3} className="text-xs text-slate-400">
                    {new Date(item.receive_date).toLocaleDateString()}
                  </span>,
                  <span key={4} className="font-bold text-emerald-600 dark:text-emerald-400">
                    Rs. {parseFloat(item.total_amount).toLocaleString()}
                  </span>,
                  <Button 
                    key={5} 
                    onClick={() => {
                      setSelectedGrn(item);
                      setIsGrnDetailOpen(true);
                    }}
                    variant="ghost" 
                    icon={<Eye className="w-4 h-4" />} 
                    className="min-h-0 py-1 px-2 text-xs"
                  >
                    View
                  </Button>
                ])}
              />
            </Card>
          </div>
        </div>
      )}

      {/* MODAL 1: MANUAL STOCK ADJUSTMENT */}
      <Modal isOpen={isAdjustOpen} onClose={() => setIsAdjustOpen(false)} title="Perform Manual Stock Adjustment">
        <div className="flex flex-col gap-4 text-left">
          {inventories.length > 0 ? (
            <Select 
              label="Target Product Variant"
              value={selectedVariant || ''}
              onChange={(e) => setSelectedVariant(parseInt(e.target.value))}
              options={variantOptions}
            />
          ) : (
            <span className="text-xs text-slate-400">No stock levels in branch to adjust.</span>
          )}

          <Input
            label="Adjustment Qty (Negative to write-off)"
            type="number"
            value={adjustQty}
            onChange={(e) => setAdjustQty(e.target.value)}
          />

          <Select
            label="Adjustment Code / Reason"
            value={adjustType}
            onChange={(e) => setAdjustType(e.target.value)}
            options={[
              { label: "General Reconciliation", value: "adjustment" },
              { label: "Damaged Stock Write-off", value: "damage" },
              { label: "Expired Product Disposal", value: "expired" }
            ]}
          />

          <div className="flex justify-end gap-3 mt-4">
            <Button onClick={() => setIsAdjustOpen(false)} variant="secondary">Cancel</Button>
            <Button onClick={handleAdjustSubmit} isLoading={isLoading}>Save Adjustments</Button>
          </div>
        </div>
      </Modal>

      {/* MODAL 2: CROSS BRANCH TRANSFER */}
      <Modal isOpen={isTransferOpen} onClose={() => setIsTransferOpen(false)} title="Initiate Cross Branch Stock Transfer">
        <div className="flex flex-col gap-4 text-left">
          <Input
            label="Destination Branch ID"
            type="number"
            placeholder="e.g. 2"
            value={transferTargetBranch}
            onChange={(e) => setTransferTargetBranch(e.target.value)}
          />
          {inventories.length > 0 ? (
            <Select 
              label="Variant to Transfer"
              value={transferVariant}
              onChange={(e) => setTransferVariant(e.target.value)}
              options={[{ label: '-- Select --', value: '' }, ...variantOptions]}
            />
          ) : (
            <span className="text-xs text-slate-400">No variants available in branch.</span>
          )}
          <Input
            label="Transfer Quantity"
            type="number"
            placeholder="e.g. 5"
            value={transferQty}
            onChange={(e) => setTransferQty(e.target.value)}
          />
          <div className="flex justify-end gap-3 mt-4">
            <Button onClick={() => setIsTransferOpen(false)} variant="secondary">Cancel</Button>
            <Button onClick={handleTransferSubmit} isLoading={isLoading}>Dispatch Request</Button>
          </div>
        </div>
      </Modal>

      {/* MODAL 3: ADD PRODUCT & VARIANTS */}
      <Modal isOpen={isProductOpen} onClose={() => setIsProductOpen(false)} title="Add Master Product & Config Variants">
        <div className="flex flex-col gap-4 text-left">
          <div className="grid grid-cols-2 gap-4">
            <Input label="Product Name" value={newProdName} onChange={(e) => setNewProdName(e.target.value)} placeholder="e.g. Mocha Latte" />
            {categories.length > 0 ? (
              <Select label="Category" value={newProdCat} onChange={(e) => setNewProdCat(e.target.value)} options={categoryOptions} />
            ) : (
              <Input label="Category" disabled value="Default" />
            )}
          </div>

          <div className="grid grid-cols-3 gap-4">
            <Input label="Tax Rate (%)" type="number" value={newProdTax} onChange={(e) => setNewProdTax(e.target.value)} />
            <Input label="Reorder Level" type="number" value={newProdReorder} onChange={(e) => setNewProdReorder(e.target.value)} />
            <Input label="Description" value={newProdDesc} onChange={(e) => setNewProdDesc(e.target.value)} placeholder="Flavour details" />
          </div>

          {/* Subform: Add variants */}
          <div className="p-4 rounded-xl border border-slate-100 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-900/40 flex flex-col gap-3">
            <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">Define Variant Attributes</span>
            
            <div className="grid grid-cols-2 gap-3">
              <Input label="Variant Name" value={tempVarName} onChange={(e) => setTempVarName(e.target.value)} placeholder="e.g. Large / Oat Milk" />
              <Input label="SKU (Custom)" value={tempVarSku} onChange={(e) => setTempVarSku(e.target.value)} placeholder="e.g. LAT-WHO-LRG" />
            </div>

            <div className="grid grid-cols-3 gap-3">
              <Input label="Price (LKR)" type="number" value={tempVarPrice} onChange={(e) => setTempVarPrice(e.target.value)} />
              <Input label="Cost (LKR)" type="number" value={tempVarCost} onChange={(e) => setTempVarCost(e.target.value)} />
              <div className="flex items-end">
                <Button onClick={addTempVariant} variant="secondary" className="w-full text-xs font-bold min-h-0 h-[44px]">
                  Add Variant
                </Button>
              </div>
            </div>
          </div>

          {/* Variants Table Display */}
          {newProdVariants.length > 0 && (
            <div className="max-h-40 overflow-y-auto">
              <Table 
                headers={["Variant Name", "SKU", "Price / Cost", ""]}
                rows={newProdVariants.map((item, idx) => [
                  <span key={1} className="font-bold">{item.name}</span>,
                  <span key={2} className="text-xs text-slate-400">{item.sku}</span>,
                  <span key={3} className="text-xs">Rs. {item.price} / Rs. {item.cost}</span>,
                  <button key={4} onClick={() => removeTempVariant(idx)} className="text-red-500 hover:text-red-600">
                    <Trash2 className="w-4 h-4" />
                  </button>
                ])}
              />
            </div>
          )}

          <div className="flex justify-end gap-3 mt-4 border-t border-slate-100 dark:border-slate-800 pt-4">
            <Button onClick={() => setIsProductOpen(false)} variant="secondary">Cancel</Button>
            <Button onClick={handleProductSubmit} isLoading={isLoading}>Save Product & Variants</Button>
          </div>
        </div>
      </Modal>

      {/* MODAL 4: ADD SUPPLIER */}
      <Modal isOpen={isSupplierOpen} onClose={() => setIsSupplierOpen(false)} title="Register Supplier Vendor">
        <div className="flex flex-col gap-4 text-left">
          <Input label="Supplier Business Name" value={newSuppName} onChange={(e) => setNewSuppName(e.target.value)} placeholder="e.g. Ceylon Coffee Roasters" />
          <Input label="Contact Person" value={newSuppContact} onChange={(e) => setNewSuppContact(e.target.value)} placeholder="e.g. Rohan Perera" />
          
          <div className="grid grid-cols-2 gap-4">
            <Input label="Email" type="email" value={newSuppEmail} onChange={(e) => setNewSuppEmail(e.target.value)} placeholder="vendor@smartpos.com" />
            <Input label="Phone" value={newSuppPhone} onChange={(e) => setNewSuppPhone(e.target.value)} placeholder="077xxxxxxx" />
          </div>

          <Input label="Supplier Address" value={newSuppAddress} onChange={(e) => setNewSuppAddress(e.target.value)} placeholder="Roastery location" />

          <div className="flex justify-end gap-3 mt-4">
            <Button onClick={() => setIsSupplierOpen(false)} variant="secondary">Cancel</Button>
            <Button onClick={handleSupplierSubmit} isLoading={isLoading}>Register Vendor</Button>
          </div>
        </div>
      </Modal>

      {/* MODAL 5: RECORD GRN SHIPMENT */}
      <Modal isOpen={isGrnOpen} onClose={() => setIsGrnOpen(false)} title="Record Goods Received Note (GRN)">
        <div className="flex flex-col gap-4 text-left">
          <div className="grid grid-cols-2 gap-4">
            {suppliers.length > 0 ? (
              <Select label="Vendor Supplier" value={grnSupplierId} onChange={(e) => setGrnSupplierId(e.target.value)} options={supplierOptions} />
            ) : (
              <Input label="Vendor Supplier" disabled value="No Suppliers Registered" />
            )}
            <Input label="Invoice Number" value={grnInvoiceNumber} onChange={(e) => setGrnInvoiceNumber(e.target.value)} placeholder="e.g. INV-2209" />
          </div>

          <Input label="Notes" value={grnNotes} onChange={(e) => setGrnNotes(e.target.value)} placeholder="E.g. Coffee bulk import" />

          {/* Subform: Receive items */}
          <div className="p-4 rounded-xl border border-slate-100 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-900/40 flex flex-col gap-3">
            <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">Add Received Items</span>
            
            {allCatalogVariantOptions.length > 1 ? (
              <Select label="Select Variant" value={tempGrnVarId} onChange={(e) => setTempGrnVarId(e.target.value)} options={allCatalogVariantOptions} />
            ) : (
              <span className="text-xs text-red-500">Create a Product and Variant in catalog tab first!</span>
            )}

            <div className="grid grid-cols-3 gap-3">
              <Input label="Qty Received" type="number" value={tempGrnQty} onChange={(e) => setTempGrnQty(e.target.value)} />
              <Input label="Unit Cost (LKR)" type="number" value={tempGrnCost} onChange={(e) => setTempGrnCost(e.target.value)} />
              <div className="flex items-end">
                <Button onClick={addTempGrnItem} variant="secondary" className="w-full text-xs font-bold min-h-0 h-[44px]">
                  Receive Item
                </Button>
              </div>
            </div>
            
            <div className="grid grid-cols-2 gap-3">
              <Input label="Batch Number" value={tempGrnBatch} onChange={(e) => setTempGrnBatch(e.target.value)} placeholder="E.g. B-01" />
              <Input label="Expiry Date" type="date" value={tempGrnExpiry} onChange={(e) => setTempGrnExpiry(e.target.value)} />
            </div>
          </div>

          {/* GRN Items Display */}
          {grnItems.length > 0 && (
            <div className="max-h-40 overflow-y-auto">
              <Table 
                headers={["Variant Received", "Qty", "Cost (LKR)", "Total", ""]}
                rows={grnItems.map((item, idx) => [
                  <span key={1} className="font-bold text-xs">{item.variantName}</span>,
                  <span key={2} className="text-xs">{item.quantity_received} units</span>,
                  <span key={3} className="text-xs">Rs. {item.unit_cost}</span>,
                  <span key={4} className="text-xs font-bold">Rs. {item.quantity_received * item.unit_cost}</span>,
                  <button key={5} onClick={() => removeGrnItem(idx)} className="text-red-500 hover:text-red-600">
                    <Trash2 className="w-4 h-4" />
                  </button>
                ])}
              />
            </div>
          )}

          <div className="flex justify-end gap-3 mt-4 border-t border-slate-100 dark:border-slate-800 pt-4">
            <Button onClick={() => setIsGrnOpen(false)} variant="secondary">Cancel</Button>
            <Button onClick={handleGrnSubmit} isLoading={isLoading}>Record & Update Inventory</Button>
          </div>
        </div>
      </Modal>

      {/* MODAL 6: GRN DETAIL SHEET VIEW */}
      <Modal isOpen={isGrnDetailOpen} onClose={() => setIsGrnDetailOpen(false)} title={`Goods Received Note details: ${selectedGrn?.invoice_number || ''}`}>
        <div className="flex flex-col gap-4 text-left">
          {selectedGrn && (
            <>
              <div className="grid grid-cols-2 gap-4 text-xs text-slate-500">
                <div className="flex flex-col gap-1">
                  <span>Vendor Supplier: <strong>{selectedGrn.supplier?.name}</strong></span>
                  <span>Invoice Number: <strong>{selectedGrn.invoice_number || 'N/A'}</strong></span>
                </div>
                <div className="flex flex-col gap-1 text-right">
                  <span>Receive Date: <strong>{new Date(selectedGrn.receive_date).toLocaleString()}</strong></span>
                  <span>Total Amount: <strong>Rs. {parseFloat(selectedGrn.total_amount).toLocaleString()}</strong></span>
                </div>
              </div>

              <div className="border-t border-slate-100 dark:border-slate-800 pt-3 mt-2">
                <span className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-2 block">Received Items Ledger</span>
                <Table
                  headers={["Product / Variant SKU", "Quantity", "Unit Cost", "Subtotal"]}
                  rows={selectedGrn.items?.map((item: any) => [
                    <div key={1} className="flex flex-col text-xs">
                      <span>{item.variant?.product?.name || 'Product'} - {item.variant?.name || 'Variant'}</span>
                      <span className="text-[9px] text-slate-400">SKU: {item.variant?.sku || 'N/A'}</span>
                    </div>,
                    <span key={2} className="text-xs font-bold">{item.quantity_received} units</span>,
                    <span key={3} className="text-xs">Rs. {parseFloat(item.unit_cost).toLocaleString()}</span>,
                    <span key={4} className="text-xs font-bold text-slate-700 dark:text-slate-200">
                      Rs. {parseFloat(item.total_cost).toLocaleString()}
                    </span>
                  ]) || []}
                />
              </div>

              <div className="flex justify-end gap-3 mt-4 pt-3 border-t border-slate-100 dark:border-slate-800">
                <Button onClick={() => setIsGrnDetailOpen(false)}>Close Details</Button>
              </div>
            </>
          )}
        </div>
      </Modal>

      {/* MODAL 7: CONFIGURE BOM / RECIPE */}
      <Modal isOpen={isRecipeOpen} onClose={() => setIsRecipeOpen(false)} title={`Manage Bill of Materials (BOM) — ${selectedProductForRecipe?.name || ''}`}>
        <div className="flex flex-col gap-5 text-left">
          
          {/* Select Product Variant */}
          <div>
            <label className="text-xs font-black text-slate-400 dark:text-slate-500 uppercase tracking-wider block mb-2">Select Variant to Edit Recipe</label>
            <div className="flex gap-2">
              <select
                value={selectedVariantIdForRecipe}
                onChange={(e) => {
                  const val = parseInt(e.target.value);
                  setSelectedVariantIdForRecipe(val);
                  fetchRecipeForVariant(val);
                }}
                className="w-full h-11 px-4 rounded-2xl border border-slate-200 dark:border-slate-850 bg-white dark:bg-slate-950 text-slate-800 dark:text-white font-sans text-xs focus:ring-2 focus:ring-brand-500 focus:outline-none"
              >
                {selectedProductForRecipe?.variants?.map((v: any) => (
                  <option key={v.id} value={v.id}>
                    {v.name} ({v.sku || 'No SKU'})
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Current Ingredients / Components Table */}
          <div className="flex flex-col gap-3">
            <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">Active Ingredients List (Bill of Materials)</span>
            
            {recipeComponents.length > 0 ? (
              <div className="max-h-52 overflow-y-auto rounded-2xl border border-slate-100 dark:border-slate-850">
                <Table
                  headers={["Ingredient Component", "Qty Required", "Actions"]}
                  rows={recipeComponents.map((comp, idx) => {
                    const compVar = comp.component_variant || {};
                    return [
                      <div key={1} className="flex flex-col">
                        <span className="font-bold text-slate-800 dark:text-slate-200">
                          {compVar.name && compVar.name !== 'Standard' ? `${compVar.product_name || 'Item'} (${compVar.name})` : (compVar.product_name || 'Item')}
                        </span>
                        <span className="text-[10px] text-slate-450 font-mono font-medium">{compVar.sku || 'No SKU'}</span>
                      </div>,
                      <span key={2} className="font-semibold text-slate-700 dark:text-slate-350">{comp.quantity} units</span>,
                      <button
                        key={3}
                        onClick={() => removeRecipeIngredient(idx)}
                        className="text-red-500 hover:text-red-650 transition-colors p-1.5 rounded-lg hover:bg-red-500/10"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    ];
                  })}
                />
              </div>
            ) : (
              <div className="text-center p-6 border border-dashed border-slate-200 dark:border-slate-800 rounded-2xl text-xs text-slate-400 font-medium">
                No recipe ingredients defined. This variant will deduct itself directly from inventory.
              </div>
            )}
          </div>

          {/* Subform: Add New Ingredient */}
          <div className="p-4 rounded-2xl border border-slate-150 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-900/40 flex flex-col gap-3">
            <span className="text-xs font-black text-slate-400 dark:text-slate-500 uppercase tracking-wider">Add Ingredient Component</span>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              <div className="md:col-span-2">
                <Select
                  label="Select Ingredient Variant"
                  value={newIngredientId}
                  onChange={(e) => setNewIngredientId(e.target.value)}
                  options={allCatalogVariantOptions.filter(o => o.value !== selectedVariantIdForRecipe)}
                />
              </div>
              <Input
                label="Qty Needed"
                type="number"
                value={newIngredientQty}
                onChange={(e) => setNewIngredientQty(e.target.value)}
                placeholder="e.g. 2"
              />
            </div>
            <Button
              onClick={addRecipeIngredient}
              variant="secondary"
              className="text-xs font-bold w-full h-[40px] min-h-0 mt-1"
              icon={<Plus className="w-3.5 h-3.5" />}
            >
              Add Component
            </Button>
          </div>

          {/* Modal Footer Actions */}
          <div className="flex justify-end gap-3 mt-4 border-t border-slate-100 dark:border-slate-800 pt-4">
            <Button onClick={() => setIsRecipeOpen(false)} variant="secondary">Cancel</Button>
            <Button onClick={saveRecipeComponents} isLoading={isLoading} icon={<Layers className="w-4 h-4" />}>
              Save Bill of Materials
            </Button>
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
