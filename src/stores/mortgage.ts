import '../lib/pinia-init';
import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import type { Mortgage, AmortizationEntry, HeldMortgage, HeldMortgagePayment, HeldMortgageStatus } from '../types';
import { mockMortgages, mockHeldMortgages } from '../mock-data';
import { generateId } from '../utils/formatters';

export const useMortgageStore = defineStore('mortgage', () => {
  const mortgages = ref<Mortgage[]>(mockMortgages.map(m => ({ ...m })));
  const heldMortgages = ref<HeldMortgage[]>(mockHeldMortgages.map(m => ({ ...m, payments: m.payments.map(p => ({ ...p })) })));

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
      const marketVal = m.property.currentMarketValue || m.property.purchasePrice;
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
    heldMortgages.value.filter(m => m.status === 'active' || m.status === 'paused').reduce((sum, m) => sum + m.currentBalance, 0)
  );

  const totalMonthlyIncome = computed(() =>
    activeHeldMortgages.value.reduce((sum, m) => sum + m.expectedMonthlyPayment, 0)
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

  function generateHeldAmortizationSchedule(hm: HeldMortgage): AmortizationEntry[] {
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

  // ==================== My Mortgage CRUD ====================

  function addMortgage(data: Omit<Mortgage, 'id' | 'createdAt' | 'updatedAt'>) {
    const now = new Date().toISOString();
    const mortgage: Mortgage = {
      ...data,
      id: generateId('mort'),
      createdAt: now,
      updatedAt: now,
    };
    mortgages.value.push(mortgage);
    return mortgage;
  }

  function updateMortgage(id: string, data: Partial<Mortgage>) {
    const index = mortgages.value.findIndex(m => m.id === id);
    if (index === -1) return null;
    mortgages.value[index] = {
      ...mortgages.value[index],
      ...data,
      id: mortgages.value[index].id,
      createdAt: mortgages.value[index].createdAt,
      updatedAt: new Date().toISOString(),
    };
    return mortgages.value[index];
  }

  function deleteMortgage(id: string) {
    const index = mortgages.value.findIndex(m => m.id === id);
    if (index !== -1) {
      mortgages.value.splice(index, 1);
    }
  }

  function recordPayment(id: string, amount: number) {
    const mortgage = mortgages.value.find(m => m.id === id);
    if (!mortgage) return;

    const monthlyRate = mortgage.interestRate / 100 / 12;
    const interestPortion = Math.round(mortgage.currentBalance * monthlyRate);
    const principalPortion = amount - interestPortion;

    const nextPayment = new Date(mortgage.nextPaymentDate);
    nextPayment.setMonth(nextPayment.getMonth() + 1);

    mortgage.paidAmount += amount;
    mortgage.paidInstallments += 1;
    mortgage.currentBalance = Math.max(0, mortgage.currentBalance - principalPortion);
    mortgage.nextPaymentDate = nextPayment.toISOString();
    mortgage.updatedAt = new Date().toISOString();

    if (mortgage.currentBalance <= 0) {
      mortgage.status = 'completed';
    }
  }

  function getMortgageById(id: string): Mortgage | undefined {
    return mortgages.value.find(m => m.id === id);
  }

  // ==================== Held Mortgage CRUD ====================

  function addHeldMortgage(data: Omit<HeldMortgage, 'id' | 'createdAt' | 'updatedAt' | 'payments'>) {
    const now = new Date().toISOString();
    const hm: HeldMortgage = {
      ...data,
      payments: [],
      id: generateId('hmort'),
      createdAt: now,
      updatedAt: now,
    };
    heldMortgages.value.push(hm);
    return hm;
  }

  function updateHeldMortgage(id: string, data: Partial<HeldMortgage>) {
    const index = heldMortgages.value.findIndex(m => m.id === id);
    if (index === -1) return null;
    heldMortgages.value[index] = {
      ...heldMortgages.value[index],
      ...data,
      id: heldMortgages.value[index].id,
      createdAt: heldMortgages.value[index].createdAt,
      payments: data.payments ?? heldMortgages.value[index].payments,
      updatedAt: new Date().toISOString(),
    };
    return heldMortgages.value[index];
  }

  function deleteHeldMortgage(id: string) {
    const index = heldMortgages.value.findIndex(m => m.id === id);
    if (index !== -1) {
      heldMortgages.value.splice(index, 1);
    }
  }

  function recordHeldPayment(id: string, amount: number, note?: string) {
    const hm = heldMortgages.value.find(m => m.id === id);
    if (!hm) return;

    const monthlyRate = hm.interestRate / 100 / 12;
    const interestPortion = Math.round(hm.currentBalance * monthlyRate);
    const principalPortion = amount - interestPortion;

    const payment: HeldMortgagePayment = {
      id: generateId('hmp'),
      heldMortgageId: id,
      amount,
      principalComponent: Math.round(principalPortion),
      interestComponent: Math.round(interestPortion),
      paymentDate: new Date().toISOString().split('T')[0],
      paymentNumber: hm.receivedInstallments + 1,
      note,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    };

    hm.payments.push(payment);

    const nextDue = new Date(hm.nextPaymentDueDate);
    nextDue.setMonth(nextDue.getMonth() + 1);

    hm.totalReceivedAmount += amount;
    hm.totalInterestEarned += Math.round(interestPortion);
    hm.receivedInstallments += 1;
    hm.currentBalance = Math.max(0, hm.currentBalance - Math.round(principalPortion));
    hm.nextPaymentDueDate = nextDue.toISOString();
    hm.updatedAt = new Date().toISOString();

    if (hm.currentBalance <= 0) {
      hm.status = 'completed';
    }
  }

  function updateHeldMortgageStatus(id: string, status: HeldMortgageStatus) {
    const hm = heldMortgages.value.find(m => m.id === id);
    if (!hm) return;
    hm.status = status;
    hm.updatedAt = new Date().toISOString();
  }

  function getHeldMortgageById(id: string): HeldMortgage | undefined {
    return heldMortgages.value.find(m => m.id === id);
  }

  return {
    // My Mortgages
    mortgages,
    activeMortgages,
    totalMortgageDebt,
    totalMonthlyEMI,
    totalEquity,
    totalEscrowMonthly,
    generateAmortizationSchedule,
    addMortgage,
    updateMortgage,
    deleteMortgage,
    recordPayment,
    getMortgageById,
    // Held Mortgages
    heldMortgages,
    activeHeldMortgages,
    totalHeldOutstanding,
    totalMonthlyIncome,
    totalInterestEarnedHeld,
    totalCollateralValue,
    generateHeldAmortizationSchedule,
    addHeldMortgage,
    updateHeldMortgage,
    deleteHeldMortgage,
    recordHeldPayment,
    updateHeldMortgageStatus,
    getHeldMortgageById,
  };
});
