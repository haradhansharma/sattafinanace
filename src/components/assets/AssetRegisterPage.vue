<script setup lang="ts">
import { ref, computed } from 'vue';
import { useAssetStore } from '../../stores/asset';
import { useCurrencyStore } from '../../stores/currency';
import { formatCurrency, formatDate } from '../../utils/formatters';
import { PageHeader, StatCard, Badge, Modal, DataTable, EmptyState, Tabs, ProgressBar } from '../ui';
import type { Asset, AssetCategory, AssetStatus, AssetCondition, DepreciationMethod, Currency } from '../../types';

const assetStore = useAssetStore();
const currencyStore = useCurrencyStore();

// ============ Tab State ============
type TabKey = 'all' | AssetCategory;
const activeTab = ref<TabKey>('all');
const tabItems = [
  { key: 'all', label: 'All', icon: '📦' },
  { key: 'real_estate', label: 'Real Estate', icon: '🏢' },
  { key: 'vehicle', label: 'Vehicles', icon: '🚗' },
  { key: 'electronics', label: 'Electronics', icon: '💻' },
  { key: 'furniture', label: 'Furniture', icon: '🪑' },
  { key: 'jewelry', label: 'Jewelry', icon: '💎' },
  { key: 'equipment', label: 'Equipment', icon: '🔧' },
];

// ============ Modal State ============
const selectedAsset = ref<Asset | null>(null);
const showDetailModal = ref(false);
const showAddModal = ref(false);
const showEditModal = ref(false);
const showValuationModal = ref(false);
const showDeleteConfirm = ref(false);

// ============ Config ============
const categoryConfig: Record<AssetCategory, { label: string; icon: string; color: string }> = {
  real_estate: { label: 'Real Estate', icon: '🏢', color: 'primary' },
  vehicle: { label: 'Vehicle', icon: '🚗', color: 'info' },
  electronics: { label: 'Electronics', icon: '💻', color: 'accent' },
  furniture: { label: 'Furniture', icon: '🪑', color: 'warning' },
  jewelry: { label: 'Jewelry', icon: '💎', color: 'danger' },
  art: { label: 'Art & Collectibles', icon: '🎨', color: 'info' },
  equipment: { label: 'Equipment', icon: '🔧', color: 'neutral' },
  other: { label: 'Other', icon: '📦', color: 'neutral' },
};

const statusConfig: Record<AssetStatus, { variant: 'success' | 'danger' | 'warning' | 'info' | 'neutral'; label: string }> = {
  owned: { variant: 'success', label: 'Owned' },
  rented: { variant: 'info', label: 'Rented' },
  leased: { variant: 'info', label: 'Leased' },
  sold: { variant: 'neutral', label: 'Sold' },
  gifted: { variant: 'neutral', label: 'Gifted' },
  damaged: { variant: 'danger', label: 'Damaged' },
  disposed: { variant: 'neutral', label: 'Disposed' },
};

const conditionConfig: Record<AssetCondition, { variant: 'success' | 'warning' | 'info' | 'danger' | 'neutral'; label: string }> = {
  excellent: { variant: 'success', label: 'Excellent' },
  good: { variant: 'info', label: 'Good' },
  fair: { variant: 'warning', label: 'Fair' },
  poor: { variant: 'danger', label: 'Poor' },
  damaged: { variant: 'danger', label: 'Damaged' },
};

const depLabels: Record<DepreciationMethod, string> = {
  none: 'None (Appreciating)',
  straight_line: 'Straight Line',
  declining_balance: 'Declining Balance',
};

// ============ Helpers ============
function fmtCur(amount: number, currency?: string): string {
  if (currency && currency !== 'BDT') {
    return currencyStore.formatWithCurrency(amount, currency as Currency);
  }
  return formatCurrency(amount, 'BDT');
}

function appreciationPct(asset: Asset): number {
  if (asset.purchasePrice === 0) return 0;
  return ((asset.currentValue - asset.purchasePrice) / asset.purchasePrice) * 100;
}

function isAppreciating(asset: Asset): boolean {
  return asset.currentValue >= asset.purchasePrice;
}

function ageYears(asset: Asset): number {
  const d = new Date(asset.purchaseDate);
  const now = new Date();
  return ((now.getTime() - d.getTime()) / (365.25 * 24 * 60 * 60 * 1000));
}

// ============ Filtered Assets ============
const filteredAssets = computed(() => {
  if (activeTab.value === 'all') return assetStore.assets;
  return assetStore.assetsByCategory[activeTab.value as AssetCategory] || [];
});

const addButtonText = computed(() => {
  if (activeTab.value === 'all') return 'Add Asset';
  return `Add ${categoryConfig[activeTab.value as AssetCategory]?.label || 'Asset'}`;
});

// ============ Valuation History Columns ============
const valuationColumns = [
  { key: 'date', label: 'Date', width: '120px' },
  { key: 'value', label: 'Value', align: 'right' as const },
  { key: 'note', label: 'Note' },
];

// ============ Add Asset Form ============
const addForm = ref({
  name: '',
  category: 'real_estate' as AssetCategory,
  description: '',
  purchaseDate: new Date().toISOString().split('T')[0],
  purchasePrice: 0,
  purchaseFrom: '',
  currentValue: 0,
  currentCondition: 'good' as AssetCondition,
  location: '',
  depreciationMethod: 'none' as DepreciationMethod,
  usefulLifeYears: 0,
  salvageValue: 0,
  status: 'owned' as AssetStatus,
  ownershipPercentage: 100,
  loanAgainstAsset: false,
  currency: 'BDT' as Currency,
  notes: '',
  // Real estate
  propertyType: 'apartment' as Asset['propertyType'],
  propertyAddress: '',
  sizeSqft: 0,
  floorNumber: '',
  // Vehicle
  vehicleType: 'car' as Asset['vehicleType'],
  vehicleBrand: '',
  vehicleModel: '',
  vehicleYear: new Date().getFullYear(),
  vehicleRegistrationNo: '',
  mileageKm: 0,
  // Electronics
  brand: '',
  model: '',
  serialNumber: '',
  warrantyExpiryDate: '' as string,
  // Jewelry
  itemType: 'set' as Asset['itemType'],
  material: '',
  weightGrams: 0,
  purity: '',
});

// ============ Valuation Form ============
const valuationForm = ref({
  date: new Date().toISOString().split('T')[0],
  value: 0,
  note: '',
});

// ============ Edit Form ============
const editForm = ref({
  currentValue: 0,
  currentCondition: 'good' as AssetCondition,
  status: 'owned' as AssetStatus,
  depreciationMethod: 'none' as DepreciationMethod,
  usefulLifeYears: 0,
  salvageValue: 0,
  ownershipPercentage: 100,
  loanAgainstAsset: false,
  currency: 'BDT' as Currency,
  notes: '',
  location: '',
});

// ============ Actions ============
function openDetail(asset: Asset) {
  selectedAsset.value = asset;
  showDetailModal.value = true;
}

function openAddModal() {
  const cat = activeTab.value !== 'all' ? (activeTab.value as AssetCategory) : 'real_estate';
  resetAddForm(cat);
  showAddModal.value = true;
}

function resetAddForm(category?: AssetCategory) {
  addForm.value = {
    name: '', category: category || 'real_estate', description: '',
    purchaseDate: new Date().toISOString().split('T')[0],
    purchasePrice: 0, purchaseFrom: '', currentValue: 0,
    currentCondition: 'good', location: '',
    depreciationMethod: 'none', usefulLifeYears: 0, salvageValue: 0,
    status: 'owned', ownershipPercentage: 100, loanAgainstAsset: false,
    currency: 'BDT', notes: '',
    propertyType: 'apartment', propertyAddress: '', sizeSqft: 0, floorNumber: '',
    vehicleType: 'car', vehicleBrand: '', vehicleModel: '', vehicleYear: new Date().getFullYear(),
    vehicleRegistrationNo: '', mileageKm: 0,
    brand: '', model: '', serialNumber: '', warrantyExpiryDate: '',
    itemType: 'set', material: '', weightGrams: 0, purity: '',
  };
}

function submitAddAsset() {
  const form = addForm.value;
  const data: any = {
    name: form.name,
    category: form.category,
    description: form.description || undefined,
    purchaseDate: new Date(form.purchaseDate).toISOString(),
    purchasePrice: form.purchasePrice,
    purchaseFrom: form.purchaseFrom || undefined,
    currentValue: form.currentValue || form.purchasePrice,
    currentCondition: form.currentCondition,
    location: form.location || undefined,
    depreciationMethod: form.depreciationMethod,
    usefulLifeYears: form.usefulLifeYears || undefined,
    salvageValue: form.salvageValue || undefined,
    status: form.status,
    ownershipPercentage: form.ownershipPercentage || undefined,
    loanAgainstAsset: form.loanAgainstAsset || undefined,
    currency: form.currency,
    notes: form.notes || undefined,
  };

  if (form.category === 'real_estate') {
    data.propertyType = form.propertyType || undefined;
    data.propertyAddress = form.propertyAddress || undefined;
    data.sizeSqft = form.sizeSqft || undefined;
    data.floorNumber = form.floorNumber || undefined;
  }
  if (form.category === 'vehicle') {
    data.vehicleType = form.vehicleType || undefined;
    data.vehicleBrand = form.vehicleBrand || undefined;
    data.vehicleModel = form.vehicleModel || undefined;
    data.vehicleYear = form.vehicleYear || undefined;
    data.vehicleRegistrationNo = form.vehicleRegistrationNo || undefined;
    data.mileageKm = form.mileageKm || undefined;
  }
  if (form.category === 'electronics' || form.category === 'equipment') {
    data.brand = form.brand || undefined;
    data.model = form.model || undefined;
    data.serialNumber = form.serialNumber || undefined;
    data.warrantyExpiryDate = form.warrantyExpiryDate ? new Date(form.warrantyExpiryDate).toISOString() : undefined;
  }
  if (form.category === 'jewelry') {
    data.itemType = form.itemType || undefined;
    data.material = form.material || undefined;
    data.weightGrams = form.weightGrams || undefined;
    data.purity = form.purity || undefined;
  }

  assetStore.addAsset(data);
  showAddModal.value = false;
}

function openValuationModal(asset: Asset) {
  selectedAsset.value = asset;
  valuationForm.value = {
    date: new Date().toISOString().split('T')[0],
    value: asset.currentValue,
    note: '',
  };
  showValuationModal.value = true;
}

function submitValuation() {
  if (!selectedAsset.value) return;
  assetStore.addValuation(selectedAsset.value.id, {
    date: new Date(valuationForm.value.date).toISOString().split('T')[0],
    value: valuationForm.value.value,
    note: valuationForm.value.note || undefined,
  });
  showValuationModal.value = false;
  selectedAsset.value = assetStore.getAssetById(selectedAsset.value.id) || null;
}

function openEditModal(asset: Asset) {
  selectedAsset.value = asset;
  editForm.value = {
    currentValue: asset.currentValue,
    currentCondition: asset.currentCondition,
    status: asset.status,
    depreciationMethod: asset.depreciationMethod,
    usefulLifeYears: asset.usefulLifeYears || 0,
    salvageValue: asset.salvageValue || 0,
    ownershipPercentage: asset.ownershipPercentage || 100,
    loanAgainstAsset: asset.loanAgainstAsset || false,
    currency: asset.currency || 'BDT',
    notes: asset.notes || '',
    location: asset.location || '',
  };
  showDetailModal.value = false;
  showEditModal.value = true;
}

function submitEdit() {
  if (!selectedAsset.value) return;
  assetStore.updateAsset(selectedAsset.value.id, {
    currentValue: editForm.value.currentValue,
    currentCondition: editForm.value.currentCondition,
    status: editForm.value.status,
    depreciationMethod: editForm.value.depreciationMethod,
    usefulLifeYears: editForm.value.usefulLifeYears || undefined,
    salvageValue: editForm.value.salvageValue || undefined,
    ownershipPercentage: editForm.value.ownershipPercentage || undefined,
    loanAgainstAsset: editForm.value.loanAgainstAsset || undefined,
    currency: editForm.value.currency,
    notes: editForm.value.notes || undefined,
    location: editForm.value.location || undefined,
  });
  showEditModal.value = false;
  selectedAsset.value = assetStore.getAssetById(selectedAsset.value.id) || null;
}

function confirmDelete() {
  if (!selectedAsset.value) return;
  assetStore.deleteAsset(selectedAsset.value.id);
  showDeleteConfirm.value = false;
  showDetailModal.value = false;
  selectedAsset.value = null;
}
</script>

<template>
  <div class="animate-fade-in space-y-6">
    <!-- Page Header -->
    <PageHeader title="Asset Register" subtitle="Track all your physical assets — property, vehicles, electronics, jewelry, and more">
      <template #actions>
        <button class="btn-primary" @click="openAddModal">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/></svg>
          {{ addButtonText }}
        </button>
      </template>
    </PageHeader>

    <!-- Tabs -->
    <Tabs :tabs="tabItems" :active-tab="activeTab" @update:active-tab="(k: string) => activeTab = k as TabKey" />

    <!-- Summary Stats -->
    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      <StatCard title="Total Asset Value" :value="fmtCur(assetStore.totalCurrentValue)" icon="📊" color="primary" />
      <StatCard title="Total Purchase Cost" :value="fmtCur(assetStore.totalPurchasePrice)" icon="💳" color="info" />
      <StatCard title="Net Appreciation" :value="fmtCur(assetStore.totalAppreciation)" icon="📈" :color="assetStore.totalAppreciation >= 0 ? 'accent' : 'danger'" />
      <StatCard title="Total Assets" :value="String(assetStore.totalAssetCount)" icon="📦" color="neutral" />
    </div>

    <!-- Empty State -->
    <div v-if="filteredAssets.length === 0">
      <EmptyState
        :icon="activeTab === 'all' ? '📦' : (categoryConfig[activeTab as AssetCategory]?.icon || '📦')"
        :title="activeTab === 'all' ? 'No assets registered yet' : `No ${categoryConfig[activeTab as AssetCategory]?.label || ''} assets`"
        description="Add your first asset to start tracking your wealth."
      >
        <template #action>
          <button class="btn-primary" @click="openAddModal">{{ addButtonText }}</button>
        </template>
      </EmptyState>
    </div>

    <!-- Asset Cards Grid -->
    <div v-else class="grid grid-cols-1 lg:grid-cols-2 gap-4">
      <div
        v-for="asset in filteredAssets"
        :key="asset.id"
        class="card-hover p-5 cursor-pointer animate-fade-in"
        @click="openDetail(asset)"
      >
        <!-- Header -->
        <div class="flex items-start justify-between mb-4">
          <div class="flex items-center gap-3">
            <div class="w-11 h-11 rounded-lg flex items-center justify-center text-xl" :class="{
              'bg-primary-100 dark:bg-primary-500/20': categoryConfig[asset.category].color === 'primary',
              'bg-accent-100 dark:bg-accent-500/20': categoryConfig[asset.category].color === 'success',
              'bg-warning-50 dark:bg-warning-500/20': categoryConfig[asset.category].color === 'warning',
              'bg-info-100 dark:bg-info-500/20': categoryConfig[asset.category].color === 'info',
              'bg-danger-100 dark:bg-danger-500/20': categoryConfig[asset.category].color === 'danger',
              'bg-surface-100 dark:bg-surface-700': categoryConfig[asset.category].color === 'neutral',
            }">
              {{ categoryConfig[asset.category].icon }}
            </div>
            <div>
              <h3 class="font-semibold text-surface-900 dark:text-white">{{ asset.name }}</h3>
              <p class="text-sm text-surface-500 dark:text-surface-400">
                <span v-if="asset.brand || asset.vehicleBrand">{{ asset.brand || asset.vehicleBrand }} · </span>
                {{ categoryConfig[asset.category].label }}
              </p>
            </div>
          </div>
          <div class="flex items-center gap-2">
            <Badge v-if="asset.loanAgainstAsset" variant="warning" class="text-xs">Loan</Badge>
            <Badge :variant="statusConfig[asset.status].variant">{{ statusConfig[asset.status].label }}</Badge>
          </div>
        </div>

        <!-- Key Metrics -->
        <div class="grid grid-cols-3 gap-3 mb-4">
          <div>
            <p class="text-xs text-surface-500 dark:text-surface-400">Purchase Price</p>
            <p class="text-sm font-semibold text-surface-900 dark:text-white tabular-nums">{{ fmtCur(asset.purchasePrice, asset.currency) }}</p>
          </div>
          <div>
            <p class="text-xs text-surface-500 dark:text-surface-400">Current Value</p>
            <p class="text-sm font-semibold tabular-nums" :class="isAppreciating(asset) ? 'text-accent-600 dark:text-accent-400' : 'text-danger-500'">
              {{ fmtCur(asset.currentValue, asset.currency) }}
            </p>
          </div>
          <div>
            <p class="text-xs text-surface-500 dark:text-surface-400">Condition</p>
            <Badge :variant="conditionConfig[asset.currentCondition].variant" class="text-xs">
              {{ conditionConfig[asset.currentCondition].label }}
            </Badge>
          </div>
        </div>

        <!-- Appreciation Progress -->
        <div class="mb-4">
          <div class="flex items-center justify-between mb-1">
            <span class="text-xs text-surface-500 dark:text-surface-400">
              {{ isAppreciating(asset) ? 'Appreciation' : 'Depreciation' }}
            </span>
            <span class="text-xs font-medium tabular-nums" :class="isAppreciating(asset) ? 'text-accent-600 dark:text-accent-400' : 'text-danger-500'">
              {{ isAppreciating(asset) ? '+' : '' }}{{ appreciationPct(asset).toFixed(1) }}%
            </span>
          </div>
          <ProgressBar
            :value="Math.max(0, asset.currentValue)"
            :max="Math.max(1, asset.purchasePrice)"
            :color="isAppreciating(asset) ? 'accent' : 'danger'"
            size="sm"
          />
        </div>

        <!-- Bottom Info Bar -->
        <div class="flex items-center justify-between bg-surface-50 dark:bg-surface-700/50 rounded-lg px-3 py-2">
          <span class="text-xs text-surface-500 dark:text-surface-400">
            <span v-if="asset.sizeSqft">{{ asset.sizeSqft.toLocaleString() }} sqft · </span>
            <span v-else-if="asset.weightGrams">{{ asset.weightGrams }}g · </span>
            <span v-else-if="asset.mileageKm">{{ asset.mileageKm.toLocaleString() }} km · </span>
            {{ ageYears(asset).toFixed(1) }} years ago
          </span>
          <span v-if="asset.ownershipPercentage && asset.ownershipPercentage < 100" class="text-xs text-surface-500 dark:text-surface-400">
            {{ asset.ownershipPercentage }}% owned
          </span>
          <span v-else class="text-sm font-medium tabular-nums" :class="isAppreciating(asset) ? 'text-accent-600 dark:text-accent-400' : 'text-danger-500'">
            {{ isAppreciating(asset) ? '▲' : '▼' }}
            {{ fmtCur(Math.abs(asset.currentValue - asset.purchasePrice), asset.currency) }}
          </span>
        </div>
      </div>
    </div>

    <!-- ======================== DETAIL MODAL ======================== -->
    <Modal v-if="selectedAsset" :is-open="showDetailModal" title="Asset Details" size="xl" @close="showDetailModal = false">
      <div class="space-y-6" v-if="selectedAsset">
        <!-- Header -->
        <div class="flex items-center gap-4 pb-4 border-b border-surface-200 dark:border-surface-700">
          <div class="w-14 h-14 rounded-xl flex items-center justify-center text-2xl" :class="{
            'bg-primary-100 dark:bg-primary-500/20': categoryConfig[selectedAsset.category].color === 'primary',
            'bg-accent-100 dark:bg-accent-500/20': categoryConfig[selectedAsset.category].color === 'success',
            'bg-warning-50 dark:bg-warning-500/20': categoryConfig[selectedAsset.category].color === 'warning',
            'bg-info-100 dark:bg-info-500/20': categoryConfig[selectedAsset.category].color === 'info',
            'bg-danger-100 dark:bg-danger-500/20': categoryConfig[selectedAsset.category].color === 'danger',
            'bg-surface-100 dark:bg-surface-700': categoryConfig[selectedAsset.category].color === 'neutral',
          }">
            {{ categoryConfig[selectedAsset.category].icon }}
          </div>
          <div class="flex-1">
            <h3 class="text-xl font-bold text-surface-900 dark:text-white">{{ selectedAsset.name }}</h3>
            <p class="text-surface-500 dark:text-surface-400">
              {{ selectedAsset.description || categoryConfig[selectedAsset.category].label }}
            </p>
          </div>
          <div class="flex items-center gap-2">
            <Badge v-if="selectedAsset.loanAgainstAsset" variant="warning">Loan Against</Badge>
            <Badge :variant="statusConfig[selectedAsset.status].variant">{{ statusConfig[selectedAsset.status].label }}</Badge>
          </div>
        </div>

        <!-- Key Metrics Grid -->
        <div class="grid grid-cols-2 md:grid-cols-4 gap-3">
          <div class="bg-surface-50 dark:bg-surface-700/50 rounded-lg p-3">
            <p class="text-xs text-surface-400 mb-1">Purchase Price</p>
            <p class="font-semibold text-surface-900 dark:text-white tabular-nums">{{ fmtCur(selectedAsset.purchasePrice, selectedAsset.currency) }}</p>
          </div>
          <div class="bg-surface-50 dark:bg-surface-700/50 rounded-lg p-3">
            <p class="text-xs text-surface-400 mb-1">Current Value</p>
            <p class="font-semibold tabular-nums" :class="isAppreciating(selectedAsset) ? 'text-accent-600 dark:text-accent-400' : 'text-danger-500'">
              {{ fmtCur(selectedAsset.currentValue, selectedAsset.currency) }}
            </p>
          </div>
          <div class="bg-surface-50 dark:bg-surface-700/50 rounded-lg p-3">
            <p class="text-xs text-surface-400 mb-1">Appreciation</p>
            <p class="font-semibold tabular-nums" :class="isAppreciating(selectedAsset) ? 'text-accent-600 dark:text-accent-400' : 'text-danger-500'">
              {{ isAppreciating(selectedAsset) ? '+' : '' }}{{ fmtCur(selectedAsset.currentValue - selectedAsset.purchasePrice, selectedAsset.currency) }}
            </p>
          </div>
          <div class="bg-surface-50 dark:bg-surface-700/50 rounded-lg p-3">
            <p class="text-xs text-surface-400 mb-1">Book Value</p>
            <p class="font-semibold text-surface-900 dark:text-white tabular-nums">{{ fmtCur(assetStore.calculateBookValue(selectedAsset) || selectedAsset.currentValue, selectedAsset.currency) }}</p>
          </div>
        </div>

        <!-- General Info -->
        <div class="bg-surface-50 dark:bg-surface-900 rounded-lg p-4">
          <h4 class="text-sm font-semibold text-surface-700 dark:text-surface-300 mb-3">General Information</h4>
          <div class="grid grid-cols-2 md:grid-cols-3 gap-3 text-sm">
            <div>
              <span class="text-xs text-surface-400">Purchase Date</span>
              <p class="font-medium text-surface-900 dark:text-white">{{ formatDate(selectedAsset.purchaseDate, 'long') }}</p>
            </div>
            <div v-if="selectedAsset.purchaseFrom">
              <span class="text-xs text-surface-400">Purchased From</span>
              <p class="font-medium text-surface-900 dark:text-white">{{ selectedAsset.purchaseFrom }}</p>
            </div>
            <div>
              <span class="text-xs text-surface-400">Condition</span>
              <Badge :variant="conditionConfig[selectedAsset.currentCondition].variant">{{ conditionConfig[selectedAsset.currentCondition].label }}</Badge>
            </div>
            <div v-if="selectedAsset.location">
              <span class="text-xs text-surface-400">Location</span>
              <p class="font-medium text-surface-900 dark:text-white text-xs">{{ selectedAsset.location }}</p>
            </div>
            <div v-if="selectedAsset.ownershipPercentage && selectedAsset.ownershipPercentage < 100">
              <span class="text-xs text-surface-400">Ownership</span>
              <p class="font-medium text-surface-900 dark:text-white">{{ selectedAsset.ownershipPercentage }}%</p>
            </div>
            <div v-if="selectedAsset.coOwners">
              <span class="text-xs text-surface-400">Co-Owners</span>
              <p class="font-medium text-surface-900 dark:text-white text-xs">{{ selectedAsset.coOwners }}</p>
            </div>
            <div>
              <span class="text-xs text-surface-400">Depreciation</span>
              <p class="font-medium text-surface-900 dark:text-white">{{ depLabels[selectedAsset.depreciationMethod] }}</p>
            </div>
            <div v-if="selectedAsset.usefulLifeYears">
              <span class="text-xs text-surface-400">Useful Life</span>
              <p class="font-medium text-surface-900 dark:text-white">{{ selectedAsset.usefulLifeYears }} years</p>
            </div>
            <div v-if="selectedAsset.salvageValue">
              <span class="text-xs text-surface-400">Salvage Value</span>
              <p class="font-medium text-surface-900 dark:text-white tabular-nums">{{ fmtCur(selectedAsset.salvageValue, selectedAsset.currency) }}</p>
            </div>
          </div>
        </div>

        <!-- Real Estate Details -->
        <div v-if="selectedAsset.category === 'real_estate'" class="bg-surface-50 dark:bg-surface-900 rounded-lg p-4">
          <h4 class="text-sm font-semibold text-surface-700 dark:text-surface-300 mb-3">Real Estate Details</h4>
          <div class="grid grid-cols-2 md:grid-cols-3 gap-3 text-sm">
            <div v-if="selectedAsset.propertyType">
              <span class="text-xs text-surface-400">Property Type</span>
              <p class="font-medium text-surface-900 dark:text-white capitalize">{{ selectedAsset.propertyType }}</p>
            </div>
            <div v-if="selectedAsset.propertyAddress">
              <span class="text-xs text-surface-400">Address</span>
              <p class="font-medium text-surface-900 dark:text-white text-xs">{{ selectedAsset.propertyAddress }}</p>
            </div>
            <div v-if="selectedAsset.sizeSqft">
              <span class="text-xs text-surface-400">Size</span>
              <p class="font-medium text-surface-900 dark:text-white tabular-nums">{{ selectedAsset.sizeSqft.toLocaleString() }} sqft</p>
            </div>
            <div v-if="selectedAsset.floorNumber">
              <span class="text-xs text-surface-400">Floor</span>
              <p class="font-medium text-surface-900 dark:text-white">{{ selectedAsset.floorNumber }}</p>
            </div>
            <div v-if="selectedAsset.registrationNumber">
              <span class="text-xs text-surface-400">Registration No.</span>
              <p class="font-medium text-surface-900 dark:text-white text-xs">{{ selectedAsset.registrationNumber }}</p>
            </div>
            <div v-if="selectedAsset.khatianNumber">
              <span class="text-xs text-surface-400">Khatian No.</span>
              <p class="font-medium text-surface-900 dark:text-white">{{ selectedAsset.khatianNumber }}</p>
            </div>
            <div v-if="selectedAsset.registrationDate">
              <span class="text-xs text-surface-400">Registration Date</span>
              <p class="font-medium text-surface-900 dark:text-white">{{ formatDate(selectedAsset.registrationDate, 'long') }}</p>
            </div>
          </div>
        </div>

        <!-- Vehicle Details -->
        <div v-if="selectedAsset.category === 'vehicle'" class="bg-surface-50 dark:bg-surface-900 rounded-lg p-4">
          <h4 class="text-sm font-semibold text-surface-700 dark:text-surface-300 mb-3">Vehicle Details</h4>
          <div class="grid grid-cols-2 md:grid-cols-3 gap-3 text-sm">
            <div v-if="selectedAsset.vehicleBrand || selectedAsset.vehicleModel">
              <span class="text-xs text-surface-400">Make / Model</span>
              <p class="font-medium text-surface-900 dark:text-white">{{ [selectedAsset.vehicleBrand, selectedAsset.vehicleModel].filter(Boolean).join(' ') }}</p>
            </div>
            <div v-if="selectedAsset.vehicleYear">
              <span class="text-xs text-surface-400">Year</span>
              <p class="font-medium text-surface-900 dark:text-white">{{ selectedAsset.vehicleYear }}</p>
            </div>
            <div v-if="selectedAsset.mileageKm">
              <span class="text-xs text-surface-400">Mileage</span>
              <p class="font-medium text-surface-900 dark:text-white tabular-nums">{{ selectedAsset.mileageKm.toLocaleString() }} km</p>
            </div>
            <div v-if="selectedAsset.vehicleRegistrationNo">
              <span class="text-xs text-surface-400">Registration</span>
              <p class="font-medium text-surface-900 dark:text-white">{{ selectedAsset.vehicleRegistrationNo }}</p>
            </div>
            <div v-if="selectedAsset.engineNo">
              <span class="text-xs text-surface-400">Engine No.</span>
              <p class="font-medium text-surface-900 dark:text-white text-xs">{{ selectedAsset.engineNo }}</p>
            </div>
            <div v-if="selectedAsset.chassisNo">
              <span class="text-xs text-surface-400">Chassis No.</span>
              <p class="font-medium text-surface-900 dark:text-white text-xs">{{ selectedAsset.chassisNo }}</p>
            </div>
          </div>
        </div>

        <!-- Electronics Details -->
        <div v-if="selectedAsset.category === 'electronics' || selectedAsset.category === 'equipment'" class="bg-surface-50 dark:bg-surface-900 rounded-lg p-4">
          <h4 class="text-sm font-semibold text-surface-700 dark:text-surface-300 mb-3">Electronics Details</h4>
          <div class="grid grid-cols-2 md:grid-cols-3 gap-3 text-sm">
            <div v-if="selectedAsset.brand || selectedAsset.model">
              <span class="text-xs text-surface-400">Brand / Model</span>
              <p class="font-medium text-surface-900 dark:text-white">{{ [selectedAsset.brand, selectedAsset.model].filter(Boolean).join(' ') }}</p>
            </div>
            <div v-if="selectedAsset.serialNumber">
              <span class="text-xs text-surface-400">Serial Number</span>
              <p class="font-medium text-surface-900 dark:text-white text-xs">{{ selectedAsset.serialNumber }}</p>
            </div>
            <div v-if="selectedAsset.warrantyExpiryDate">
              <span class="text-xs text-surface-400">Warranty Until</span>
              <p class="font-medium" :class="new Date(selectedAsset.warrantyExpiryDate) > new Date() ? 'text-accent-600 dark:text-accent-400' : 'text-danger-500'">
                {{ formatDate(selectedAsset.warrantyExpiryDate, 'long') }}
              </p>
            </div>
          </div>
        </div>

        <!-- Jewelry Details -->
        <div v-if="selectedAsset.category === 'jewelry'" class="bg-surface-50 dark:bg-surface-900 rounded-lg p-4">
          <h4 class="text-sm font-semibold text-surface-700 dark:text-surface-300 mb-3">Jewelry Details</h4>
          <div class="grid grid-cols-2 md:grid-cols-3 gap-3 text-sm">
            <div v-if="selectedAsset.itemType">
              <span class="text-xs text-surface-400">Type</span>
              <p class="font-medium text-surface-900 dark:text-white capitalize">{{ selectedAsset.itemType }}</p>
            </div>
            <div v-if="selectedAsset.material">
              <span class="text-xs text-surface-400">Material</span>
              <p class="font-medium text-surface-900 dark:text-white">{{ selectedAsset.material }}</p>
            </div>
            <div v-if="selectedAsset.weightGrams">
              <span class="text-xs text-surface-400">Weight</span>
              <p class="font-medium text-surface-900 dark:text-white tabular-nums">{{ selectedAsset.weightGrams }}g</p>
            </div>
            <div v-if="selectedAsset.purity">
              <span class="text-xs text-surface-400">Purity</span>
              <p class="font-medium text-surface-900 dark:text-white">{{ selectedAsset.purity }}</p>
            </div>
            <div v-if="selectedAsset.weightGrams && selectedAsset.currentValue">
              <span class="text-xs text-surface-400">Price/gram</span>
              <p class="font-medium text-surface-900 dark:text-white tabular-nums">{{ fmtCur(Math.round(selectedAsset.currentValue / selectedAsset.weightGrams), selectedAsset.currency) }}/g</p>
            </div>
          </div>
        </div>

        <!-- Appreciation/Depreciation Progress -->
        <div>
          <div class="flex items-center justify-between mb-1">
            <span class="text-sm font-medium text-surface-700 dark:text-surface-300">
              {{ isAppreciating(selectedAsset) ? 'Appreciation' : 'Depreciation' }}
            </span>
            <span class="text-sm font-medium tabular-nums" :class="isAppreciating(selectedAsset) ? 'text-accent-600 dark:text-accent-400' : 'text-danger-500'">
              {{ isAppreciating(selectedAsset) ? '+' : '' }}{{ appreciationPct(selectedAsset).toFixed(1) }}%
              ({{ fmtCur(Math.abs(selectedAsset.currentValue - selectedAsset.purchasePrice), selectedAsset.currency) }})
            </span>
          </div>
          <ProgressBar
            :value="Math.max(0, selectedAsset.currentValue)"
            :max="Math.max(1, selectedAsset.purchasePrice)"
            :color="isAppreciating(selectedAsset) ? 'accent' : 'danger'"
            size="md"
          />
        </div>

        <!-- Valuation History -->
        <div>
          <h4 class="text-sm font-semibold text-surface-700 dark:text-surface-300 mb-3">Valuation History</h4>
          <div class="max-h-56 overflow-y-auto">
            <DataTable
              :columns="valuationColumns"
              :data="[...selectedAsset.valuations].reverse()"
              empty-message="No valuations recorded"
            >
              <template #cell-date="{ value }">
                {{ formatDate(value, 'short') }}
              </template>
              <template #cell-value="{ value }">
                <span class="tabular-nums text-surface-900 dark:text-white font-medium">{{ fmtCur(value, selectedAsset?.currency) }}</span>
              </template>
              <template #cell-note="{ value }">
                <span class="text-xs text-surface-500 dark:text-surface-400">{{ value || '—' }}</span>
              </template>
            </DataTable>
          </div>
        </div>

        <!-- Notes -->
        <div v-if="selectedAsset.notes">
          <h4 class="text-sm font-semibold text-surface-700 dark:text-surface-300 mb-1">Notes</h4>
          <p class="text-sm text-surface-600 dark:text-surface-400">{{ selectedAsset.notes }}</p>
        </div>

        <!-- Actions -->
        <div class="flex flex-wrap gap-3 pt-2 border-t border-surface-200 dark:border-surface-700">
          <button class="btn-primary" @click="openValuationModal(selectedAsset!)">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"/></svg>
            Update Valuation
          </button>
          <button class="btn-secondary" @click="openEditModal(selectedAsset!)">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"/></svg>
            Edit
          </button>
          <button class="btn-danger" @click="showDeleteConfirm = true">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/></svg>
            Delete
          </button>
        </div>
      </div>
    </Modal>

    <!-- ======================== ADD ASSET MODAL ======================== -->
    <Modal :is-open="showAddModal" title="Add Asset" size="xl" @close="showAddModal = false">
      <div class="space-y-5">
        <!-- Basic Details -->
        <div>
          <h4 class="text-sm font-semibold text-surface-900 dark:text-white mb-3 flex items-center gap-2">
            <span>{{ categoryConfig[addForm.category].icon }}</span> Basic Details
          </h4>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label class="field-label">Asset Name</label>
              <input v-model="addForm.name" type="text" class="input-field" placeholder="e.g., Dhanmondi Apartment" />
            </div>
            <div>
              <label class="field-label">Category</label>
              <select v-model="addForm.category" class="input-field">
                <option value="real_estate">🏢 Real Estate</option>
                <option value="vehicle">🚗 Vehicle</option>
                <option value="electronics">💻 Electronics</option>
                <option value="furniture">🪑 Furniture</option>
                <option value="jewelry">💎 Jewelry</option>
                <option value="equipment">🔧 Equipment</option>
                <option value="art">🎨 Art & Collectibles</option>
                <option value="other">📦 Other</option>
              </select>
            </div>
            <div class="md:col-span-2">
              <label class="field-label">Description</label>
              <input v-model="addForm.description" type="text" class="input-field" placeholder="Brief description..." />
            </div>
          </div>
        </div>

        <!-- Purchase & Value -->
        <div>
          <h4 class="text-sm font-semibold text-surface-900 dark:text-white mb-3">Purchase & Value</h4>
          <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label class="field-label">Purchase Price (৳)</label>
              <input v-model.number="addForm.purchasePrice" type="number" class="input-field" placeholder="0" min="0" />
            </div>
            <div>
              <label class="field-label">Current Value (৳)</label>
              <input v-model.number="addForm.currentValue" type="number" class="input-field" placeholder="0" min="0" />
            </div>
            <div>
              <label class="field-label">Purchase Date</label>
              <input v-model="addForm.purchaseDate" type="date" class="input-field" />
            </div>
            <div>
              <label class="field-label">Purchased From</label>
              <input v-model="addForm.purchaseFrom" type="text" class="input-field" placeholder="e.g., Rangs Properties" />
            </div>
            <div>
              <label class="field-label">Condition</label>
              <select v-model="addForm.currentCondition" class="input-field">
                <option value="excellent">Excellent</option>
                <option value="good">Good</option>
                <option value="fair">Fair</option>
                <option value="poor">Poor</option>
                <option value="damaged">Damaged</option>
              </select>
            </div>
            <div>
              <label class="field-label">Location</label>
              <input v-model="addForm.location" type="text" class="input-field" placeholder="e.g., Home — Dhanmondi" />
            </div>
          </div>
        </div>

        <!-- Depreciation -->
        <div>
          <h4 class="text-sm font-semibold text-surface-900 dark:text-white mb-3">Depreciation</h4>
          <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div>
              <label class="field-label">Method</label>
              <select v-model="addForm.depreciationMethod" class="input-field">
                <option value="none">None (Appreciating)</option>
                <option value="straight_line">Straight Line</option>
                <option value="declining_balance">Declining Balance</option>
              </select>
            </div>
            <div v-if="addForm.depreciationMethod !== 'none'">
              <label class="field-label">Useful Life (years)</label>
              <input v-model.number="addForm.usefulLifeYears" type="number" class="input-field" placeholder="e.g., 10" min="1" />
            </div>
            <div v-if="addForm.depreciationMethod !== 'none'">
              <label class="field-label">Salvage Value (৳)</label>
              <input v-model.number="addForm.salvageValue" type="number" class="input-field" placeholder="0" min="0" />
            </div>
          </div>
        </div>

        <!-- Ownership -->
        <div>
          <h4 class="text-sm font-semibold text-surface-900 dark:text-white mb-3">Ownership</h4>
          <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label class="field-label">Ownership %</label>
              <input v-model.number="addForm.ownershipPercentage" type="number" class="input-field" placeholder="100" min="1" max="100" />
            </div>
            <div class="flex items-end">
              <label class="flex items-center gap-2 cursor-pointer py-2">
                <input type="checkbox" v-model="addForm.loanAgainstAsset" class="rounded border-surface-300" />
                <span class="text-sm text-surface-700 dark:text-surface-300">Loan/Mortgage against this asset</span>
              </label>
            </div>
            <div>
              <label class="field-label">Status</label>
              <select v-model="addForm.status" class="input-field">
                <option value="owned">Owned</option>
                <option value="rented">Rented</option>
                <option value="leased">Leased</option>
                <option value="sold">Sold</option>
                <option value="gifted">Gifted</option>
              </select>
            </div>
          </div>
        </div>

        <!-- Real Estate Fields -->
        <div v-if="addForm.category === 'real_estate'">
          <h4 class="text-sm font-semibold text-surface-900 dark:text-white mb-3">🏢 Real Estate Details</h4>
          <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label class="field-label">Property Type</label>
              <select v-model="addForm.propertyType" class="input-field">
                <option value="apartment">Apartment</option>
                <option value="house">House</option>
                <option value="land">Land</option>
                <option value="commercial">Commercial</option>
                <option value="condo">Condo</option>
                <option value="plot">Plot</option>
              </select>
            </div>
            <div>
              <label class="field-label">Address</label>
              <input v-model="addForm.propertyAddress" type="text" class="input-field" placeholder="e.g., Road #8, Dhanmondi" />
            </div>
            <div>
              <label class="field-label">Size (sqft)</label>
              <input v-model.number="addForm.sizeSqft" type="number" class="input-field" placeholder="0" min="0" />
            </div>
            <div>
              <label class="field-label">Floor</label>
              <input v-model="addForm.floorNumber" type="text" class="input-field" placeholder="e.g., 7th" />
            </div>
          </div>
        </div>

        <!-- Vehicle Fields -->
        <div v-if="addForm.category === 'vehicle'">
          <h4 class="text-sm font-semibold text-surface-900 dark:text-white mb-3">🚗 Vehicle Details</h4>
          <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label class="field-label">Type</label>
              <select v-model="addForm.vehicleType" class="input-field">
                <option value="car">Car</option>
                <option value="motorcycle">Motorcycle</option>
                <option value="bus">Bus</option>
                <option value="truck">Truck</option>
                <option value="bicycle">Bicycle</option>
                <option value="other">Other</option>
              </select>
            </div>
            <div>
              <label class="field-label">Brand</label>
              <input v-model="addForm.vehicleBrand" type="text" class="input-field" placeholder="e.g., Toyota" />
            </div>
            <div>
              <label class="field-label">Model</label>
              <input v-model="addForm.vehicleModel" type="text" class="input-field" placeholder="e.g., Corolla X 1.6" />
            </div>
            <div>
              <label class="field-label">Year</label>
              <input v-model.number="addForm.vehicleYear" type="number" class="input-field" :placeholder="String(new Date().getFullYear())" />
            </div>
            <div>
              <label class="field-label">Registration No.</label>
              <input v-model="addForm.vehicleRegistrationNo" type="text" class="input-field" placeholder="e.g., Dhaka Metro Ga-45-8921" />
            </div>
            <div>
              <label class="field-label">Mileage (km)</label>
              <input v-model.number="addForm.mileageKm" type="number" class="input-field" placeholder="0" min="0" />
            </div>
          </div>
        </div>

        <!-- Electronics / Equipment Fields -->
        <div v-if="addForm.category === 'electronics' || addForm.category === 'equipment'">
          <h4 class="text-sm font-semibold text-surface-900 dark:text-white mb-3">💻 Product Details</h4>
          <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label class="field-label">Brand</label>
              <input v-model="addForm.brand" type="text" class="input-field" placeholder="e.g., Apple" />
            </div>
            <div>
              <label class="field-label">Model</label>
              <input v-model="addForm.model" type="text" class="input-field" placeholder="e.g., MacBook Pro 16-inch M3" />
            </div>
            <div>
              <label class="field-label">Serial Number</label>
              <input v-model="addForm.serialNumber" type="text" class="input-field" placeholder="e.g., C02ZW1XXMD6N" />
            </div>
            <div>
              <label class="field-label">Warranty Expiry</label>
              <input v-model="addForm.warrantyExpiryDate" type="date" class="input-field" />
            </div>
          </div>
        </div>

        <!-- Jewelry Fields -->
        <div v-if="addForm.category === 'jewelry'">
          <h4 class="text-sm font-semibold text-surface-900 dark:text-white mb-3">💎 Jewelry Details</h4>
          <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label class="field-label">Type</label>
              <select v-model="addForm.itemType" class="input-field">
                <option value="necklace">Necklace</option>
                <option value="ring">Ring</option>
                <option value="earring">Earring</option>
                <option value="bangle">Bangle</option>
                <option value="bracelet">Bracelet</option>
                <option value="chain">Chain</option>
                <option value="pendant">Pendant</option>
                <option value="watch">Watch</option>
                <option value="set">Set</option>
                <option value="other">Other</option>
              </select>
            </div>
            <div>
              <label class="field-label">Material</label>
              <input v-model="addForm.material" type="text" class="input-field" placeholder="e.g., 22K Gold" />
            </div>
            <div>
              <label class="field-label">Weight (grams)</label>
              <input v-model.number="addForm.weightGrams" type="number" class="input-field" placeholder="0" min="0" />
            </div>
            <div>
              <label class="field-label">Purity</label>
              <input v-model="addForm.purity" type="text" class="input-field" placeholder="e.g., 22K" />
            </div>
          </div>
        </div>

        <!-- Notes -->
        <div>
          <label class="field-label">Notes</label>
          <textarea v-model="addForm.notes" class="input-field" rows="2" placeholder="Any additional notes..."></textarea>
        </div>

        <!-- Submit -->
        <div class="flex items-center gap-3 justify-end pt-2 border-t border-surface-200 dark:border-surface-700">
          <button class="btn-secondary" @click="showAddModal = false">Cancel</button>
          <button class="btn-primary" @click="submitAddAsset" :disabled="!addForm.name || addForm.purchasePrice <= 0">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/></svg>
            Add Asset
          </button>
        </div>
      </div>
    </Modal>

    <!-- ======================== VALUATION MODAL ======================== -->
    <Modal :is-open="showValuationModal" title="Update Asset Valuation" size="md" @close="showValuationModal = false">
      <div class="space-y-4">
        <div class="bg-surface-50 dark:bg-surface-700/50 rounded-lg p-3 text-sm">
          <span class="text-surface-500 dark:text-surface-400">Asset: </span>
          <span class="font-medium text-surface-900 dark:text-white">{{ selectedAsset?.name }}</span>
          <span class="text-surface-400 ml-2">· Current: {{ fmtCur(selectedAsset?.currentValue || 0, selectedAsset?.currency) }}</span>
        </div>
        <div>
          <label class="field-label">New Value (৳)</label>
          <input v-model.number="valuationForm.value" type="number" class="input-field" placeholder="0" min="0" />
        </div>
        <div>
          <label class="field-label">Valuation Date</label>
          <input v-model="valuationForm.date" type="date" class="input-field" />
        </div>
        <div>
          <label class="field-label">Note</label>
          <input v-model="valuationForm.note" type="text" class="input-field" placeholder="e.g., Market assessment" />
        </div>
        <div class="flex items-center gap-3 justify-end pt-2 border-t border-surface-200 dark:border-surface-700">
          <button class="btn-secondary" @click="showValuationModal = false">Cancel</button>
          <button class="btn-primary" @click="submitValuation" :disabled="valuationForm.value <= 0">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/></svg>
            Update Value
          </button>
        </div>
      </div>
    </Modal>

    <!-- ======================== EDIT MODAL ======================== -->
    <Modal :is-open="showEditModal" title="Edit Asset" size="lg" @close="showEditModal = false">
      <div class="space-y-4">
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label class="field-label">Current Value (৳)</label>
            <input v-model.number="editForm.currentValue" type="number" class="input-field" placeholder="0" min="0" />
          </div>
          <div>
            <label class="field-label">Condition</label>
            <select v-model="editForm.currentCondition" class="input-field">
              <option value="excellent">Excellent</option>
              <option value="good">Good</option>
              <option value="fair">Fair</option>
              <option value="poor">Poor</option>
              <option value="damaged">Damaged</option>
            </select>
          </div>
          <div>
            <label class="field-label">Status</label>
            <select v-model="editForm.status" class="input-field">
              <option value="owned">Owned</option>
              <option value="rented">Rented</option>
              <option value="leased">Leased</option>
              <option value="sold">Sold</option>
              <option value="gifted">Gifted</option>
              <option value="damaged">Damaged</option>
              <option value="disposed">Disposed</option>
            </select>
          </div>
          <div>
            <label class="field-label">Depreciation Method</label>
            <select v-model="editForm.depreciationMethod" class="input-field">
              <option value="none">None (Appreciating)</option>
              <option value="straight_line">Straight Line</option>
              <option value="declining_balance">Declining Balance</option>
            </select>
          </div>
          <div v-if="editForm.depreciationMethod !== 'none'">
            <label class="field-label">Useful Life (years)</label>
            <input v-model.number="editForm.usefulLifeYears" type="number" class="input-field" placeholder="e.g., 10" min="1" />
          </div>
          <div v-if="editForm.depreciationMethod !== 'none'">
            <label class="field-label">Salvage Value (৳)</label>
            <input v-model.number="editForm.salvageValue" type="number" class="input-field" placeholder="0" min="0" />
          </div>
          <div>
            <label class="field-label">Ownership %</label>
            <input v-model.number="editForm.ownershipPercentage" type="number" class="input-field" placeholder="100" min="1" max="100" />
          </div>
          <div>
            <label class="field-label">Location</label>
            <input v-model="editForm.location" type="text" class="input-field" placeholder="e.g., Home — Dhanmondi" />
          </div>
          <div class="md:col-span-2">
            <label class="field-label">Notes</label>
            <textarea v-model="editForm.notes" class="input-field" rows="2" placeholder="Notes..."></textarea>
          </div>
        </div>
        <div class="flex items-center gap-3 justify-end pt-2 border-t border-surface-200 dark:border-surface-700">
          <button class="btn-secondary" @click="showEditModal = false">Cancel</button>
          <button class="btn-primary" @click="submitEdit">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/></svg>
            Save Changes
          </button>
        </div>
      </div>
    </Modal>

    <!-- ======================== DELETE CONFIRM ======================== -->
    <Modal :is-open="showDeleteConfirm" title="Delete Asset" size="sm" @close="showDeleteConfirm = false">
      <div class="space-y-4">
        <p class="text-sm text-surface-600 dark:text-surface-400">
          Are you sure you want to delete <strong class="text-surface-900 dark:text-white">{{ selectedAsset?.name }}</strong>?
          This action cannot be undone. All valuation history will be lost.
        </p>
        <div class="flex items-center gap-3 justify-end">
          <button class="btn-secondary" @click="showDeleteConfirm = false">Cancel</button>
          <button class="btn-danger" @click="confirmDelete">Delete Asset</button>
        </div>
      </div>
    </Modal>
  </div>
</template>
