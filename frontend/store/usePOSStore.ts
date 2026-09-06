import { create } from 'zustand';

export interface CartItem {
  variantId: number;
  productId: number;
  name: string;
  sku: string;
  barcode: string;
  price: number;
  cost: number;
  quantity: number;
  discount: number; // item-level discount amount
  taxRate: number;
}

export interface PaymentItem {
  amount: number;
  payment_method: string;
  transaction_reference?: string;
  bank_account_id?: number;
}

interface POSState {
  cart: CartItem[];
  customer: any | null;
  discount: number; // overall discount
  discountType: 'percentage' | 'flat';
  payments: PaymentItem[];
  shift: any | null;
  activeCompany: any | null;
  activeBranch: any | null;
  currentUser: any | null;
  darkMode: boolean;

  // Setters & Methods
  toggleDarkMode: () => void;
  addToCart: (item: Omit<CartItem, 'quantity' | 'discount'>) => void;
  updateCartQuantity: (variantId: number, quantity: number) => void;
  removeFromCart: (variantId: number) => void;
  clearCart: () => void;
  setCustomer: (customer: any | null) => void;
  setDiscount: (discount: number, type?: 'percentage' | 'flat') => void;
  addPayment: (payment: PaymentItem) => void;
  removePayment: (index: number) => void;
  clearPayments: () => void;
  setShift: (shift: any | null) => void;
  setAuthContext: (user: any, company: any, branch: any) => void;
  logout: () => void;
}

export const usePOSStore = create<POSState>((set) => ({
  cart: [],
  customer: null,
  discount: 0,
  discountType: 'flat',
  payments: [],
  shift: null,
  activeCompany: null,
  activeBranch: null,
  currentUser: null,
  darkMode: false,

  toggleDarkMode: () => set((state) => {
    const nextMode = !state.darkMode;
    if (typeof window !== 'undefined') {
      if (nextMode) {
        document.body.classList.add('dark');
      } else {
        document.body.classList.remove('dark');
      }
    }
    return { darkMode: nextMode };
  }),

  addToCart: (item) => set((state) => {
    const existing = state.cart.find((c) => c.variantId === item.variantId);
    if (existing) {
      return {
        cart: state.cart.map((c) =>
          c.variantId === item.variantId ? { ...c, quantity: c.quantity + 1 } : c
        ),
      };
    }
    return { cart: [...state.cart, { ...item, quantity: 1, discount: 0 }] };
  }),

  updateCartQuantity: (variantId, quantity) => set((state) => {
    if (quantity <= 0) {
      return { cart: state.cart.filter((c) => c.variantId !== variantId) };
    }
    return {
      cart: state.cart.map((c) =>
        c.variantId === variantId ? { ...c, quantity } : c
      ),
    };
  }),

  removeFromCart: (variantId) => set((state) => ({
    cart: state.cart.filter((c) => c.variantId !== variantId)
  })),

  clearCart: () => set({ cart: [], customer: null, discount: 0, payments: [] }),

  setCustomer: (customer) => set({ customer }),

  setDiscount: (discount, type = 'flat') => set({ discount, discountType: type }),

  addPayment: (payment) => set((state) => ({ payments: [...state.payments, payment] })),

  removePayment: (index) => set((state) => ({
    payments: state.payments.filter((_, idx) => idx !== index)
  })),

  clearPayments: () => set({ payments: [] }),

  setShift: (shift) => set({ shift }),

  setAuthContext: (user, company, branch) => set({
    currentUser: user,
    activeCompany: company,
    activeBranch: branch
  }),

  logout: () => {
    if (typeof window !== 'undefined') {
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
    }
    set({
      currentUser: null,
      activeCompany: null,
      activeBranch: null,
      shift: null,
      cart: [],
      customer: null,
      payments: []
    });
  }
}));
