<script setup lang="ts">
import { ref, computed } from 'vue';
import { useInsuranceStore } from '../../stores/insurance';
import { useCurrencyStore } from '../../stores/currency';
import { formatCurrency, formatDate } from '../../utils/formatters';
import { PageHeader, StatCard, Badge, Modal, DataTable, EmptyState, Tabs } from '../ui';
import type { Insurance, InsuranceCategory, InsuranceStatus, InsuranceClaimStatus, Currency } from '../../types';

const insuranceStore = useInsuranceStore();
const currencyStore = useCurrencyStore();

// ============ Tab State ============
type TabKey = 'all' | InsuranceCategory;
const activeTab = ref<TabKey>('all');
const tabItems = [
  { key: 'all', label: 'All', icon: '🛡️' },
  { key: 'life', label: 'Life', icon: '❤️' },
  { key: 'health', label: 'Health', icon: '🏥' },
  { key: 'vehicle', label: 'Vehicle', icon: '🚗' },
  { key: 'property', label: 'Property', icon: '🏠' },
  { key: 'travel', label: 'Travel', icon: '✈️' },
  { key: 'critical_illness', label: 'Critical Illness', icon: '⚕️' },
];

// ============ Modal State ============
const selectedInsurance = ref<Insurance | null>(null);
const showDetailModal = ref(false);
const showAddModal = ref(false);
const showPremiumModal = ref(false);
const showClaimModal = ref(false);
const showDeleteConfirm = ref(false);

// ============ Config ============
const categoryConfig: Record<InsuranceCategory, { label: string; icon: string; color: string }> = {
  life: { label: 'Life', icon: '❤️', color: 'danger' },
  health: { label: 'Health', icon: '🏥', color: 'success' },
  vehicle: { label: 'Vehicle', icon: '🚗', color: 'info' },
  property: { label: 'Property', icon: '🏠', color: 'warning' },
  travel: { label: 'Travel', icon: '✈️', color: 'primary' },
  critical_illness: { label: 'Critical Illness', icon: '⚕️', color: 'danger' },
  other: { label: 'Other', icon: '📋', color: 'neutral' },
};

const statusConfig: Record<InsuranceStatus, { variant: 'success' | 'danger' | 'warning' | 'info' | 'neutral'; label: string }> = {
  active: { variant: 'success', label: 'Active' },
  expired: { variant: 'neutral', label: 'Expired' },
  cancelled: { variant: 'danger', label: 'Cancelled' },
  claimed: { variant: 'info', label: 'Claimed' },
  lapsed: { variant: 'warning', label: 'Lapsed' },
  pending_renewal: { variant: 'warning', label: 'Pending Renewal' },
};

const claimStatusConfig: Record<InsuranceClaimStatus, { variant: 'success' | 'danger' | 'warning' | 'info' | 'neutral'; label: string }> = {
  pending: { variant: 'warning', label: 'Pending' },
  approved: { variant: 'info', label: 'Approved' },
  rejected: { variant: 'danger', label: 'Rejected' },
  paid: { variant: 'success', label: 'Paid' },
  in_review: { variant: 'info', label: 'In Review' },
};

const freqLabels: Record<string, string> = {
  monthly: 'Monthly',
  quarterly: 'Quarterly',
  semiannually: 'Semi-Annually',
  annually: 'Annually',
  single: 'Single',
};

// ============ Helpers ============
function fmtCur(amount: number, currency?: string): string {
  if (currency && currency !== 'BDT') {
    return currencyStore.formatWithCurrency(amount, currency as Currency);
  }
  return formatCurrency(amount, 'BDT');
}

function annualPremium(ins: Insurance): number {
  const f = ins.premiumFrequency;
  return f === 'monthly' ? ins.premiumAmount * 12
    : f === 'quarterly' ? ins.premiumAmount * 4
    : f === 'semiannually' ? ins.premiumAmount * 2
    : ins.premiumAmount;
}

function daysUntil(dateStr: string): number {
  const now = new Date();
  const target = new Date(dateStr);
  const diff = target.getTime() - now.getTime();
  return Math.ceil(diff / (1000 * 60 * 60 * 24));
}

function isExpiringSoon(ins: Insurance): boolean {
  if (!ins.expiryDate) return false;
  const days = daysUntil(ins.expiryDate);
  return days >= 0 && days <= 30;
}

function isExpired(ins: Insurance): boolean {
  if (!ins.expiryDate) return false;
  return new Date(ins.expiryDate) < new Date();
}

// ============ Filtered Insurances ============
const filteredInsurances = computed(() => {
  if (activeTab.value === 'all') return insuranceStore.insurances;
  return insuranceStore.insurancesByCategory[activeTab.value as InsuranceCategory] || [];
});

const addButtonText = computed(() => {
  if (activeTab.value === 'all') return 'Add Insurance';
  return `Add ${categoryConfig[activeTab.value as InsuranceCategory]?.label || 'Insurance'}`;
});

// ============ Payment & Claim Table Columns ============
const paymentColumns = [
  { key: 'paymentDate', label: 'Date', width: '110px' },
  { key: 'paymentNumber', label: '#', width: '50px' },
  { key: 'amount', label: 'Amount', align: 'right' as const },
  { key: 'note', label: 'Note' },
];

const claimColumns = [
  { key: 'claimDate', label: 'Date', width: '110px' },
  { key: 'claimAmount', label: 'Claimed', align: 'right' as const },
  { key: 'approvedAmount', label: 'Approved', align: 'right' as const },
  { key: 'status', label: 'Status', width: '100px' },
  { key: 'description', label: 'Description' },
];

// ============ Add Insurance Form ============
const addForm = ref({
  name: '',
  category: 'life' as InsuranceCategory,
  provider: '',
  policyNumber: '',
  coverageAmount: 0,
  premiumAmount: 0,
  premiumFrequency: 'annually' as Insurance['premiumFrequency'],
  issueDate: new Date().toISOString().split('T')[0],
  startDate: new Date().toISOString().split('T')[0],
  expiryDate: '' as string,
  maturityDate: '' as string,
  bankAccountId: '',
  currency: 'BDT' as Currency,
  notes: '',
  autoRenew: false,
  // Life specific
  policyTerm: 0,
  maturityBenefit: 0,
  riderNames: '' as string,
  // Health specific
  deductibleAmount: 0,
  copayPercent: 0,
  // Vehicle specific
  vehicleType: 'car' as Insurance['vehicleType'],
  vehicleRegistration: '',
  vehicleModel: '',
  // Property specific
  propertyType: 'apartment' as Insurance['propertyType'],
  propertyAddress: '',
  propertyValue: 0,
  // Beneficiaries
  beneficiaryName: '',
  beneficiaryRelationship: 'self' as Insurance['beneficiaries'][0]['relationship'],
  beneficiaryPercentage: 100,
});

// ============ Premium Form ============
const premiumForm = ref({
  amount: 0,
  date: new Date().toISOString().split('T')[0],
  note: '',
});

// ============ Claim Form ============
const claimForm = ref({
  claimNumber: '',
  claimDate: new Date().toISOString().split('T')[0],
  claimAmount: 0,
  description: '',
});

// ============ Actions ============
function openDetail(ins: Insurance) {
  selectedInsurance.value = ins;
  showDetailModal.value = true;
}

function openAddModal() {
  const cat = activeTab.value !== 'all' ? (activeTab.value as InsuranceCategory) : 'life';
  resetAddForm(cat);
  showAddModal.value = true;
}

function resetAddForm(category?: InsuranceCategory) {
  addForm.value = {
    name: '',
    category: category || 'life',
    provider: '',
    policyNumber: '',
    coverageAmount: 0,
    premiumAmount: 0,
    premiumFrequency: 'annually',
    issueDate: new Date().toISOString().split('T')[0],
    startDate: new Date().toISOString().split('T')[0],
    expiryDate: '',
    maturityDate: '',
    bankAccountId: '',
    currency: 'BDT',
    notes: '',
    autoRenew: false,
    policyTerm: 0,
    maturityBenefit: 0,
    riderNames: '',
    deductibleAmount: 0,
    copayPercent: 0,
    vehicleType: 'car',
    vehicleRegistration: '',
    vehicleModel: '',
    propertyType: 'apartment',
    propertyAddress: '',
    propertyValue: 0,
    beneficiaryName: '',
    beneficiaryRelationship: 'self',
    beneficiaryPercentage: 100,
  };
}

function submitAddInsurance() {
  const form = addForm.value;
  const beneficiaries = form.beneficiaryName ? [{
    name: form.beneficiaryName,
    relationship: form.beneficiaryRelationship,
    percentage: form.beneficiaryPercentage,
  }] : [];

  const data: any = {
    name: form.name,
    category: form.category,
    provider: form.provider,
    policyNumber: form.policyNumber,
    coverageAmount: form.coverageAmount,
    premiumAmount: form.premiumAmount,
    premiumFrequency: form.premiumFrequency,
    issueDate: new Date(form.issueDate).toISOString(),
    startDate: new Date(form.startDate).toISOString(),
    expiryDate: form.expiryDate ? new Date(form.expiryDate).toISOString() : undefined,
    maturityDate: form.maturityDate ? new Date(form.maturityDate).toISOString() : undefined,
    bankAccountId: form.bankAccountId || undefined,
    currency: form.currency,
    notes: form.notes || undefined,
    status: 'active' as InsuranceStatus,
    autoRenew: form.autoRenew || undefined,
    beneficiaries,
  };

  if (form.category === 'life') {
    data.policyTerm = form.policyTerm || undefined;
    data.maturityBenefit = form.maturityBenefit || undefined;
    data.riderNames = form.riderNames ? form.riderNames.split(',').map(s => s.trim()).filter(Boolean) : undefined;
  }

  if (form.category === 'health') {
    data.deductibleAmount = form.deductibleAmount || undefined;
    data.copayPercent = form.copayPercent || undefined;
  }

  if (form.category === 'vehicle') {
    data.vehicleType = form.vehicleType || undefined;
    data.vehicleRegistration = form.vehicleRegistration || undefined;
    data.vehicleModel = form.vehicleModel || undefined;
  }

  if (form.category === 'property') {
    data.propertyType = form.propertyType || undefined;
    data.propertyAddress = form.propertyAddress || undefined;
    data.propertyValue = form.propertyValue || undefined;
  }

  // Set next premium due
  if (form.premiumFrequency !== 'single' && form.startDate) {
    const nextDue = new Date(form.startDate);
    if (form.premiumFrequency === 'monthly') nextDue.setMonth(nextDue.getMonth() + 1);
    else if (form.premiumFrequency === 'quarterly') nextDue.setMonth(nextDue.getMonth() + 3);
    else if (form.premiumFrequency === 'semiannually') nextDue.setMonth(nextDue.getMonth() + 6);
    else if (form.premiumFrequency === 'annually') nextDue.setFullYear(nextDue.getFullYear() + 1);
    data.nextPremiumDueDate = nextDue.toISOString();
  }

  insuranceStore.addInsurance(data);
  showAddModal.value = false;
}

function openPremiumModal(ins: Insurance) {
  selectedInsurance.value = ins;
  premiumForm.value = {
    amount: ins.premiumAmount,
    date: new Date().toISOString().split('T')[0],
    note: '',
  };
  showPremiumModal.value = true;
}

function submitPremium() {
  if (!selectedInsurance.value) return;
  const ins = selectedInsurance.value;
  insuranceStore.addPremiumPayment(ins.id, {
    amount: premiumForm.value.amount,
    paymentDate: new Date(premiumForm.value.date).toISOString(),
    paymentNumber: ins.paidPremiumsCount + 1,
    note: premiumForm.value.note || undefined,
    bankAccountId: ins.bankAccountId,
  });
  showPremiumModal.value = false;
  selectedInsurance.value = insuranceStore.getInsuranceById(ins.id) || null;
}

function openClaimModal(ins: Insurance) {
  selectedInsurance.value = ins;
  claimForm.value = {
    claimNumber: '',
    claimDate: new Date().toISOString().split('T')[0],
    claimAmount: 0,
    description: '',
  };
  showClaimModal.value = true;
}

function submitClaim() {
  if (!selectedInsurance.value) return;
  const ins = selectedInsurance.value;
  insuranceStore.addClaim(ins.id, {
    claimNumber: claimForm.value.claimNumber || undefined,
    claimDate: new Date(claimForm.value.claimDate).toISOString(),
    claimAmount: claimForm.value.claimAmount,
    description: claimForm.value.description,
    status: 'pending',
  });
  showClaimModal.value = false;
  selectedInsurance.value = insuranceStore.getInsuranceById(ins.id) || null;
}

function confirmDelete() {
  if (!selectedInsurance.value) return;
  insuranceStore.deleteInsurance(selectedInsurance.value.id);
  showDeleteConfirm.value = false;
  showDetailModal.value = false;
  selectedInsurance.value = null;
}
</script>

<template>
  <div class="animate-fade-in space-y-6">
    <!-- Page Header -->
    <PageHeader title="Insurance" subtitle="Track life, health, vehicle, property, and travel insurance policies">
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
      <StatCard title="Total Coverage" :value="fmtCur(insuranceStore.totalCoverage)" icon="🛡️" color="primary" />
      <StatCard title="Annual Premium" :value="fmtCur(insuranceStore.totalAnnualPremium)" icon="💳" color="warning" />
      <StatCard title="Total Paid" :value="fmtCur(insuranceStore.totalPremiumPaid)" icon="💰" color="info" />
      <StatCard title="Open Claims" :value="String(insuranceStore.openClaimsCount)" icon="📋" :color="insuranceStore.openClaimsCount > 0 ? 'danger' : 'success'" />
    </div>

    <!-- Upcoming Renewals Alert -->
    <div v-if="insuranceStore.upcomingRenewals.length > 0" class="bg-warning-50 dark:bg-warning-500/10 border border-warning-200 dark:border-warning-500/30 rounded-xl p-4">
      <div class="flex items-center gap-3 mb-2">
        <svg class="w-5 h-5 text-warning-600 dark:text-warning-400 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z"/></svg>
        <h4 class="font-semibold text-warning-800 dark:text-warning-300">Upcoming Renewals (30 days)</h4>
      </div>
      <div class="space-y-2">
        <div v-for="r in insuranceStore.upcomingRenewals" :key="r.id" class="flex items-center justify-between text-sm">
          <span class="text-warning-700 dark:text-warning-400">
            {{ categoryConfig[r.category].icon }} {{ r.name }} — {{ r.provider }}
          </span>
          <span class="text-warning-800 dark:text-warning-300 font-medium tabular-nums">
            {{ daysUntil(r.nextPremiumDueDate || '') }} days left
          </span>
        </div>
      </div>
    </div>

    <!-- Empty State -->
    <div v-if="filteredInsurances.length === 0">
      <EmptyState
        :icon="activeTab === 'all' ? '🛡️' : (categoryConfig[activeTab as InsuranceCategory]?.icon || '🛡️')"
        :title="activeTab === 'all' ? 'No insurance policies yet' : `No ${categoryConfig[activeTab as InsuranceCategory]?.label || ''} policies`"
        description="Add your first insurance policy to start tracking your coverage."
      >
        <template #action>
          <button class="btn-primary" @click="openAddModal">{{ addButtonText }}</button>
        </template>
      </EmptyState>
    </div>

    <!-- Insurance Cards Grid -->
    <div v-else class="grid grid-cols-1 lg:grid-cols-2 gap-4">
      <div
        v-for="ins in filteredInsurances"
        :key="ins.id"
        class="card-hover p-5 cursor-pointer animate-fade-in"
        @click="openDetail(ins)"
      >
        <!-- Header -->
        <div class="flex items-start justify-between mb-4">
          <div class="flex items-center gap-3">
            <div class="w-11 h-11 rounded-lg flex items-center justify-center text-xl" :class="{
              'bg-danger-100 dark:bg-danger-500/20': categoryConfig[ins.category].color === 'danger',
              'bg-success-50 dark:bg-success-500/20': categoryConfig[ins.category].color === 'success',
              'bg-warning-50 dark:bg-warning-500/20': categoryConfig[ins.category].color === 'warning',
              'bg-info-100 dark:bg-info-500/20': categoryConfig[ins.category].color === 'info',
              'bg-primary-100 dark:bg-primary-500/20': categoryConfig[ins.category].color === 'primary',
              'bg-surface-100 dark:bg-surface-700': categoryConfig[ins.category].color === 'neutral',
            }">
              {{ categoryConfig[ins.category].icon }}
            </div>
            <div>
              <h3 class="font-semibold text-surface-900 dark:text-white">{{ ins.name }}</h3>
              <p class="text-sm text-surface-500 dark:text-surface-400">{{ ins.provider }}</p>
            </div>
          </div>
          <div class="flex items-center gap-2">
            <Badge v-if="isExpiringSoon(ins) && ins.status === 'active'" variant="warning" class="text-xs">Expiring Soon</Badge>
            <Badge :variant="statusConfig[ins.status].variant">{{ statusConfig[ins.status].label }}</Badge>
          </div>
        </div>

        <!-- Key Metrics -->
        <div class="grid grid-cols-3 gap-3 mb-4">
          <div>
            <p class="text-xs text-surface-500 dark:text-surface-400">Coverage</p>
            <p class="text-sm font-semibold text-surface-900 dark:text-white tabular-nums">{{ fmtCur(ins.coverageAmount, ins.currency) }}</p>
          </div>
          <div>
            <p class="text-xs text-surface-500 dark:text-surface-400">Premium</p>
            <p class="text-sm font-semibold text-surface-900 dark:text-white tabular-nums">{{ fmtCur(ins.premiumAmount, ins.currency) }}</p>
            <p class="text-xs text-surface-400">{{ freqLabels[ins.premiumFrequency] }}</p>
          </div>
          <div>
            <p class="text-xs text-surface-500 dark:text-surface-400">Total Paid</p>
            <p class="text-sm font-semibold text-surface-900 dark:text-white tabular-nums">{{ fmtCur(ins.totalPremiumPaid, ins.currency) }}</p>
          </div>
        </div>

        <!-- Bottom Info Bar -->
        <div class="flex items-center justify-between bg-surface-50 dark:bg-surface-700/50 rounded-lg px-3 py-2">
          <span class="text-xs text-surface-500 dark:text-surface-400">
            {{ ins.policyNumber }}
          </span>
          <div class="flex items-center gap-3">
            <span v-if="ins.claims.length > 0" class="text-xs text-surface-500 dark:text-surface-400">
              {{ ins.claims.length }} claim{{ ins.claims.length > 1 ? 's' : '' }}
            </span>
            <span v-if="ins.expiryDate" class="text-xs text-surface-500 dark:text-surface-400">
              Exp: {{ formatDate(ins.expiryDate, 'short') }}
            </span>
          </div>
        </div>
      </div>
    </div>

    <!-- ======================== DETAIL MODAL ======================== -->
    <Modal v-if="selectedInsurance" :is-open="showDetailModal" title="Policy Details" size="xl" @close="showDetailModal = false">
      <div class="space-y-6" v-if="selectedInsurance">
        <!-- Header -->
        <div class="flex items-center gap-4 pb-4 border-b border-surface-200 dark:border-surface-700">
          <div class="w-14 h-14 rounded-xl flex items-center justify-center text-2xl" :class="{
            'bg-danger-100 dark:bg-danger-500/20': categoryConfig[selectedInsurance.category].color === 'danger',
            'bg-success-50 dark:bg-success-500/20': categoryConfig[selectedInsurance.category].color === 'success',
            'bg-warning-50 dark:bg-warning-500/20': categoryConfig[selectedInsurance.category].color === 'warning',
            'bg-info-100 dark:bg-info-500/20': categoryConfig[selectedInsurance.category].color === 'info',
            'bg-primary-100 dark:bg-primary-500/20': categoryConfig[selectedInsurance.category].color === 'primary',
            'bg-surface-100 dark:bg-surface-700': categoryConfig[selectedInsurance.category].color === 'neutral',
          }">
            {{ categoryConfig[selectedInsurance.category].icon }}
          </div>
          <div class="flex-1">
            <h3 class="text-xl font-bold text-surface-900 dark:text-white">{{ selectedInsurance.name }}</h3>
            <p class="text-surface-500 dark:text-surface-400">
              {{ selectedInsurance.provider }}
              <span v-if="selectedInsurance.policyNumber" class="ml-1">&middot; {{ selectedInsurance.policyNumber }}</span>
            </p>
          </div>
          <Badge :variant="statusConfig[selectedInsurance.status].variant" class="ml-auto">
            {{ statusConfig[selectedInsurance.status].label }}
          </Badge>
        </div>

        <!-- Key Metrics Grid -->
        <div class="grid grid-cols-2 md:grid-cols-4 gap-3">
          <div class="bg-surface-50 dark:bg-surface-700/50 rounded-lg p-3">
            <p class="text-xs text-surface-400 mb-1">Coverage</p>
            <p class="font-semibold text-surface-900 dark:text-white tabular-nums">{{ fmtCur(selectedInsurance.coverageAmount, selectedInsurance.currency) }}</p>
          </div>
          <div class="bg-surface-50 dark:bg-surface-700/50 rounded-lg p-3">
            <p class="text-xs text-surface-400 mb-1">Premium</p>
            <p class="font-semibold text-surface-900 dark:text-white tabular-nums">{{ fmtCur(selectedInsurance.premiumAmount, selectedInsurance.currency) }}</p>
            <p class="text-xs text-surface-400">{{ freqLabels[selectedInsurance.premiumFrequency] }}</p>
          </div>
          <div class="bg-surface-50 dark:bg-surface-700/50 rounded-lg p-3">
            <p class="text-xs text-surface-400 mb-1">Annual Premium</p>
            <p class="font-semibold text-surface-900 dark:text-white tabular-nums">{{ fmtCur(annualPremium(selectedInsurance), selectedInsurance.currency) }}</p>
          </div>
          <div class="bg-surface-50 dark:bg-surface-700/50 rounded-lg p-3">
            <p class="text-xs text-surface-400 mb-1">Total Paid</p>
            <p class="font-semibold text-surface-900 dark:text-white tabular-nums">{{ fmtCur(selectedInsurance.totalPremiumPaid, selectedInsurance.currency) }}</p>
          </div>
        </div>

        <!-- Policy Info -->
        <div class="bg-surface-50 dark:bg-surface-900 rounded-lg p-4">
          <h4 class="text-sm font-semibold text-surface-700 dark:text-surface-300 mb-3">Policy Information</h4>
          <div class="grid grid-cols-2 md:grid-cols-3 gap-3 text-sm">
            <div>
              <span class="text-xs text-surface-400">Issue Date</span>
              <p class="font-medium text-surface-900 dark:text-white">{{ formatDate(selectedInsurance.issueDate, 'long') }}</p>
            </div>
            <div>
              <span class="text-xs text-surface-400">Start Date</span>
              <p class="font-medium text-surface-900 dark:text-white">{{ formatDate(selectedInsurance.startDate, 'long') }}</p>
            </div>
            <div>
              <span class="text-xs text-surface-400">Expiry Date</span>
              <p class="font-medium" :class="isExpired(selectedInsurance) ? 'text-danger-500' : 'text-surface-900 dark:text-white'">
                {{ selectedInsurance.expiryDate ? formatDate(selectedInsurance.expiryDate, 'long') : '—' }}
                <span v-if="isExpiringSoon(selectedInsurance) && !isExpired(selectedInsurance)" class="text-warning-500 text-xs ml-1">({{ daysUntil(selectedInsurance.expiryDate || '') }} days left)</span>
              </p>
            </div>
            <div v-if="selectedInsurance.maturityDate">
              <span class="text-xs text-surface-400">Maturity Date</span>
              <p class="font-medium text-surface-900 dark:text-white">{{ formatDate(selectedInsurance.maturityDate, 'long') }}</p>
            </div>
            <div v-if="selectedInsurance.nextPremiumDueDate">
              <span class="text-xs text-surface-400">Next Due</span>
              <p class="font-medium text-surface-900 dark:text-white">{{ formatDate(selectedInsurance.nextPremiumDueDate, 'long') }}</p>
            </div>
            <div>
              <span class="text-xs text-surface-400">Auto-Renew</span>
              <p class="font-medium text-surface-900 dark:text-white">{{ selectedInsurance.autoRenew ? 'Yes' : 'No' }}</p>
            </div>
            <div v-if="selectedInsurance.groupPolicyNumber">
              <span class="text-xs text-surface-400">Group Policy</span>
              <p class="font-medium text-surface-900 dark:text-white">{{ selectedInsurance.groupPolicyNumber }}</p>
            </div>
          </div>
        </div>

        <!-- Life-specific Details -->
        <div v-if="selectedInsurance.category === 'life'" class="bg-surface-50 dark:bg-surface-900 rounded-lg p-4">
          <h4 class="text-sm font-semibold text-surface-700 dark:text-surface-300 mb-3">Life Insurance Details</h4>
          <div class="grid grid-cols-2 md:grid-cols-3 gap-3 text-sm">
            <div v-if="selectedInsurance.policyTerm">
              <span class="text-xs text-surface-400">Policy Term</span>
              <p class="font-medium text-surface-900 dark:text-white">{{ selectedInsurance.policyTerm }} years</p>
            </div>
            <div v-if="selectedInsurance.maturityBenefit">
              <span class="text-xs text-surface-400">Maturity Benefit</span>
              <p class="font-medium text-surface-900 dark:text-white tabular-nums">{{ fmtCur(selectedInsurance.maturityBenefit, selectedInsurance.currency) }}</p>
            </div>
            <div v-if="selectedInsurance.riderNames && selectedInsurance.riderNames.length > 0">
              <span class="text-xs text-surface-400">Riders</span>
              <div class="flex flex-wrap gap-1 mt-1">
                <Badge v-for="rider in selectedInsurance.riderNames" :key="rider" variant="info" class="text-xs">{{ rider }}</Badge>
              </div>
            </div>
          </div>
        </div>

        <!-- Health-specific Details -->
        <div v-if="selectedInsurance.category === 'health'" class="bg-surface-50 dark:bg-surface-900 rounded-lg p-4">
          <h4 class="text-sm font-semibold text-surface-700 dark:text-surface-300 mb-3">Health Insurance Details</h4>
          <div class="grid grid-cols-2 md:grid-cols-3 gap-3 text-sm">
            <div v-if="selectedInsurance.deductibleAmount">
              <span class="text-xs text-surface-400">Deductible</span>
              <p class="font-medium text-surface-900 dark:text-white tabular-nums">{{ fmtCur(selectedInsurance.deductibleAmount, selectedInsurance.currency) }}</p>
            </div>
            <div v-if="selectedInsurance.copayPercent">
              <span class="text-xs text-surface-400">Copay</span>
              <p class="font-medium text-surface-900 dark:text-white tabular-nums">{{ selectedInsurance.copayPercent }}%</p>
            </div>
            <div v-if="selectedInsurance.networkHospitals">
              <span class="text-xs text-surface-400">Network Hospitals</span>
              <p class="font-medium text-surface-900 dark:text-white text-xs">{{ selectedInsurance.networkHospitals }}</p>
            </div>
          </div>
        </div>

        <!-- Vehicle-specific Details -->
        <div v-if="selectedInsurance.category === 'vehicle'" class="bg-surface-50 dark:bg-surface-900 rounded-lg p-4">
          <h4 class="text-sm font-semibold text-surface-700 dark:text-surface-300 mb-3">Vehicle Details</h4>
          <div class="grid grid-cols-2 md:grid-cols-3 gap-3 text-sm">
            <div v-if="selectedInsurance.vehicleType">
              <span class="text-xs text-surface-400">Vehicle Type</span>
              <p class="font-medium text-surface-900 dark:text-white capitalize">{{ selectedInsurance.vehicleType }}</p>
            </div>
            <div v-if="selectedInsurance.vehicleModel">
              <span class="text-xs text-surface-400">Model</span>
              <p class="font-medium text-surface-900 dark:text-white">{{ selectedInsurance.vehicleModel }}</p>
            </div>
            <div v-if="selectedInsurance.vehicleRegistration">
              <span class="text-xs text-surface-400">Registration</span>
              <p class="font-medium text-surface-900 dark:text-white">{{ selectedInsurance.vehicleRegistration }}</p>
            </div>
          </div>
        </div>

        <!-- Property-specific Details -->
        <div v-if="selectedInsurance.category === 'property'" class="bg-surface-50 dark:bg-surface-900 rounded-lg p-4">
          <h4 class="text-sm font-semibold text-surface-700 dark:text-surface-300 mb-3">Property Details</h4>
          <div class="grid grid-cols-2 md:grid-cols-3 gap-3 text-sm">
            <div v-if="selectedInsurance.propertyType">
              <span class="text-xs text-surface-400">Property Type</span>
              <p class="font-medium text-surface-900 dark:text-white capitalize">{{ selectedInsurance.propertyType }}</p>
            </div>
            <div v-if="selectedInsurance.propertyAddress">
              <span class="text-xs text-surface-400">Address</span>
              <p class="font-medium text-surface-900 dark:text-white text-xs">{{ selectedInsurance.propertyAddress }}</p>
            </div>
            <div v-if="selectedInsurance.propertyValue">
              <span class="text-xs text-surface-400">Property Value</span>
              <p class="font-medium text-surface-900 dark:text-white tabular-nums">{{ fmtCur(selectedInsurance.propertyValue, selectedInsurance.currency) }}</p>
            </div>
          </div>
        </div>

        <!-- Beneficiaries -->
        <div v-if="selectedInsurance.beneficiaries.length > 0">
          <h4 class="text-sm font-semibold text-surface-700 dark:text-surface-300 mb-3">Beneficiaries</h4>
          <div class="space-y-2">
            <div v-for="ben in selectedInsurance.beneficiaries" :key="ben.name" class="flex items-center justify-between bg-surface-50 dark:bg-surface-700/50 rounded-lg px-4 py-3">
              <div>
                <p class="font-medium text-surface-900 dark:text-white">{{ ben.name }}</p>
                <p class="text-xs text-surface-400 capitalize">{{ ben.relationship }}{{ ben.phone ? ` · ${ben.phone}` : '' }}</p>
              </div>
              <Badge variant="info">{{ ben.percentage }}%</Badge>
            </div>
          </div>
        </div>

        <!-- Premium Payment History -->
        <div>
          <h4 class="text-sm font-semibold text-surface-700 dark:text-surface-300 mb-3">Premium Payments ({{ selectedInsurance.paidPremiumsCount }})</h4>
          <div class="max-h-56 overflow-y-auto">
            <DataTable
              :columns="paymentColumns"
              :data="[...selectedInsurance.premiumPayments].reverse()"
              empty-message="No payments recorded"
            >
              <template #cell-paymentDate="{ value }">
                {{ formatDate(value, 'short') }}
              </template>
              <template #cell-amount="{ value }">
                <span class="tabular-nums text-surface-900 dark:text-white">{{ fmtCur(value, selectedInsurance?.currency) }}</span>
              </template>
              <template #cell-note="{ value }">
                <span class="text-xs text-surface-500 dark:text-surface-400 truncate block max-w-[200px]">{{ value || '—' }}</span>
              </template>
            </DataTable>
          </div>
        </div>

        <!-- Claims History -->
        <div>
          <h4 class="text-sm font-semibold text-surface-700 dark:text-surface-300 mb-3">Claims ({{ selectedInsurance.claims.length }})</h4>
          <div class="max-h-56 overflow-y-auto">
            <DataTable
              :columns="claimColumns"
              :data="[...selectedInsurance.claims].reverse()"
              empty-message="No claims filed"
            >
              <template #cell-claimDate="{ value }">
                {{ formatDate(value, 'short') }}
              </template>
              <template #cell-claimAmount="{ value }">
                <span class="tabular-nums text-surface-900 dark:text-white">{{ fmtCur(value, selectedInsurance?.currency) }}</span>
              </template>
              <template #cell-approvedAmount="{ value }">
                <span class="tabular-nums" :class="value ? 'text-accent-600 dark:text-accent-400' : 'text-surface-400'">
                  {{ value ? fmtCur(value, selectedInsurance?.currency) : '—' }}
                </span>
              </template>
              <template #cell-status="{ value }">
                <Badge :variant="claimStatusConfig[value as InsuranceClaimStatus]?.variant || 'neutral'">
                  {{ claimStatusConfig[value as InsuranceClaimStatus]?.label || value }}
                </Badge>
              </template>
              <template #cell-description="{ value }">
                <span class="text-xs text-surface-500 dark:text-surface-400 truncate block max-w-[200px]">{{ value || '—' }}</span>
              </template>
            </DataTable>
          </div>
        </div>

        <!-- Notes -->
        <div v-if="selectedInsurance.notes">
          <h4 class="text-sm font-semibold text-surface-700 dark:text-surface-300 mb-1">Notes</h4>
          <p class="text-sm text-surface-600 dark:text-surface-400">{{ selectedInsurance.notes }}</p>
        </div>

        <!-- Actions -->
        <div class="flex flex-wrap gap-3 pt-2 border-t border-surface-200 dark:border-surface-700">
          <button v-if="selectedInsurance.status === 'active'" class="btn-primary" @click="openPremiumModal(selectedInsurance!)">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/></svg>
            Record Premium
          </button>
          <button v-if="selectedInsurance.status === 'active'" class="btn-secondary" @click="openClaimModal(selectedInsurance!)">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/></svg>
            File Claim
          </button>
          <button class="btn-danger" @click="showDeleteConfirm = true">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/></svg>
            Delete
          </button>
        </div>
      </div>
    </Modal>

    <!-- ======================== ADD INSURANCE MODAL ======================== -->
    <Modal :is-open="showAddModal" title="Add Insurance Policy" size="xl" @close="showAddModal = false">
      <div class="space-y-5">
        <!-- Basic Details -->
        <div>
          <h4 class="text-sm font-semibold text-surface-900 dark:text-white mb-3 flex items-center gap-2">
            <span>{{ categoryConfig[addForm.category].icon }}</span> Basic Details
          </h4>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label class="field-label">Category</label>
              <select v-model="addForm.category" class="input-field">
                <option value="life">❤️ Life Insurance</option>
                <option value="health">🏥 Health Insurance</option>
                <option value="vehicle">🚗 Vehicle Insurance</option>
                <option value="property">🏠 Property Insurance</option>
                <option value="travel">✈️ Travel Insurance</option>
                <option value="critical_illness">⚕️ Critical Illness</option>
                <option value="other">📋 Other</option>
              </select>
            </div>
            <div>
              <label class="field-label">Insurance Provider</label>
              <input v-model="addForm.provider" type="text" class="input-field" placeholder="e.g., MetLife Bangladesh" />
            </div>
            <div>
              <label class="field-label">Policy Name</label>
              <input v-model="addForm.name" type="text" class="input-field" placeholder="e.g., Jiban Suraksha" />
            </div>
            <div>
              <label class="field-label">Policy Number</label>
              <input v-model="addForm.policyNumber" type="text" class="input-field" placeholder="e.g., ML-JBS-2023-45821" />
            </div>
          </div>
        </div>

        <!-- Coverage & Premium -->
        <div>
          <h4 class="text-sm font-semibold text-surface-900 dark:text-white mb-3">Coverage & Premium</h4>
          <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label class="field-label">Coverage Amount (৳)</label>
              <input v-model.number="addForm.coverageAmount" type="number" class="input-field" placeholder="0" min="0" />
            </div>
            <div>
              <label class="field-label">Premium Amount (৳)</label>
              <input v-model.number="addForm.premiumAmount" type="number" class="input-field" placeholder="0" min="0" />
            </div>
            <div>
              <label class="field-label">Premium Frequency</label>
              <select v-model="addForm.premiumFrequency" class="input-field">
                <option value="monthly">Monthly</option>
                <option value="quarterly">Quarterly</option>
                <option value="semiannually">Semi-Annually</option>
                <option value="annually">Annually</option>
                <option value="single">Single Payment</option>
              </select>
            </div>
          </div>
        </div>

        <!-- Dates -->
        <div>
          <h4 class="text-sm font-semibold text-surface-900 dark:text-white mb-3">Dates</h4>
          <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label class="field-label">Issue Date</label>
              <input v-model="addForm.issueDate" type="date" class="input-field" />
            </div>
            <div>
              <label class="field-label">Start Date</label>
              <input v-model="addForm.startDate" type="date" class="input-field" />
            </div>
            <div>
              <label class="field-label">Expiry Date</label>
              <input v-model="addForm.expiryDate" type="date" class="input-field" />
            </div>
          </div>
        </div>

        <!-- Life-specific fields -->
        <div v-if="addForm.category === 'life'">
          <h4 class="text-sm font-semibold text-surface-900 dark:text-white mb-3">❤️ Life Insurance Details</h4>
          <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label class="field-label">Policy Term (years)</label>
              <input v-model.number="addForm.policyTerm" type="number" class="input-field" placeholder="e.g., 20" min="0" />
            </div>
            <div>
              <label class="field-label">Maturity Benefit (৳)</label>
              <input v-model.number="addForm.maturityBenefit" type="number" class="input-field" placeholder="0" min="0" />
            </div>
            <div>
              <label class="field-label">Riders (comma-separated)</label>
              <input v-model="addForm.riderNames" type="text" class="input-field" placeholder="e.g., ADB, Critical Illness" />
            </div>
          </div>
        </div>

        <!-- Health-specific fields -->
        <div v-if="addForm.category === 'health'">
          <h4 class="text-sm font-semibold text-surface-900 dark:text-white mb-3">🏥 Health Insurance Details</h4>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label class="field-label">Deductible Amount (৳)</label>
              <input v-model.number="addForm.deductibleAmount" type="number" class="input-field" placeholder="0" min="0" />
            </div>
            <div>
              <label class="field-label">Copay Percent (%)</label>
              <input v-model.number="addForm.copayPercent" type="number" class="input-field" placeholder="e.g., 10" min="0" max="100" />
            </div>
          </div>
        </div>

        <!-- Vehicle-specific fields -->
        <div v-if="addForm.category === 'vehicle'">
          <h4 class="text-sm font-semibold text-surface-900 dark:text-white mb-3">🚗 Vehicle Details</h4>
          <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label class="field-label">Vehicle Type</label>
              <select v-model="addForm.vehicleType" class="input-field">
                <option value="car">Car</option>
                <option value="motorcycle">Motorcycle</option>
                <option value="bus">Bus</option>
                <option value="truck">Truck</option>
                <option value="other">Other</option>
              </select>
            </div>
            <div>
              <label class="field-label">Vehicle Model</label>
              <input v-model="addForm.vehicleModel" type="text" class="input-field" placeholder="e.g., Toyota Corolla X 2023" />
            </div>
            <div>
              <label class="field-label">Registration No.</label>
              <input v-model="addForm.vehicleRegistration" type="text" class="input-field" placeholder="e.g., Dhaka Metro Ga-45-8921" />
            </div>
          </div>
        </div>

        <!-- Property-specific fields -->
        <div v-if="addForm.category === 'property'">
          <h4 class="text-sm font-semibold text-surface-900 dark:text-white mb-3">🏠 Property Details</h4>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label class="field-label">Property Type</label>
              <select v-model="addForm.propertyType" class="input-field">
                <option value="apartment">Apartment</option>
                <option value="house">House</option>
                <option value="land">Land</option>
                <option value="commercial">Commercial</option>
                <option value="other">Other</option>
              </select>
            </div>
            <div>
              <label class="field-label">Property Address</label>
              <input v-model="addForm.propertyAddress" type="text" class="input-field" placeholder="e.g., House #45, Road #8, Dhanmondi" />
            </div>
            <div>
              <label class="field-label">Property Value (৳)</label>
              <input v-model.number="addForm.propertyValue" type="number" class="input-field" placeholder="0" min="0" />
            </div>
          </div>
        </div>

        <!-- Beneficiary -->
        <div>
          <h4 class="text-sm font-semibold text-surface-900 dark:text-white mb-3">Beneficiary</h4>
          <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label class="field-label">Name</label>
              <input v-model="addForm.beneficiaryName" type="text" class="input-field" placeholder="e.g., Fatima Rahman" />
            </div>
            <div>
              <label class="field-label">Relationship</label>
              <select v-model="addForm.beneficiaryRelationship" class="input-field">
                <option value="self">Self</option>
                <option value="spouse">Spouse</option>
                <option value="child">Child</option>
                <option value="parent">Parent</option>
                <option value="sibling">Sibling</option>
                <option value="other">Other</option>
              </select>
            </div>
            <div>
              <label class="field-label">Share (%)</label>
              <input v-model.number="addForm.beneficiaryPercentage" type="number" class="input-field" placeholder="100" min="1" max="100" />
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
          <button class="btn-primary" @click="submitAddInsurance" :disabled="!addForm.name || !addForm.provider || !addForm.policyNumber">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/></svg>
            Add Policy
          </button>
        </div>
      </div>
    </Modal>

    <!-- ======================== RECORD PREMIUM MODAL ======================== -->
    <Modal :is-open="showPremiumModal" title="Record Premium Payment" size="md" @close="showPremiumModal = false">
      <div class="space-y-4">
        <div class="bg-surface-50 dark:bg-surface-700/50 rounded-lg p-3 text-sm">
          <span class="text-surface-500 dark:text-surface-400">Policy: </span>
          <span class="font-medium text-surface-900 dark:text-white">{{ selectedInsurance?.name }}</span>
          <span class="text-surface-400 ml-2">· Premium #{{ (selectedInsurance?.paidPremiumsCount || 0) + 1 }}</span>
        </div>
        <div>
          <label class="field-label">Amount (৳)</label>
          <input v-model.number="premiumForm.amount" type="number" class="input-field" placeholder="0" min="0" />
        </div>
        <div>
          <label class="field-label">Payment Date</label>
          <input v-model="premiumForm.date" type="date" class="input-field" />
        </div>
        <div>
          <label class="field-label">Note</label>
          <input v-model="premiumForm.note" type="text" class="input-field" placeholder="e.g., Quarterly premium" />
        </div>
        <div class="flex items-center gap-3 justify-end pt-2 border-t border-surface-200 dark:border-surface-700">
          <button class="btn-secondary" @click="showPremiumModal = false">Cancel</button>
          <button class="btn-primary" @click="submitPremium" :disabled="premiumForm.amount <= 0">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/></svg>
            Record Payment
          </button>
        </div>
      </div>
    </Modal>

    <!-- ======================== FILE CLAIM MODAL ======================== -->
    <Modal :is-open="showClaimModal" title="File Insurance Claim" size="md" @close="showClaimModal = false">
      <div class="space-y-4">
        <div class="bg-surface-50 dark:bg-surface-700/50 rounded-lg p-3 text-sm">
          <span class="text-surface-500 dark:text-surface-400">Policy: </span>
          <span class="font-medium text-surface-900 dark:text-white">{{ selectedInsurance?.name }}</span>
          <span class="text-surface-400 ml-2">· Coverage: {{ fmtCur(selectedInsurance?.coverageAmount || 0, selectedInsurance?.currency) }}</span>
        </div>
        <div>
          <label class="field-label">Claim Number (optional)</label>
          <input v-model="claimForm.claimNumber" type="text" class="input-field" placeholder="e.g., CLM-2026-001" />
        </div>
        <div>
          <label class="field-label">Claim Amount (৳)</label>
          <input v-model.number="claimForm.claimAmount" type="number" class="input-field" placeholder="0" min="0" />
        </div>
        <div>
          <label class="field-label">Claim Date</label>
          <input v-model="claimForm.claimDate" type="date" class="input-field" />
        </div>
        <div>
          <label class="field-label">Description</label>
          <textarea v-model="claimForm.description" class="input-field" rows="3" placeholder="Describe the incident and reason for claim..."></textarea>
        </div>
        <div class="flex items-center gap-3 justify-end pt-2 border-t border-surface-200 dark:border-surface-700">
          <button class="btn-secondary" @click="showClaimModal = false">Cancel</button>
          <button class="btn-primary" @click="submitClaim" :disabled="claimForm.claimAmount <= 0 || !claimForm.description">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/></svg>
            File Claim
          </button>
        </div>
      </div>
    </Modal>

    <!-- ======================== DELETE CONFIRM ======================== -->
    <Modal :is-open="showDeleteConfirm" title="Delete Insurance Policy" size="sm" @close="showDeleteConfirm = false">
      <div class="space-y-4">
        <p class="text-sm text-surface-600 dark:text-surface-400">
          Are you sure you want to delete <strong class="text-surface-900 dark:text-white">{{ selectedInsurance?.name }}</strong>?
          This action cannot be undone. All premium payments and claims history will be lost.
        </p>
        <div class="flex items-center gap-3 justify-end">
          <button class="btn-secondary" @click="showDeleteConfirm = false">Cancel</button>
          <button class="btn-danger" @click="confirmDelete">Delete Policy</button>
        </div>
      </div>
    </Modal>
  </div>
</template>
