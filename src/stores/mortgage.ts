import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import type {
  Mortgage,
  AmortizationEntry,
  HeldMortgage,
  HeldMortgagePayment,
  HeldMortgageStatus,
} from '../types';
import { api, fetchAllPages } from '../services/api-bridge';

export const useMortgageStore = defineStore('mortgage', () => {
  // ==================== State ====================
  const mortgages = ref<Mortgage[]>([]);
  const heldMortgages = ref<HeldMortgage[]>([]);
  const loading = ref(false);
  const error = ref<string | null>(null);

  // ==================== My Mortgages Computed ====================

  const activeMortgages = computed(() =>
    mortgages.value.filter(m => m.status === 'active')
  );

  const totalMortgageDebt = computed(() =>
    activeMortgages.value.reduce((sum, m) => sum + m.currentBalance, 0)
  );

  const totalMonthlyEMI = computed(() =>
    activeMortgages.value.reduce((sum, m) => sum + m.emiAmount, 0)
  );

  const totalEquity = computed(() =>
    mortgages.value.reduce((sum, m) => {
      const marketVal =
        m.property.currentMarketValue || m.property.purchasePrice;
      return sum + (marketVal - m.currentBalance);
    }, 0)
  );

  const totalEscrowMonthly = computed(() =>
    activeMortgages.value.reduce((sum, m) => sum + m.escrow.monthlyEscrow, 0)
  );

  // ==================== Held Mortgages Computed ====================

  const activeHeldMortgages = computed(() =>
    heldMortgages.value.filter(m => m.status === 'active')
  );

  const totalHeldOutstanding = computed(() =>
    heldMortgages.value
      .filter(m => m.status === 'active' || m.status === 'paused')
      .reduce((sum, m) => sum + m.currentBalance, 0)
  );

  const totalMonthlyIncome = computed(() =>
    activeHeldMortgages.value.reduce(
      (sum, m) => sum + m.expectedMonthlyPayment,
      0
    )
  );

  const totalInterestEarnedHeld = computed(() =>
    heldMortgages.value.reduce((sum, m) => sum + m.totalInterestEarned, 0)
  );

  const totalCollateralValue = computed(() =>
    heldMortgages.value.reduce((sum, m) => sum + m.collateral.currentValue, 0)
  );

  // ==================== Amortization (My Mortgages) ====================

  function generateAmortizationSchedule(mortgage: Mortgage): AmortizationEntry[] {
    const monthlyRate = mortgage.interestRate / 100 / 12;
    const balance = mortgage.loanAmount - mortgage.downPayment;
    const schedule: AmortizationEntry[] = [];
    let remaining = balance;

    for (let i = 1; i <= mortgage.totalInstallments; i++) {
      const date = new Date(mortgage.startDate);
      date.setMonth(date.getMonth() + i);

      const interestComponent = remaining * monthlyRate;
      const principalComponent = mortgage.emiAmount - interestComponent;
      remaining = Math.max(0, remaining - principalComponent);

      schedule.push({
        installment: i,
        date: date.toISOString(),
        emiAmount: mortgage.emiAmount,
        principalComponent: Math.round(principalComponent),
        interestComponent: Math.round(interestComponent),
        remainingBalance: Math.round(remaining),
        isPaid: i <= mortgage.paidInstallments,
      });
    }

    return schedule;
  }

  // ==================== Amortization (Held Mortgages) ====================

  function generateHeldAmortizationSchedule(
    hm: HeldMortgage
  ): AmortizationEntry[] {
    const monthlyRate = hm.interestRate / 100 / 12;
    const schedule: AmortizationEntry[] = [];
    let remaining = hm.loanAmount;

    for (let i = 1; i <= hm.totalInstallments; i++) {
      const date = new Date(hm.startDate);
      date.setMonth(date.getMonth() + i);

      const interestComponent = remaining * monthlyRate;
      const principalComponent = hm.expectedMonthlyPayment - interestComponent;
      remaining = Math.max(0, remaining - principalComponent);

      schedule.push({
        installment: i,
        date: date.toISOString(),
        emiAmount: hm.expectedMonthlyPayment,
        principalComponent: Math.round(principalComponent),
        interestComponent: Math.round(interestComponent),
        remainingBalance: Math.round(remaining),
        isPaid: i <= hm.receivedInstallments,
      });
    }

    return schedule;
  }

  // ==================== Fetch / List ====================

  async function fetchMortgages(): Promise<void> {
    loading.value = true;
    error.value = null;
    try {
      mortgages.value = await fetchAllPages<Mortgage>('/mortgage/');
    } catch (err: any) {
      error.value = err.message || 'Failed to fetch mortgages';
      throw err;
    } finally {
      loading.value = false;
    }
  }

  async function fetchHeldMortgages(): Promise<void> {
    loading.value = true;
    error.value = null;
    try {
      heldMortgages.value = await fetchAllPages<HeldMortgage>(
        '/mortgage/held/'
      );
    } catch (err: any) {
      error.value = err.message || 'Failed to fetch held mortgages';
      throw err;
    } finally {
      loading.value = false;
    }
  }

  // ==================== Internal helpers ====================

  async function fetchHeldMortgageById(id: string): Promise<HeldMortgage> {
    const result = await api.get<HeldMortgage>(`/mortgage/held/${id}/`);
    const idx = heldMortgages.value.findIndex(m => m.id === id);
    if (idx !== -1) {
      heldMortgages.value[idx] = result;
    }
    return result;
  }

  function replaceMortgage(mortgage: Mortgage): void {
    const idx = mortgages.value.findIndex(m => m.id === mortgage.id);
    if (idx !== -1) {
      mortgages.value[idx] = mortgage;
    }
  }

  function replaceHeldMortgage(hm: HeldMortgage): void {
    const idx = heldMortgages.value.findIndex(m => m.id === hm.id);
    if (idx !== -1) {
      heldMortgages.value[idx] = hm;
    }
  }

  // ==================== My Mortgage CRUD ====================

  type MortgageCreateData = Omit<Mortgage, 'id' | 'createdAt' | 'updatedAt'>;

  async function addMortgage(data: MortgageCreateData): Promise<Mortgage> {
    loading.value = true;
    error.value = null;
    try {
      const created = await api.post<Mortgage>('/mortgage/', data);
      mortgages.value.push(created);
      return created;
    } catch (err: any) {
      error.value = err.message || 'Failed to create mortgage';
      throw err;
    } finally {
      loading.value = false;
    }
  }

  async function updateMortgage(
    id: string,
    data: Partial<Mortgage>
  ): Promise<Mortgage> {
    loading.value = true;
    error.value = null;
    try {
      const updated = await api.put<Mortgage>(`/mortgage/${id}/`, data);
      replaceMortgage(updated);
      return updated;
    } catch (err: any) {
      error.value = err.message || 'Failed to update mortgage';
      throw err;
    } finally {
      loading.value = false;
    }
  }

  async function deleteMortgage(id: string): Promise<void> {
    loading.value = true;
    error.value = null;
    try {
      await api.delete(`/mortgage/${id}/`);
      const idx = mortgages.value.findIndex(m => m.id === id);
      if (idx !== -1) mortgages.value.splice(idx, 1);
    } catch (err: any) {
      error.value = err.message || 'Failed to delete mortgage';
      throw err;
    } finally {
      loading.value = false;
    }
  }

  /**
   * Record a payment on a regular mortgage.
   * Computes interest/principal split locally, then PUTs updated fields
   * to the backend and refreshes local state.
   */
  async function recordPayment(id: string, amount: number): Promise<Mortgage> {
    loading.value = true;
    error.value = null;
    try {
      const current = mortgages.value.find(m => m.id === id);
      if (!current) throw new Error('Mortgage not found');

      const monthlyRate = current.interestRate / 100 / 12;
      const interestPortion = Math.round(current.currentBalance * monthlyRate);
      const principalPortion = amount - interestPortion;

      const nextPayment = new Date(current.nextPaymentDate);
      nextPayment.setMonth(nextPayment.getMonth() + 1);

      const newPaidAmount = current.paidAmount + amount;
      const newPaidInstallments = current.paidInstallments + 1;
      const newBalance = Math.max(0, current.currentBalance - principalPortion);
      const newStatus =
        newBalance <= 0 ? ('completed' as const) : current.status;

      const updated = await api.put<Mortgage>(`/mortgage/${id}/`, {
        paidAmount: newPaidAmount,
        paidInstallments: newPaidInstallments,
        currentBalance: newBalance,
        nextPaymentDate: nextPayment.toISOString(),
        status: newStatus,
      });

      replaceMortgage(updated);
      return updated;
    } catch (err: any) {
      error.value = err.message || 'Failed to record mortgage payment';
      throw err;
    } finally {
      loading.value = false;
    }
  }

  function getMortgageById(id: string): Mortgage | undefined {
    return mortgages.value.find(m => m.id === id);
  }

  // ==================== Held Mortgage CRUD ====================

  type HeldMortgageCreateData = Omit<
    HeldMortgage,
    'id' | 'createdAt' | 'updatedAt' | 'payments'
  >;

  async function addHeldMortgage(
    data: HeldMortgageCreateData
  ): Promise<HeldMortgage> {
    loading.value = true;
    error.value = null;
    try {
      const created = await api.post<HeldMortgage>('/mortgage/held/', data);
      heldMortgages.value.push(created);
      return created;
    } catch (err: any) {
      error.value = err.message || 'Failed to create held mortgage';
      throw err;
    } finally {
      loading.value = false;
    }
  }

  async function updateHeldMortgage(
    id: string,
    data: Partial<HeldMortgage>
  ): Promise<HeldMortgage> {
    loading.value = true;
    error.value = null;
    try {
      const updated = await api.put<HeldMortgage>(
        `/mortgage/held/${id}/`,
        data
      );
      replaceHeldMortgage(updated);
      return updated;
    } catch (err: any) {
      error.value = err.message || 'Failed to update held mortgage';
      throw err;
    } finally {
      loading.value = false;
    }
  }

  async function deleteHeldMortgage(id: string): Promise<void> {
    loading.value = true;
    error.value = null;
    try {
      await api.delete(`/mortgage/held/${id}/`);
      const idx = heldMortgages.value.findIndex(m => m.id === id);
      if (idx !== -1) heldMortgages.value.splice(idx, 1);
    } catch (err: any) {
      error.value = err.message || 'Failed to delete held mortgage';
      throw err;
    } finally {
      loading.value = false;
    }
  }

  /**
   * Record a payment received on a held mortgage.
   * POSTs to the payments endpoint, then re-fetches the held mortgage
   * to get updated totals (backend auto-calculates).
   */
  async function recordHeldPayment(
    id: string,
    amount: number,
    note?: string
  ): Promise<HeldMortgage> {
    loading.value = true;
    error.value = null;
    try {
      await api.post(`/mortgage/held/${id}/payments/`, { amount, note });
      // Re-fetch to get updated totals from backend
      const refreshed = await fetchHeldMortgageById(id);
      return refreshed;
    } catch (err: any) {
      error.value = err.message || 'Failed to record held mortgage payment';
      throw err;
    } finally {
      loading.value = false;
    }
  }

  async function updateHeldMortgageStatus(
    id: string,
    status: HeldMortgageStatus
  ): Promise<HeldMortgage> {
    loading.value = true;
    error.value = null;
    try {
      const updated = await api.put<HeldMortgage>(
        `/mortgage/held/${id}/`,
        { status }
      );
      replaceHeldMortgage(updated);
      return updated;
    } catch (err: any) {
      error.value = err.message || 'Failed to update held mortgage status';
      throw err;
    } finally {
      loading.value = false;
    }
  }

  function getHeldMortgageById(id: string): HeldMortgage | undefined {
    return heldMortgages.value.find(m => m.id === id);
  }

  return {
    // State
    mortgages,
    heldMortgages,
    loading,
    error,
    // My Mortgages Computed
    activeMortgages,
    totalMortgageDebt,
    totalMonthlyEMI,
    totalEquity,
    totalEscrowMonthly,
    // My Mortgages Actions
    generateAmortizationSchedule,
    fetchMortgages,
    addMortgage,
    updateMortgage,
    deleteMortgage,
    recordPayment,
    getMortgageById,
    // Held Mortgages Computed
    activeHeldMortgages,
    totalHeldOutstanding,
    totalMonthlyIncome,
    totalInterestEarnedHeld,
    totalCollateralValue,
    // Held Mortgages Actions
    generateHeldAmortizationSchedule,
    fetchHeldMortgages,
    addHeldMortgage,
    updateHeldMortgage,
    deleteHeldMortgage,
    recordHeldPayment,
    updateHeldMortgageStatus,
    getHeldMortgageById,
  };
});
