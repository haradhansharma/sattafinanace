import '../lib/pinia-init';
import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import type { Insurance, InsuranceCategory, InsuranceStatus, InsurancePremiumPayment, InsuranceClaim, InsuranceClaimStatus } from '../types';
import { mockInsurances } from '../mock-data';
import { generateId } from '../utils/formatters';

export const useInsuranceStore = defineStore('insurance', () => {
  const insurances = ref<Insurance[]>(mockInsurances.map(i => ({
    ...i,
    premiumPayments: i.premiumPayments.map(p => ({ ...p })),
    claims: i.claims.map(c => ({ ...c })),
    beneficiaries: i.beneficiaries.map(b => ({ ...b })),
  })));

  // ==================== Computed ====================

  const activeInsurances = computed(() =>
    insurances.value.filter(i => i.status === 'active')
  );

  const pendingRenewals = computed(() =>
    insurances.value.filter(i => i.status === 'pending_renewal')
  );

  const totalCoverage = computed(() =>
    activeInsurances.value.reduce((sum, i) => sum + i.coverageAmount, 0)
  );

  const totalAnnualPremium = computed(() =>
    insurances.value.filter(i => i.status === 'active' || i.status === 'pending_renewal').reduce((sum, i) => {
      const annual = i.premiumFrequency === 'monthly' ? i.premiumAmount * 12
        : i.premiumFrequency === 'quarterly' ? i.premiumAmount * 4
        : i.premiumFrequency === 'semiannually' ? i.premiumAmount * 2
        : i.premiumAmount;
      return sum + annual;
    }, 0)
  );

  const totalPremiumPaid = computed(() =>
    insurances.value.reduce((sum, i) => sum + i.totalPremiumPaid, 0)
  );

  const totalClaimed = computed(() =>
    insurances.value.reduce((sum, i) => sum + i.totalClaimedAmount, 0)
  );

  const openClaimsCount = computed(() =>
    insurances.value.reduce((sum, i) => sum + i.claims.filter(c => c.status === 'pending' || c.status === 'in_review').length, 0)
  );

  const upcomingRenewals = computed(() => {
    const now = new Date();
    const thirtyDaysLater = new Date(now.getTime() + 30 * 24 * 60 * 60 * 1000);
    return insurances.value.filter(i => {
      if (!i.nextPremiumDueDate) return false;
      const due = new Date(i.nextPremiumDueDate);
      return due >= now && due <= thirtyDaysLater && (i.status === 'active' || i.status === 'pending_renewal');
    });
  });

  // Category breakdowns
  const insurancesByCategory = computed(() => {
    const map: Record<InsuranceCategory, Insurance[]> = {
      life: [], health: [], vehicle: [], property: [],
      travel: [], critical_illness: [], other: [],
    };
    insurances.value.forEach(i => {
      if (map[i.category]) map[i.category].push(i);
    });
    return map;
  });

  const categoryTotals = computed(() => {
    const map = {} as Record<string, { count: number; coverage: number; annualPremium: number; paid: number }>;
    insurances.value.forEach(i => {
      if (!map[i.category]) map[i.category] = { count: 0, coverage: 0, annualPremium: 0, paid: 0 };
      map[i.category].count += 1;
      map[i.category].coverage += i.coverageAmount;
      const annual = i.premiumFrequency === 'monthly' ? i.premiumAmount * 12
        : i.premiumFrequency === 'quarterly' ? i.premiumAmount * 4
        : i.premiumFrequency === 'semiannually' ? i.premiumAmount * 2
        : i.premiumAmount;
      map[i.category].annualPremium += annual;
      map[i.category].paid += i.totalPremiumPaid;
    });
    return map;
  });

  // ==================== CRUD ====================

  function addInsurance(data: Omit<Insurance, 'id' | 'createdAt' | 'updatedAt' | 'premiumPayments' | 'claims' | 'totalPremiumPaid' | 'paidPremiumsCount' | 'totalClaimedAmount'>) {
    const now = new Date().toISOString();
    const ins: Insurance = {
      ...data,
      premiumPayments: [],
      claims: [],
      totalPremiumPaid: 0,
      paidPremiumsCount: 0,
      totalClaimedAmount: 0,
      id: generateId('ins'),
      createdAt: now,
      updatedAt: now,
    };
    insurances.value.push(ins);
    return ins;
  }

  function updateInsurance(id: string, data: Partial<Insurance>) {
    const index = insurances.value.findIndex(i => i.id === id);
    if (index === -1) return null;
    insurances.value[index] = {
      ...insurances.value[index],
      ...data,
      id: insurances.value[index].id,
      createdAt: insurances.value[index].createdAt,
      premiumPayments: data.premiumPayments ?? insurances.value[index].premiumPayments,
      claims: data.claims ?? insurances.value[index].claims,
      beneficiaries: data.beneficiaries ?? insurances.value[index].beneficiaries,
      updatedAt: new Date().toISOString(),
    };
    return insurances.value[index];
  }

  function deleteInsurance(id: string) {
    const index = insurances.value.findIndex(i => i.id === id);
    if (index !== -1) insurances.value.splice(index, 1);
  }

  function addPremiumPayment(insuranceId: string, payment: Omit<InsurancePremiumPayment, 'id' | 'createdAt' | 'updatedAt' | 'insuranceId'>) {
    const ins = insurances.value.find(i => i.id === insuranceId);
    if (!ins) return;

    const now = new Date().toISOString();
    const newPayment: InsurancePremiumPayment = {
      ...payment,
      insuranceId,
      id: generateId('pp'),
      createdAt: now,
      updatedAt: now,
    };
    ins.premiumPayments.push(newPayment);
    ins.totalPremiumPaid += payment.amount;
    ins.paidPremiumsCount += 1;
    ins.updatedAt = now;

    // Update next premium due date
    if (ins.expiryDate) {
      const nextDue = new Date(payment.paymentDate);
      const freq = ins.premiumFrequency;
      if (freq === 'monthly') nextDue.setMonth(nextDue.getMonth() + 1);
      else if (freq === 'quarterly') nextDue.setMonth(nextDue.getMonth() + 3);
      else if (freq === 'semiannually') nextDue.setMonth(nextDue.getMonth() + 6);
      else if (freq === 'annually') nextDue.setFullYear(nextDue.getFullYear() + 1);
      if (nextDue < new Date(ins.expiryDate)) {
        ins.nextPremiumDueDate = nextDue.toISOString();
      } else {
        ins.nextPremiumDueDate = undefined;
      }
    }

    // Move from pending_renewal to active
    if (ins.status === 'pending_renewal') {
      ins.status = 'active';
    }

    return ins;
  }

  function addClaim(insuranceId: string, claim: Omit<InsuranceClaim, 'id' | 'createdAt' | 'updatedAt' | 'insuranceId'>) {
    const ins = insurances.value.find(i => i.id === insuranceId);
    if (!ins) return;

    const now = new Date().toISOString();
    const newClaim: InsuranceClaim = {
      ...claim,
      insuranceId,
      id: generateId('clm'),
      createdAt: now,
      updatedAt: now,
    };
    ins.claims.push(newClaim);
    ins.updatedAt = now;
    return ins;
  }

  function updateClaimStatus(insuranceId: string, claimId: string, status: InsuranceClaimStatus, approvedAmount?: number, resolutionNote?: string) {
    const ins = insurances.value.find(i => i.id === insuranceId);
    if (!ins) return;
    const claim = ins.claims.find(c => c.id === claimId);
    if (!claim) return;

    claim.status = status;
    if (approvedAmount !== undefined) claim.approvedAmount = approvedAmount;
    if (resolutionNote) claim.resolutionNote = resolutionNote;
    if (status === 'paid' && claim.approvedAmount) {
      ins.totalClaimedAmount += claim.approvedAmount;
    }
    if (status === 'approved' || status === 'paid' || status === 'rejected') {
      claim.resolutionDate = new Date().toISOString();
    }
    ins.updatedAt = new Date().toISOString();
    return ins;
  }

  function updateStatus(id: string, status: InsuranceStatus) {
    const ins = insurances.value.find(i => i.id === id);
    if (!ins) return;
    ins.status = status;
    ins.updatedAt = new Date().toISOString();
  }

  function getInsuranceById(id: string): Insurance | undefined {
    return insurances.value.find(i => i.id === id);
  }

  return {
    insurances,
    activeInsurances,
    pendingRenewals,
    totalCoverage,
    totalAnnualPremium,
    totalPremiumPaid,
    totalClaimed,
    openClaimsCount,
    upcomingRenewals,
    insurancesByCategory,
    categoryTotals,
    addInsurance,
    updateInsurance,
    deleteInsurance,
    addPremiumPayment,
    addClaim,
    updateClaimStatus,
    updateStatus,
    getInsuranceById,
  };
});
