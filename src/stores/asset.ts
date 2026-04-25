import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import type { Asset, AssetCategory, AssetStatus, AssetValuation } from '../types';
import { api, fetchAllPages, ApiError } from '../services/api-bridge';

export const useAssetStore = defineStore('asset', () => {
  // ==================== State ====================
  const assets = ref<Asset[]>([]);
  const loading = ref(false);
  const error = ref<string | null>(null);

  // ==================== Computed ====================

  const ownedAssets = computed(() =>
    assets.value.filter(a => a.status === 'owned'),
  );

  const totalCurrentValue = computed(() =>
    ownedAssets.value.reduce((sum, a) => {
      const pct = (a.ownershipPercentage || 100) / 100;
      return sum + a.currentValue * pct;
    }, 0),
  );

  const totalPurchasePrice = computed(() =>
    assets.value.reduce((sum, a) => sum + a.purchasePrice, 0),
  );

  const totalAppreciation = computed(() =>
    ownedAssets.value.reduce((sum, a) => {
      const pct = (a.ownershipPercentage || 100) / 100;
      return sum + (a.currentValue - a.purchasePrice) * pct;
    }, 0),
  );

  const totalAssetCount = computed(() => assets.value.length);

  const ownedCount = computed(() => ownedAssets.value.length);

  const loanAgainstCount = computed(() =>
    ownedAssets.value.filter(a => a.loanAgainstAsset).length,
  );

  const assetsByCategory = computed(() => {
    const map: Record<AssetCategory, Asset[]> = {
      real_estate: [],
      vehicle: [],
      electronics: [],
      furniture: [],
      jewelry: [],
      art: [],
      equipment: [],
      other: [],
    };
    assets.value.forEach(a => {
      if (map[a.category]) map[a.category].push(a);
    });
    return map;
  });

  const categoryTotals = computed(() => {
    const map = {} as Record<string, { count: number; purchaseValue: number; currentValue: number }>;
    assets.value.forEach(a => {
      if (!map[a.category]) map[a.category] = { count: 0, purchaseValue: 0, currentValue: 0 };
      map[a.category].count += 1;
      map[a.category].purchaseValue += a.purchasePrice;
      map[a.category].currentValue += a.currentValue;
    });
    return map;
  });

  const topAppreciating = computed(() =>
    ownedAssets.value
      .filter(a => a.currentValue > a.purchasePrice)
      .sort((a, b) => (b.currentValue - b.purchasePrice) - (a.currentValue - a.purchasePrice))
      .slice(0, 5),
  );

  const topDepreciating = computed(() =>
    assets.value
      .filter(a => a.currentValue < a.purchasePrice)
      .sort((a, b) => (a.currentValue - a.purchasePrice) - (b.currentValue - b.purchasePrice))
      .slice(0, 5),
  );

  // ==================== Fetch Methods ====================

  async function fetchAssets(params?: { category?: AssetCategory; status?: AssetStatus }): Promise<void> {
    loading.value = true;
    error.value = null;
    try {
      const query: Record<string, string | undefined> = {};
      if (params?.category) query.category = params.category;
      if (params?.status) query.status = params.status;
      assets.value = await fetchAllPages<Asset>('/asset/', { params: query });
    } catch (err) {
      error.value = err instanceof ApiError ? err.message : 'Failed to fetch assets';
      throw err;
    } finally {
      loading.value = false;
    }
  }

  async function fetchAssetById(id: string): Promise<Asset> {
    loading.value = true;
    error.value = null;
    try {
      const asset = await api.get<Asset>(`/asset/${id}/`);
      const idx = assets.value.findIndex(a => a.id === asset.id);
      if (idx !== -1) {
        assets.value[idx] = asset;
      } else {
        assets.value.push(asset);
      }
      return asset;
    } catch (err) {
      error.value = err instanceof ApiError ? err.message : 'Failed to fetch asset';
      throw err;
    } finally {
      loading.value = false;
    }
  }

  // ==================== Depreciation Calculation ====================

  function calculateBookValue(asset: Asset): number | undefined {
    if (asset.depreciationMethod === 'none') return asset.currentValue;
    const years = asset.usefulLifeYears;
    if (!years) return asset.currentValue;

    const purchaseDate = new Date(asset.purchaseDate);
    const now = new Date();
    const ageYears =
      (now.getTime() - purchaseDate.getTime()) / (365.25 * 24 * 60 * 60 * 1000);
    const salvage = asset.salvageValue || 0;

    if (asset.depreciationMethod === 'straight_line') {
      const annualDep = (asset.purchasePrice - salvage) / years;
      const bookVal = asset.purchasePrice - annualDep * Math.min(ageYears, years);
      return Math.max(salvage, bookVal);
    }

    if (asset.depreciationMethod === 'declining_balance') {
      const rate = 1 - Math.pow(salvage / asset.purchasePrice, 1 / years);
      let bookVal = asset.purchasePrice;
      for (let y = 0; y < Math.floor(ageYears); y++) {
        bookVal *= 1 - rate;
      }
      return Math.max(salvage, bookVal);
    }

    return undefined;
  }

  // ==================== Query Methods ====================

  function getAssetById(id: string): Asset | undefined {
    return assets.value.find(a => a.id === id);
  }

  // ==================== CRUD ====================

  async function addAsset(data: any): Promise<Asset> {
    error.value = null;
    try {
      const asset = await api.post<Asset>('/asset/', data);
      assets.value.push(asset);
      return asset;
    } catch (err) {
      error.value = err instanceof ApiError ? err.message : 'Failed to create asset';
      throw err;
    }
  }

  async function updateAsset(id: string, data: Partial<Asset>): Promise<Asset | null> {
    error.value = null;
    try {
      const updated = await api.put<Asset>(`/asset/${id}/`, data);
      const index = assets.value.findIndex(a => a.id === id);
      if (index !== -1) {
        assets.value[index] = updated;
      }
      return updated;
    } catch (err) {
      error.value = err instanceof ApiError ? err.message : 'Failed to update asset';
      throw err;
    }
  }

  async function deleteAsset(id: string): Promise<void> {
    error.value = null;
    try {
      await api.delete(`/asset/${id}/`);
      const index = assets.value.findIndex(a => a.id === id);
      if (index !== -1) {
        assets.value.splice(index, 1);
      }
    } catch (err) {
      error.value = err instanceof ApiError ? err.message : 'Failed to delete asset';
      throw err;
    }
  }

  // ==================== Valuation Actions ====================

  async function addValuation(
    assetId: string,
    data: { date: string; value: number; note?: string },
  ): Promise<AssetValuation> {
    error.value = null;
    try {
      const valuation = await api.post<AssetValuation>(
        `/asset/${assetId}/valuations/`,
        data,
      );
      // Re-fetch asset so currentValue and computed fields are in sync
      await fetchAssetById(assetId);
      return valuation;
    } catch (err) {
      error.value = err instanceof ApiError ? err.message : 'Failed to add valuation';
      throw err;
    }
  }

  async function fetchValuations(assetId: string): Promise<AssetValuation[]> {
    loading.value = true;
    error.value = null;
    try {
      return await fetchAllPages<AssetValuation>(`/asset/${assetId}/valuations/`);
    } catch (err) {
      error.value = err instanceof ApiError ? err.message : 'Failed to fetch valuations';
      throw err;
    } finally {
      loading.value = false;
    }
  }

  async function deleteValuation(assetId: string, valId: string): Promise<void> {
    error.value = null;
    try {
      await api.delete(`/asset/${assetId}/valuations/${valId}/`);
      // Re-fetch asset to get updated state
      await fetchAssetById(assetId);
    } catch (err) {
      error.value = err instanceof ApiError ? err.message : 'Failed to delete valuation';
      throw err;
    }
  }

  // ==================== Status Update ====================

  async function updateStatus(id: string, status: AssetStatus): Promise<Asset | null> {
    return updateAsset(id, { status });
  }

  return {
    // State
    assets,
    loading,
    error,
    // Computed
    ownedAssets,
    totalCurrentValue,
    totalPurchasePrice,
    totalAppreciation,
    totalAssetCount,
    ownedCount,
    loanAgainstCount,
    assetsByCategory,
    categoryTotals,
    topAppreciating,
    topDepreciating,
    // Fetch
    fetchAssets,
    fetchAssetById,
    // Helpers
    calculateBookValue,
    // Query
    getAssetById,
    // CRUD
    addAsset,
    updateAsset,
    deleteAsset,
    // Valuations
    addValuation,
    fetchValuations,
    deleteValuation,
    // Status
    updateStatus,
  };
});
