import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import type {
  Insurance,
  InsuranceCategory,
  InsuranceStatus,
  InsurancePremiumPayment,
  InsuranceClaim,
  InsuranceClaimStatus,
  InsuranceBeneficiary,
} from '../types';
import { api, fetchAllPages } from '../services/api-bridge';

export const useInsuranceStore = defineStore('insurance', () => {
  // ==================== State ====================
  const insurances = ref<Insurance[]>([]);
  const loading = ref(false);
  const error = ref<string | null>(null);

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
    insurances.value
      .filter(i => i.status === 'active' || i.status === 'pending_renewal')
      .reduce((sum, i) => {
        const annual =
          i.premiumFrequency === 'monthly'
            ? i.premiumAmount * 12
            : i.premiumFrequency === 'quarterly'
              ? i.premiumAmount * 4
              : i.premiumFrequency === 'semiannually'
                ? i.premiumAmount * 2
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
    insurances.value.reduce(
      (sum, i) =>
        sum +
        i.claims.filter(
          c => c.status === 'pending' || c.status === 'in_review'
        ).length,
      0
    )
  );

  const upcomingRenewals = computed(() => {
    const now = new Date();
    const thirtyDaysLater = new Date(now.getTime() + 30 * 24 * 60 * 60 * 1000);
    return insurances.value.filter(i => {
      if (!i.nextPremiumDueDate) return false;
      const due = new Date(i.nextPremiumDueDate);
      return (
        due >= now &&
        due <= thirtyDaysLater &&
        (i.status === 'active' || i.status === 'pending_renewal')
      );
    });
  });

  // Category breakdowns
  const insurancesByCategory = computed(() => {
    const map: Record<InsuranceCategory, Insurance[]> = {
      life: [],
      health: [],
      vehicle: [],
      property: [],
      travel: [],
      critical_illness: [],
      other: [],
    };
    insurances.value.forEach(i => {
      if (map[i.category]) map[i.category].push(i);
    });
    return map;
  });

  const categoryTotals = computed(() => {
    const map = {} as Record<
      string,
      { count: number; coverage: number; annualPremium: number; paid: number }
    >;
    insurances.value.forEach(i => {
      if (!map[i.category])
        map[i.category] = { count: 0, coverage: 0, annualPremium: 0, paid: 0 };
      map[i.category].count += 1;
      map[i.category].coverage += i.coverageAmount;
      const annual =
        i.premiumFrequency === 'monthly'
          ? i.premiumAmount * 12
          : i.premiumFrequency === 'quarterly'
            ? i.premiumAmount * 4
            : i.premiumFrequency === 'semiannually'
              ? i.premiumAmount * 2
              : i.premiumAmount;
      map[i.category].annualPremium += annual;
      map[i.category].paid += i.totalPremiumPaid;
    });
    return map;
  });

  // ==================== Fetch / List ====================

  async function fetchInsurances(params?: {
    category?: InsuranceCategory;
    status?: InsuranceStatus;
  }): Promise<void> {
    loading.value = true;
    error.value = null;
    try {
      const query: Record<string, any> = {};
      if (params?.category) query.category = params.category;
      if (params?.status) query.status = params.status;
      insurances.value = await fetchAllPages<Insurance>('/insurance/', {
        params: query,
      });
    } catch (err: any) {
      error.value = err.message || 'Failed to fetch insurances';
      throw err;
    } finally {
      loading.value = false;
    }
  }

  // ==================== Internal helpers ====================

  async function fetchInsuranceById(id: string): Promise<Insurance> {
    const result = await api.get<Insurance>(`/insurance/${id}/`);
    // Update local state so computed values stay in sync
    const idx = insurances.value.findIndex(i => i.id === id);
    if (idx !== -1) {
      insurances.value[idx] = result;
    }
    return result;
  }

  function replaceInList(insurance: Insurance): void {
    const idx = insurances.value.findIndex(i => i.id === insurance.id);
    if (idx !== -1) {
      insurances.value[idx] = insurance;
    }
  }

  // ==================== CRUD ====================

  type InsuranceCreateData = Omit<
    Insurance,
    | 'id'
    | 'createdAt'
    | 'updatedAt'
    | 'premiumPayments'
    | 'claims'
    | 'beneficiaries'
    | 'totalPremiumPaid'
    | 'paidPremiumsCount'
    | 'totalClaimedAmount'
  >;

  async function addInsurance(data: InsuranceCreateData): Promise<Insurance> {
    loading.value = true;
    error.value = null;
    try {
      const created = await api.post<Insurance>('/insurance/', data);
      insurances.value.push(created);
      return created;
    } catch (err: any) {
      error.value = err.message || 'Failed to create insurance';
      throw err;
    } finally {
      loading.value = false;
    }
  }

  async function updateInsurance(
    id: string,
    data: Partial<Insurance>
  ): Promise<Insurance> {
    loading.value = true;
    error.value = null;
    try {
      const updated = await api.put<Insurance>(`/insurance/${id}/`, data);
      replaceInList(updated);
      return updated;
    } catch (err: any) {
      error.value = err.message || 'Failed to update insurance';
      throw err;
    } finally {
      loading.value = false;
    }
  }

  async function deleteInsurance(id: string): Promise<void> {
    loading.value = true;
    error.value = null;
    try {
      await api.delete(`/insurance/${id}/`);
      const idx = insurances.value.findIndex(i => i.id === id);
      if (idx !== -1) insurances.value.splice(idx, 1);
    } catch (err: any) {
      error.value = err.message || 'Failed to delete insurance';
      throw err;
    } finally {
      loading.value = false;
    }
  }

  // ==================== Premium Payments ====================

  async function addPremiumPayment(
    insuranceId: string,
    payment: Omit<
      InsurancePremiumPayment,
      'id' | 'createdAt' | 'updatedAt' | 'insuranceId'
    >
  ): Promise<Insurance> {
    loading.value = true;
    error.value = null;
    try {
      await api.post(
        `/insurance/${insuranceId}/premium-payments/`,
        payment
      );
      // Re-fetch insurance to get updated totals (backend auto-calculates)
      const refreshed = await fetchInsuranceById(insuranceId);
      return refreshed;
    } catch (err: any) {
      error.value = err.message || 'Failed to add premium payment';
      throw err;
    } finally {
      loading.value = false;
    }
  }

  // ==================== Claims ====================

  async function addClaim(
    insuranceId: string,
    claim: Omit<
      InsuranceClaim,
      'id' | 'createdAt' | 'updatedAt' | 'insuranceId'
    >
  ): Promise<Insurance> {
    loading.value = true;
    error.value = null;
    try {
      await api.post(`/insurance/${insuranceId}/claims/`, claim);
      // Re-fetch insurance to get updated totals
      const refreshed = await fetchInsuranceById(insuranceId);
      return refreshed;
    } catch (err: any) {
      error.value = err.message || 'Failed to add claim';
      throw err;
    } finally {
      loading.value = false;
    }
  }

  async function updateClaimStatus(
    insuranceId: string,
    claimId: string,
    status: InsuranceClaimStatus,
    approvedAmount?: number,
    resolutionNote?: string
  ): Promise<Insurance> {
    loading.value = true;
    error.value = null;
    try {
      const payload: Record<string, any> = { status };
      if (approvedAmount !== undefined) payload.approvedAmount = approvedAmount;
      if (resolutionNote) payload.resolutionNote = resolutionNote;

      await api.put(
        `/insurance/${insuranceId}/claims/${claimId}/`,
        payload
      );
      // Re-fetch insurance to get updated totalClaimedAmount
      const refreshed = await fetchInsuranceById(insuranceId);
      return refreshed;
    } catch (err: any) {
      error.value = err.message || 'Failed to update claim status';
      throw err;
    } finally {
      loading.value = false;
    }
  }

  // ==================== Status Update ====================

  async function updateStatus(id: string, status: InsuranceStatus): Promise<Insurance> {
    loading.value = true;
    error.value = null;
    try {
      const updated = await api.put<Insurance>(`/insurance/${id}/`, { status });
      replaceInList(updated);
      return updated;
    } catch (err: any) {
      error.value = err.message || 'Failed to update insurance status';
      throw err;
    } finally {
      loading.value = false;
    }
  }

  // ==================== Lookup ====================

  function getInsuranceById(id: string): Insurance | undefined {
    return insurances.value.find(i => i.id === id);
  }

  // ==================== Beneficiaries (bonus sub-resource) ====================

  async function addBeneficiary(
    insuranceId: string,
    beneficiary: Omit<InsuranceBeneficiary, 'id'>
  ): Promise<Insurance> {
    loading.value = true;
    error.value = null;
    try {
      await api.post(
        `/insurance/${insuranceId}/beneficiaries/`,
        beneficiary
      );
      const refreshed = await fetchInsuranceById(insuranceId);
      return refreshed;
    } catch (err: any) {
      error.value = err.message || 'Failed to add beneficiary';
      throw err;
    } finally {
      loading.value = false;
    }
  }

  async function updateBeneficiary(
    insuranceId: string,
    benId: string,
    data: Partial<InsuranceBeneficiary>
  ): Promise<Insurance> {
    loading.value = true;
    error.value = null;
    try {
      await api.put(
        `/insurance/${insuranceId}/beneficiaries/${benId}/`,
        data
      );
      const refreshed = await fetchInsuranceById(insuranceId);
      return refreshed;
    } catch (err: any) {
      error.value = err.message || 'Failed to update beneficiary';
      throw err;
    } finally {
      loading.value = false;
    }
  }

  async function deleteBeneficiary(
    insuranceId: string,
    benId: string
  ): Promise<Insurance> {
    loading.value = true;
    error.value = null;
    try {
      await api.delete(
        `/insurance/${insuranceId}/beneficiaries/${benId}/`
      );
      const refreshed = await fetchInsuranceById(insuranceId);
      return refreshed;
    } catch (err: any) {
      error.value = err.message || 'Failed to delete beneficiary';
      throw err;
    } finally {
      loading.value = false;
    }
  }

  return {
    // State
    insurances,
    loading,
    error,
    // Computed
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
    // Fetch
    fetchInsurances,
    // CRUD
    addInsurance,
    updateInsurance,
    deleteInsurance,
    // Premium Payments
    addPremiumPayment,
    // Claims
    addClaim,
    updateClaimStatus,
    // Status
    updateStatus,
    // Lookup
    getInsuranceById,
    // Beneficiaries
    addBeneficiary,
    updateBeneficiary,
    deleteBeneficiary,
  };
});
