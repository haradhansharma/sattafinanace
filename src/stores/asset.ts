import '../lib/pinia-init';
import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import type { Asset, AssetCategory, AssetStatus, AssetCondition, AssetValuation, DepreciationMethod } from '../types';
import { mockAssets } from '../mock-data';
import { generateId } from '../utils/formatters';

export const useAssetStore = defineStore('asset', () => {
  const assets = ref<Asset[]>(mockAssets.map(a => ({
    ...a,
    valuations: a.valuations.map(v => ({ ...v })),
  })));

  // ==================== Computed ====================

  const ownedAssets = computed(() =>
    assets.value.filter(a => a.status === 'owned')
  );

  const totalCurrentValue = computed(() =>
    ownedAssets.value.reduce((sum, a) => {
      const pct = (a.ownershipPercentage || 100) / 100;
      return sum + (a.currentValue * pct);
    }, 0)
  );

  const totalPurchasePrice = computed(() =>
    assets.value.reduce((sum, a) => sum + a.purchasePrice, 0)
  );

  const totalAppreciation = computed(() =>
    ownedAssets.value.reduce((sum, a) => {
      const pct = (a.ownershipPercentage || 100) / 100;
      return sum + ((a.currentValue - a.purchasePrice) * pct);
    }, 0)
  );

  const totalAssetCount = computed(() => assets.value.length);
  const ownedCount = computed(() => ownedAssets.value.length);
  const loanAgainstCount = computed(() => ownedAssets.value.filter(a => a.loanAgainstAsset).length);

  // Category breakdowns
  const assetsByCategory = computed(() => {
    const map: Record<AssetCategory, Asset[]> = {
      real_estate: [], vehicle: [], electronics: [], furniture: [],
      jewelry: [], art: [], equipment: [], other: [],
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

  // Top appreciating assets
  const topAppreciating = computed(() =>
    ownedAssets.value
      .filter(a => a.currentValue > a.purchasePrice)
      .sort((a, b) => (b.currentValue - b.purchasePrice) - (a.currentValue - a.purchasePrice))
      .slice(0, 5)
  );

  // Top depreciating assets
  const topDepreciating = computed(() =>
    assets.value
      .filter(a => a.currentValue < a.purchasePrice)
      .sort((a, b) => (a.currentValue - a.purchasePrice) - (b.currentValue - b.purchasePrice))
      .slice(0, 5)
  );

  // ==================== Depreciation Calculation ====================

  function calculateBookValue(asset: Asset): number | undefined {
    if (asset.depreciationMethod === 'none') return asset.currentValue;
    const years = asset.usefulLifeYears;
    if (!years) return asset.currentValue;

    const purchaseDate = new Date(asset.purchaseDate);
    const now = new Date();
    const ageYears = (now.getTime() - purchaseDate.getTime()) / (365.25 * 24 * 60 * 60 * 1000);
    const salvage = asset.salvageValue || 0;

    if (asset.depreciationMethod === 'straight_line') {
      const annualDep = (asset.purchasePrice - salvage) / years;
      const bookVal = asset.purchasePrice - (annualDep * Math.min(ageYears, years));
      return Math.max(salvage, bookVal);
    }

    if (asset.depreciationMethod === 'declining_balance') {
      const rate = 1 - Math.pow(salvage / asset.purchasePrice, 1 / years);
      let bookVal = asset.purchasePrice;
      for (let y = 0; y < Math.floor(ageYears); y++) {
        bookVal *= (1 - rate);
      }
      return Math.max(salvage, bookVal);
    }

    return undefined;
  }

  // ==================== CRUD ====================

  function addAsset(data: Omit<Asset, 'id' | 'createdAt' | 'updatedAt' | 'valuations' | 'currentBookValue'>) {
    const now = new Date().toISOString();
    const asset: Asset = {
      ...data,
      valuations: data.currentValue ? [{ date: new Date().toISOString().split('T')[0], value: data.currentValue, note: 'Initial valuation' }] : [],
      currentBookValue: undefined,
      id: generateId('ast'),
      createdAt: now,
      updatedAt: now,
    };
    asset.currentBookValue = calculateBookValue(asset);
    assets.value.push(asset);
    return asset;
  }

  function updateAsset(id: string, data: Partial<Asset>) {
    const index = assets.value.findIndex(a => a.id === id);
    if (index === -1) return null;
    assets.value[index] = {
      ...assets.value[index],
      ...data,
      id: assets.value[index].id,
      createdAt: assets.value[index].createdAt,
      valuations: data.valuations ?? assets.value[index].valuations,
      updatedAt: new Date().toISOString(),
    };
    assets.value[index].currentBookValue = calculateBookValue(assets.value[index]);
    return assets.value[index];
  }

  function deleteAsset(id: string) {
    const index = assets.value.findIndex(a => a.id === id);
    if (index !== -1) assets.value.splice(index, 1);
  }

  function addValuation(assetId: string, valuation: Omit<AssetValuation, never>) {
    const asset = assets.value.find(a => a.id === assetId);
    if (!asset) return;
    asset.valuations.push(valuation);
    asset.currentValue = valuation.value;
    asset.currentBookValue = calculateBookValue(asset);
    asset.updatedAt = new Date().toISOString();
    return asset;
  }

  function updateStatus(id: string, status: AssetStatus) {
    const asset = assets.value.find(a => a.id === id);
    if (!asset) return;
    asset.status = status;
    asset.updatedAt = new Date().toISOString();
  }

  function getAssetById(id: string): Asset | undefined {
    return assets.value.find(a => a.id === id);
  }

  return {
    assets,
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
    calculateBookValue,
    addAsset,
    updateAsset,
    deleteAsset,
    addValuation,
    updateStatus,
    getAssetById,
  };
});
