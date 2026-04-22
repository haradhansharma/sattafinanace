<script setup lang="ts">
import { ref, computed } from 'vue';
import { useDocumentStore } from '../../stores/document';
import { formatDate } from '../../utils/formatters';
import { PageHeader, StatCard, Badge, Modal, EmptyState, Tabs, SearchInput } from '../ui';
import type { DocumentVaultItem, DocumentCategory, DocumentStatus, DocumentFormat } from '../../types';

const store = useDocumentStore();

// ============ Tab State ============
type TabKey = 'all' | 'favorites' | 'expiring' | 'archived' | DocumentCategory;
const activeTab = ref<TabKey>('all');
const tabItems = [
  { key: 'all', label: 'All', icon: '📁' },
  { key: 'favorites', label: 'Favorites', icon: '⭐' },
  { key: 'expiring', label: 'Expiring', icon: '⏰' },
  { key: 'tax_return', label: 'Tax', icon: '🧾' },
  { key: 'insurance_policy', label: 'Insurance', icon: '🛡️' },
  { key: 'property_deed', label: 'Property', icon: '🏠' },
  { key: 'bank_statement', label: 'Banking', icon: '🏦' },
  { key: 'investment_statement', label: 'Investments', icon: '📈' },
  { key: 'loan_document', label: 'Loans', icon: '📋' },
  { key: 'contract', label: 'Contracts', icon: '📝' },
  { key: 'receipt', label: 'Receipts', icon: '🧾' },
  { key: 'invoice', label: 'Invoices', icon: '📄' },
  { key: 'id_proof', label: 'ID / Personal', icon: '🪪' },
  { key: 'medical_record', label: 'Medical', icon: '🏥' },
  { key: 'education_certificate', label: 'Education', icon: '🎓' },
  { key: 'vehicle_registration', label: 'Vehicle', icon: '🚗' },
  { key: 'archived', label: 'Archived', icon: '📦' },
  { key: 'other', label: 'Other', icon: '📎' },
];

// ============ Search ============
const searchQuery = ref('');

// ============ Modal State ============
const selectedDoc = ref<DocumentVaultItem | null>(null);
const showDetailModal = ref(false);
const showAddModal = ref(false);
const showDeleteConfirm = ref(false);

// ============ Config ============
const categoryConfig: Record<DocumentCategory, { label: string; icon: string; color: string }> = {
  tax_return: { label: 'Tax Return', icon: '🧾', color: 'danger' },
  insurance_policy: { label: 'Insurance Policy', icon: '🛡️', color: 'success' },
  property_deed: { label: 'Property Deed', icon: '🏠', color: 'warning' },
  bank_statement: { label: 'Bank Statement', icon: '🏦', color: 'info' },
  investment_statement: { label: 'Investment Statement', icon: '📈', color: 'primary' },
  loan_document: { label: 'Loan Document', icon: '📋', color: 'warning' },
  contract: { label: 'Contract', icon: '📝', color: 'info' },
  receipt: { label: 'Receipt', icon: '🧾', color: 'neutral' },
  invoice: { label: 'Invoice', icon: '📄', color: 'neutral' },
  id_proof: { label: 'ID Proof', icon: '🪪', color: 'danger' },
  medical_record: { label: 'Medical Record', icon: '🏥', color: 'success' },
  education_certificate: { label: 'Education Certificate', icon: '🎓', color: 'primary' },
  vehicle_registration: { label: 'Vehicle Registration', icon: '🚗', color: 'info' },
  other: { label: 'Other', icon: '📎', color: 'neutral' },
};

const statusConfig: Record<DocumentStatus, { variant: 'success' | 'danger' | 'warning' | 'info' | 'neutral'; label: string }> = {
  active: { variant: 'success', label: 'Active' },
  expired: { variant: 'danger', label: 'Expired' },
  archived: { variant: 'neutral', label: 'Archived' },
  draft: { variant: 'warning', label: 'Draft' },
};

const formatConfig: Record<string, { icon: string; color: string; label: string }> = {
  pdf: { icon: '📕', color: 'text-red-500', label: 'PDF' },
  doc: { icon: '📘', color: 'text-blue-500', label: 'DOC' },
  docx: { icon: '📘', color: 'text-blue-500', label: 'DOCX' },
  xls: { icon: '📗', color: 'text-green-500', label: 'XLS' },
  xlsx: { icon: '📗', color: 'text-green-500', label: 'XLSX' },
  jpg: { icon: '🖼️', color: 'text-purple-500', label: 'JPG' },
  jpeg: { icon: '🖼️', color: 'text-purple-500', label: 'JPEG' },
  png: { icon: '🖼️', color: 'text-purple-500', label: 'PNG' },
  csv: { icon: '📊', color: 'text-green-600', label: 'CSV' },
  txt: { icon: '📄', color: 'text-surface-500', label: 'TXT' },
  zip: { icon: '🗜️', color: 'text-yellow-500', label: 'ZIP' },
  other: { icon: '📎', color: 'text-surface-400', label: 'File' },
};

// ============ Helpers ============
function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
}

function daysUntil(dateStr: string): number {
  const now = new Date();
  now.setHours(0, 0, 0, 0);
  const target = new Date(dateStr);
  target.setHours(0, 0, 0, 0);
  const diff = target.getTime() - now.getTime();
  return Math.ceil(diff / (1000 * 60 * 60 * 24));
}

function isExpiringSoon(doc: DocumentVaultItem): boolean {
  if (!doc.expiryDate) return false;
  const days = daysUntil(doc.expiryDate);
  const threshold = doc.reminderBeforeDays || 30;
  return days >= 0 && days <= threshold && doc.status === 'active';
}

function isOverdue(doc: DocumentVaultItem): boolean {
  if (!doc.expiryDate || doc.status !== 'active') return false;
  return daysUntil(doc.expiryDate) < 0;
}

// ============ Filtered Documents ============
const filteredDocuments = computed(() => {
  let docs: DocumentVaultItem[];

  if (activeTab.value === 'all') {
    docs = store.documents;
  } else if (activeTab.value === 'favorites') {
    docs = store.favoriteDocuments;
  } else if (activeTab.value === 'expiring') {
    docs = [...store.documentsExpiringSoon, ...store.overdueDocuments];
  } else if (activeTab.value === 'archived') {
    docs = store.archivedDocuments;
  } else {
    docs = store.getByCategory(activeTab.value as DocumentCategory);
  }

  // Apply search
  if (searchQuery.value.trim()) {
    const q = searchQuery.value.toLowerCase().trim();
    docs = docs.filter(d =>
      d.name.toLowerCase().includes(q) ||
      d.description?.toLowerCase().includes(q) ||
      d.tags.some(t => t.toLowerCase().includes(q)) ||
      d.fileName?.toLowerCase().includes(q) ||
      d.notes?.toLowerCase().includes(q)
    );
  }

  return docs;
});

const addButtonText = computed(() => {
  if (activeTab.value === 'all' || activeTab.value === 'favorites' || activeTab.value === 'expiring' || activeTab.value === 'archived') return 'Add Document';
  const cat = activeTab.value as DocumentCategory;
  return `Add ${categoryConfig[cat]?.label || 'Document'}`;
});

// ============ Sort ============
const sortBy = ref<'date' | 'name' | 'size' | 'category'>('date');
const sortDir = ref<'desc' | 'asc'>('desc');

const sortedDocuments = computed(() => {
  const docs = [...filteredDocuments.value];
  const dir = sortDir.value === 'asc' ? 1 : -1;

  return docs.sort((a, b) => {
    if (sortBy.value === 'date') return dir * (new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime());
    if (sortBy.value === 'name') return dir * a.name.localeCompare(b.name);
    if (sortBy.value === 'size') return dir * (a.fileSize - b.fileSize);
    if (sortBy.value === 'category') return dir * a.category.localeCompare(b.category);
    return 0;
  });
});

// ============ Add Document Form ============
const addForm = ref({
  name: '',
  description: '',
  category: 'other' as DocumentCategory,
  format: 'pdf' as DocumentFormat,
  status: 'active' as DocumentStatus,
  fileSize: 0,
  fileName: '',
  tags: '' as string,
  isFavorite: false,
  isImportant: false,
  documentDate: '' as string,
  expiryDate: '' as string,
  reminderBeforeDays: 30,
  linkedEntityId: '',
  linkedEntityType: '' as string,
  isEncrypted: false,
  source: 'upload' as string,
  notes: '',
});

// ============ Actions ============
function openDetail(doc: DocumentVaultItem) {
  selectedDoc.value = doc;
  showDetailModal.value = true;
}

function openAddModal() {
  resetAddForm();
  if (activeTab.value !== 'all' && activeTab.value !== 'favorites' && activeTab.value !== 'expiring' && activeTab.value !== 'archived') {
    addForm.value.category = activeTab.value as DocumentCategory;
  }
  showAddModal.value = true;
}

function resetAddForm() {
  addForm.value = {
    name: '',
    description: '',
    category: 'other',
    format: 'pdf',
    status: 'active',
    fileSize: 0,
    fileName: '',
    tags: '',
    isFavorite: false,
    isImportant: false,
    documentDate: '',
    expiryDate: '',
    reminderBeforeDays: 30,
    linkedEntityId: '',
    linkedEntityType: '',
    isEncrypted: false,
    source: 'upload',
    notes: '',
  };
}

function submitAddDocument() {
  const f = addForm.value;
  if (!f.name) return;

  const tags = f.tags ? f.tags.split(',').map(t => t.trim()).filter(Boolean) : [];

  store.addDocument({
    name: f.name,
    description: f.description || undefined,
    category: f.category,
    format: f.format,
    status: f.status,
    fileSize: f.fileSize || 1024,
    fileName: f.fileName || `${f.name.replace(/\s+/g, '_')}.${f.format}`,
    tags,
    isFavorite: f.isFavorite,
    isImportant: f.isImportant,
    documentDate: f.documentDate ? new Date(f.documentDate).toISOString() : undefined,
    expiryDate: f.expiryDate ? new Date(f.expiryDate).toISOString() : undefined,
    reminderBeforeDays: f.reminderBeforeDays || undefined,
    linkedEntityId: f.linkedEntityId || undefined,
    linkedEntityType: (f.linkedEntityType as any) || undefined,
    isEncrypted: f.isEncrypted || undefined,
    source: f.source || undefined,
    notes: f.notes || undefined,
  });

  showAddModal.value = false;
}

function confirmDelete() {
  if (!selectedDoc.value) return;
  store.deleteDocument(selectedDoc.value.id);
  showDeleteConfirm.value = false;
  showDetailModal.value = false;
  selectedDoc.value = null;
}

function handleToggleFavorite(doc: DocumentVaultItem, event: Event) {
  event.stopPropagation();
  store.toggleFavorite(doc.id);
}

function handleToggleImportant(doc: DocumentVaultItem, event: Event) {
  event.stopPropagation();
  store.toggleImportant(doc.id);
}

function handleArchive(doc: DocumentVaultItem) {
  if (doc.status === 'archived') {
    store.restoreDocument(doc.id);
  } else {
    store.archiveDocument(doc.id);
  }
}

function handleSort(field: 'date' | 'name' | 'size' | 'category') {
  if (sortBy.value === field) {
    sortDir.value = sortDir.value === 'asc' ? 'desc' : 'asc';
  } else {
    sortBy.value = field;
    sortDir.value = 'desc';
  }
}

const linkedEntityLabels: Record<string, string> = {
  insurance: 'Insurance Policy',
  loan: 'Loan',
  mortgage: 'Mortgage',
  asset: 'Asset',
  investment: 'Investment',
  lending: 'Lending',
  invoice: 'Invoice',
  other: 'Other',
};
</script>

<template>
  <div class="animate-fade-in space-y-6">
    <!-- Page Header -->
    <PageHeader title="Document Vault" subtitle="Securely organize and track all your important financial documents">
      <template #actions>
        <button class="btn-primary" @click="openAddModal">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/></svg>
          {{ addButtonText }}
        </button>
      </template>
    </PageHeader>

    <!-- Tabs -->
    <Tabs :tabs="tabItems" :active-tab="activeTab" @update:active-tab="(k: string) => { activeTab = k as TabKey; searchQuery = ''; }" />

    <!-- Summary Stats -->
    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      <StatCard title="Total Documents" :value="String(store.totalDocuments)" icon="📁" color="primary" />
      <StatCard title="Active Documents" :value="String(store.activeDocuments.length)" icon="✅" color="success" />
      <StatCard title="Expiring Soon" :value="String(store.documentsExpiringSoon.length + store.overdueDocuments.length)" icon="⏰" :color="store.documentsExpiringSoon.length + store.overdueDocuments.length > 0 ? 'warning' : 'success'" />
      <StatCard title="Storage Used" :value="formatFileSize(store.totalFileSize)" icon="💾" color="info" />
    </div>

    <!-- Expiring Soon Alert -->
    <div v-if="activeTab === 'all' && (store.documentsExpiringSoon.length > 0 || store.overdueDocuments.length > 0)" class="bg-warning-50 dark:bg-warning-500/10 border border-warning-200 dark:border-warning-500/30 rounded-xl p-4">
      <div class="flex items-center gap-3 mb-2">
        <svg class="w-5 h-5 text-warning-600 dark:text-warning-400 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z"/></svg>
        <h4 class="font-semibold text-warning-800 dark:text-warning-300">Document Alerts</h4>
      </div>
      <div class="space-y-2">
        <div v-for="doc in [...store.overdueDocuments, ...store.documentsExpiringSoon]" :key="doc.id" class="flex items-center justify-between text-sm">
          <span class="text-warning-700 dark:text-warning-400">
            {{ categoryConfig[doc.category]?.icon }} {{ doc.name }}
          </span>
          <span :class="isOverdue(doc) ? 'text-danger-600 dark:text-danger-400 font-semibold' : 'text-warning-800 dark:text-warning-300 font-medium'" class="tabular-nums">
            {{ isOverdue(doc) ? 'Expired' : `${daysUntil(doc.expiryDate || '')} days left` }}
          </span>
        </div>
      </div>
    </div>

    <!-- Search & Sort Bar -->
    <div class="flex flex-col sm:flex-row gap-3 items-start sm:items-center">
      <div class="flex-1 w-full sm:w-auto">
        <SearchInput v-model="searchQuery" placeholder="Search documents by name, tag, description..." />
      </div>
      <div class="flex items-center gap-2 shrink-0">
        <span class="text-xs text-surface-400">Sort:</span>
        <button @click="handleSort('date')" class="sort-btn" :class="{ active: sortBy === 'date' }">
          Date {{ sortBy === 'date' ? (sortDir === 'desc' ? '↓' : '↑') : '' }}
        </button>
        <button @click="handleSort('name')" class="sort-btn" :class="{ active: sortBy === 'name' }">
          Name {{ sortBy === 'name' ? (sortDir === 'desc' ? '↓' : '↑') : '' }}
        </button>
        <button @click="handleSort('size')" class="sort-btn" :class="{ active: sortBy === 'size' }">
          Size {{ sortBy === 'size' ? (sortDir === 'desc' ? '↓' : '↑') : '' }}
        </button>
        <button @click="handleSort('category')" class="sort-btn" :class="{ active: sortBy === 'category' }">
          Category {{ sortBy === 'category' ? (sortDir === 'desc' ? '↓' : '↑') : '' }}
        </button>
      </div>
    </div>

    <!-- Empty State -->
    <div v-if="sortedDocuments.length === 0">
      <EmptyState
        :icon="activeTab === 'favorites' ? '⭐' : activeTab === 'expiring' ? '✅' : activeTab === 'archived' ? '📦' : (categoryConfig[activeTab as DocumentCategory]?.icon || '📁')"
        :title="activeTab === 'all' ? 'No documents yet' : activeTab === 'favorites' ? 'No favorite documents' : activeTab === 'expiring' ? 'No expiring documents' : activeTab === 'archived' ? 'No archived documents' : `No ${categoryConfig[activeTab as DocumentCategory]?.label || ''} documents`"
        :description="searchQuery ? 'No results for &quot;' + searchQuery + '&quot;. Try a different search.' : 'Add your first document to start building your vault.'"
      >
        <template #action v-if="!searchQuery">
          <button class="btn-primary" @click="openAddModal">{{ addButtonText }}</button>
        </template>
      </EmptyState>
    </div>

    <!-- Document Cards Grid -->
    <div v-else class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
      <div
        v-for="doc in sortedDocuments"
        :key="doc.id"
        class="card-hover p-4 cursor-pointer animate-fade-in relative group"
        :class="{ 'opacity-60': doc.status === 'archived' }"
        @click="openDetail(doc)"
      >
        <!-- Top Row: Format Icon + Name + Actions -->
        <div class="flex items-start justify-between mb-3">
          <div class="flex items-center gap-3 min-w-0 flex-1">
            <div class="w-11 h-11 rounded-lg flex items-center justify-center text-xl shrink-0 bg-surface-100 dark:bg-surface-700">
              {{ formatConfig[doc.format]?.icon || '📎' }}
            </div>
            <div class="min-w-0 flex-1">
              <h3 class="font-semibold text-surface-900 dark:text-white text-sm truncate">{{ doc.name }}</h3>
              <p class="text-xs text-surface-400 truncate">
                {{ doc.fileName || formatConfig[doc.format]?.label || 'File' }}
              </p>
            </div>
          </div>

          <!-- Favorite / Important toggle buttons -->
          <div class="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity shrink-0 ml-2">
            <button @click="handleToggleFavorite(doc, $event)" class="p-1 rounded hover:bg-surface-100 dark:hover:bg-surface-700 transition-colors" :title="doc.isFavorite ? 'Remove from favorites' : 'Add to favorites'">
              <span class="text-base">{{ doc.isFavorite ? '⭐' : '☆' }}</span>
            </button>
            <button @click="handleToggleImportant(doc, $event)" class="p-1 rounded hover:bg-surface-100 dark:hover:bg-surface-700 transition-colors" :title="doc.isImportant ? 'Unmark important' : 'Mark important'">
              <span class="text-base">{{ doc.isImportant ? '🔴' : '⚪' }}</span>
            </button>
          </div>
        </div>

        <!-- Category & Status -->
        <div class="flex items-center gap-2 mb-3 flex-wrap">
          <span class="inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-full bg-surface-100 dark:bg-surface-700 text-surface-600 dark:text-surface-300">
            {{ categoryConfig[doc.category]?.icon }} {{ categoryConfig[doc.category]?.label }}
          </span>
          <Badge :variant="statusConfig[doc.status]?.variant || 'neutral'" class="text-xs">
            {{ statusConfig[doc.status]?.label || doc.status }}
          </Badge>
          <span v-if="doc.isEncrypted" class="text-xs" title="Encrypted">🔐</span>
          <span v-if="isOverdue(doc)" class="text-xs text-danger-500 font-semibold">EXPIRED</span>
          <span v-else-if="isExpiringSoon(doc)" class="text-xs text-warning-500 font-medium">
            {{ daysUntil(doc.expiryDate || '') }}d left
          </span>
        </div>

        <!-- Description -->
        <p v-if="doc.description" class="text-xs text-surface-500 dark:text-surface-400 line-clamp-2 mb-3">
          {{ doc.description }}
        </p>

        <!-- Tags -->
        <div v-if="doc.tags.length > 0" class="flex flex-wrap gap-1 mb-3">
          <span v-for="tag in doc.tags.slice(0, 4)" :key="tag" class="text-xs px-1.5 py-0.5 rounded bg-primary-50 dark:bg-primary-500/10 text-primary-600 dark:text-primary-400">
            {{ tag }}
          </span>
          <span v-if="doc.tags.length > 4" class="text-xs text-surface-400">+{{ doc.tags.length - 4 }}</span>
        </div>

        <!-- Bottom Info Bar -->
        <div class="flex items-center justify-between bg-surface-50 dark:bg-surface-700/50 rounded-lg px-3 py-2 text-xs text-surface-500 dark:text-surface-400">
          <div class="flex items-center gap-3">
            <span class="tabular-nums">{{ formatFileSize(doc.fileSize) }}</span>
            <span class="uppercase font-medium" :class="formatConfig[doc.format]?.color">{{ doc.format }}</span>
            <span v-if="doc.currentVersion > 1" class="tabular-nums">v{{ doc.currentVersion }}</span>
          </div>
          <span>{{ formatDate(doc.updatedAt, 'short') }}</span>
        </div>

        <!-- Linked Entity Indicator -->
        <div v-if="doc.linkedEntityId" class="absolute top-3 right-3 opacity-0 group-hover:opacity-100 transition-opacity">
          <span class="text-xs px-2 py-1 rounded-full bg-primary-100 dark:bg-primary-500/20 text-primary-600 dark:text-primary-400">
            🔗 {{ linkedEntityLabels[doc.linkedEntityType || 'other'] || 'Linked' }}
          </span>
        </div>
      </div>
    </div>

    <!-- ======================== DETAIL MODAL ======================== -->
    <Modal v-if="selectedDoc" :is-open="showDetailModal" title="Document Details" size="xl" @close="showDetailModal = false">
      <div class="space-y-5" v-if="selectedDoc">
        <!-- Header -->
        <div class="flex items-center gap-4 pb-4 border-b border-surface-200 dark:border-surface-700">
          <div class="w-14 h-14 rounded-xl flex items-center justify-center text-2xl bg-surface-100 dark:bg-surface-700">
            {{ formatConfig[selectedDoc.format]?.icon || '📎' }}
          </div>
          <div class="flex-1 min-w-0">
            <h3 class="text-lg font-bold text-surface-900 dark:text-white truncate">{{ selectedDoc.name }}</h3>
            <p class="text-sm text-surface-500 dark:text-surface-400">
              {{ selectedDoc.fileName || 'No filename' }}
              <span class="mx-1">&middot;</span>
              <span class="uppercase font-medium" :class="formatConfig[selectedDoc.format]?.color">{{ selectedDoc.format }}</span>
              <span class="mx-1">&middot;</span>
              <span class="tabular-nums">{{ formatFileSize(selectedDoc.fileSize) }}</span>
            </p>
          </div>
          <div class="flex items-center gap-2 shrink-0">
            <button @click="store.toggleFavorite(selectedDoc.id); selectedDoc = { ...selectedDoc, isFavorite: !selectedDoc.isFavorite }" class="p-2 rounded-lg hover:bg-surface-100 dark:hover:bg-surface-700 transition-colors" :title="selectedDoc.isFavorite ? 'Remove from favorites' : 'Add to favorites'">
              <span class="text-xl">{{ selectedDoc.isFavorite ? '⭐' : '☆' }}</span>
            </button>
            <button @click="store.toggleImportant(selectedDoc.id); selectedDoc = { ...selectedDoc, isImportant: !selectedDoc.isImportant }" class="p-2 rounded-lg hover:bg-surface-100 dark:hover:bg-surface-700 transition-colors" :title="selectedDoc.isImportant ? 'Unmark important' : 'Mark important'">
              <span class="text-xl">{{ selectedDoc.isImportant ? '🔴' : '⚪' }}</span>
            </button>
          </div>
        </div>

        <!-- Key Info Grid -->
        <div class="grid grid-cols-2 md:grid-cols-4 gap-3">
          <div class="bg-surface-50 dark:bg-surface-700/50 rounded-lg p-3">
            <p class="text-xs text-surface-400 mb-1">Category</p>
            <p class="text-sm font-medium text-surface-900 dark:text-white">
              {{ categoryConfig[selectedDoc.category]?.icon }} {{ categoryConfig[selectedDoc.category]?.label }}
            </p>
          </div>
          <div class="bg-surface-50 dark:bg-surface-700/50 rounded-lg p-3">
            <p class="text-xs text-surface-400 mb-1">Status</p>
            <Badge :variant="statusConfig[selectedDoc.status]?.variant || 'neutral'">
              {{ statusConfig[selectedDoc.status]?.label || selectedDoc.status }}
            </Badge>
          </div>
          <div class="bg-surface-50 dark:bg-surface-700/50 rounded-lg p-3">
            <p class="text-xs text-surface-400 mb-1">Version</p>
            <p class="text-sm font-medium text-surface-900 dark:text-white tabular-nums">v{{ selectedDoc.currentVersion }}</p>
          </div>
          <div class="bg-surface-50 dark:bg-surface-700/50 rounded-lg p-3">
            <p class="text-xs text-surface-400 mb-1">Size</p>
            <p class="text-sm font-medium text-surface-900 dark:text-white tabular-nums">{{ formatFileSize(selectedDoc.fileSize) }}</p>
          </div>
        </div>

        <!-- Description -->
        <div v-if="selectedDoc.description" class="bg-surface-50 dark:bg-surface-900 rounded-lg p-4">
          <h4 class="text-sm font-semibold text-surface-700 dark:text-surface-300 mb-2">Description</h4>
          <p class="text-sm text-surface-600 dark:text-surface-400">{{ selectedDoc.description }}</p>
        </div>

        <!-- Document Info -->
        <div class="bg-surface-50 dark:bg-surface-900 rounded-lg p-4">
          <h4 class="text-sm font-semibold text-surface-700 dark:text-surface-300 mb-3">Document Information</h4>
          <div class="grid grid-cols-2 md:grid-cols-3 gap-3 text-sm">
            <div>
              <span class="text-xs text-surface-400">Document Date</span>
              <p class="font-medium text-surface-900 dark:text-white">{{ selectedDoc.documentDate ? formatDate(selectedDoc.documentDate, 'long') : '—' }}</p>
            </div>
            <div>
              <span class="text-xs text-surface-400">Expiry Date</span>
              <p class="font-medium" :class="isOverdue(selectedDoc) ? 'text-danger-500' : 'text-surface-900 dark:text-white'">
                {{ selectedDoc.expiryDate ? formatDate(selectedDoc.expiryDate, 'long') : '—' }}
                <span v-if="isExpiringSoon(selectedDoc) && !isOverdue(selectedDoc)" class="text-warning-500 text-xs ml-1">({{ daysUntil(selectedDoc.expiryDate || '') }} days left)</span>
                <span v-if="isOverdue(selectedDoc)" class="text-danger-500 text-xs ml-1">(Expired)</span>
              </p>
            </div>
            <div>
              <span class="text-xs text-surface-400">Reminder Before</span>
              <p class="font-medium text-surface-900 dark:text-white">{{ selectedDoc.reminderBeforeDays || 30 }} days</p>
            </div>
            <div>
              <span class="text-xs text-surface-400">Uploaded By</span>
              <p class="font-medium text-surface-900 dark:text-white">{{ selectedDoc.uploadedBy || '—' }}</p>
            </div>
            <div>
              <span class="text-xs text-surface-400">Source</span>
              <p class="font-medium text-surface-900 dark:text-white capitalize">{{ selectedDoc.source || '—' }}</p>
            </div>
            <div>
              <span class="text-xs text-surface-400">Security</span>
              <p class="font-medium text-surface-900 dark:text-white">
                <span v-if="selectedDoc.isEncrypted">🔐 Encrypted</span>
                <span v-else>Unencrypted</span>
              </p>
            </div>
            <div v-if="selectedDoc.sharedWith">
              <span class="text-xs text-surface-400">Shared With</span>
              <p class="font-medium text-surface-900 dark:text-white text-xs">{{ selectedDoc.sharedWith }}</p>
            </div>
            <div v-if="selectedDoc.linkedEntityId">
              <span class="text-xs text-surface-400">Linked To</span>
              <p class="font-medium text-surface-900 dark:text-white">
                🔗 {{ linkedEntityLabels[selectedDoc.linkedEntityType || 'other'] || 'Entity' }}
                <span class="text-xs text-surface-400 ml-1">{{ selectedDoc.linkedEntityId }}</span>
              </p>
            </div>
            <div>
              <span class="text-xs text-surface-400">Created</span>
              <p class="font-medium text-surface-900 dark:text-white">{{ formatDate(selectedDoc.createdAt, 'long') }}</p>
            </div>
            <div>
              <span class="text-xs text-surface-400">Last Updated</span>
              <p class="font-medium text-surface-900 dark:text-white">{{ formatDate(selectedDoc.updatedAt, 'long') }}</p>
            </div>
          </div>
        </div>

        <!-- Tags -->
        <div v-if="selectedDoc.tags.length > 0">
          <h4 class="text-sm font-semibold text-surface-700 dark:text-surface-300 mb-2">Tags</h4>
          <div class="flex flex-wrap gap-2">
            <span v-for="tag in selectedDoc.tags" :key="tag" class="text-sm px-2.5 py-1 rounded-lg bg-primary-50 dark:bg-primary-500/10 text-primary-600 dark:text-primary-400">
              {{ tag }}
            </span>
          </div>
        </div>

        <!-- Version History -->
        <div v-if="selectedDoc.versions.length > 1">
          <h4 class="text-sm font-semibold text-surface-700 dark:text-surface-300 mb-3">Version History ({{ selectedDoc.versions.length }})</h4>
          <div class="max-h-48 overflow-y-auto space-y-2">
            <div v-for="ver in [...selectedDoc.versions].reverse()" :key="ver.versionNumber" class="flex items-center justify-between bg-surface-50 dark:bg-surface-700/50 rounded-lg px-4 py-2.5 text-sm">
              <div class="flex items-center gap-3">
                <Badge variant="info" class="text-xs tabular-nums">v{{ ver.versionNumber }}</Badge>
                <span class="text-surface-600 dark:text-surface-400">{{ formatDate(ver.date, 'short') }}</span>
                <span class="text-surface-400 text-xs">{{ ver.note || '' }}</span>
              </div>
              <span class="tabular-nums text-surface-500 text-xs">{{ formatFileSize(ver.fileSize) }}</span>
            </div>
          </div>
        </div>

        <!-- Notes -->
        <div v-if="selectedDoc.notes">
          <h4 class="text-sm font-semibold text-surface-700 dark:text-surface-300 mb-1">Notes</h4>
          <p class="text-sm text-surface-600 dark:text-surface-400">{{ selectedDoc.notes }}</p>
        </div>

        <!-- Actions -->
        <div class="flex flex-wrap gap-3 pt-2 border-t border-surface-200 dark:border-surface-700">
          <button class="btn-secondary" @click="handleArchive(selectedDoc)">
            {{ selectedDoc.status === 'archived' ? 'Restore' : 'Archive' }}
          </button>
          <button class="btn-danger" @click="showDeleteConfirm = true">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/></svg>
            Delete
          </button>
        </div>
      </div>
    </Modal>

    <!-- ======================== ADD DOCUMENT MODAL ======================== -->
    <Modal :is-open="showAddModal" title="Add Document" size="xl" @close="showAddModal = false">
      <div class="space-y-5">
        <!-- Basic Details -->
        <div>
          <h4 class="text-sm font-semibold text-surface-900 dark:text-white mb-3">Basic Details</h4>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div class="md:col-span-2">
              <label class="field-label">Document Name *</label>
              <input v-model="addForm.name" type="text" class="input-field" placeholder="e.g., Tax Return FY 2024-25" />
            </div>
            <div>
              <label class="field-label">Category</label>
              <select v-model="addForm.category" class="input-field">
                <option value="tax_return">🧾 Tax Return</option>
                <option value="insurance_policy">🛡️ Insurance Policy</option>
                <option value="property_deed">🏠 Property Deed</option>
                <option value="bank_statement">🏦 Bank Statement</option>
                <option value="investment_statement">📈 Investment Statement</option>
                <option value="loan_document">📋 Loan Document</option>
                <option value="contract">📝 Contract</option>
                <option value="receipt">🧾 Receipt</option>
                <option value="invoice">📄 Invoice</option>
                <option value="id_proof">🪪 ID Proof</option>
                <option value="medical_record">🏥 Medical Record</option>
                <option value="education_certificate">🎓 Education Certificate</option>
                <option value="vehicle_registration">🚗 Vehicle Registration</option>
                <option value="other">📎 Other</option>
              </select>
            </div>
            <div>
              <label class="field-label">Format</label>
              <select v-model="addForm.format" class="input-field">
                <option value="pdf">📕 PDF</option>
                <option value="doc">📘 DOC</option>
                <option value="docx">📘 DOCX</option>
                <option value="xls">📗 XLS</option>
                <option value="xlsx">📗 XLSX</option>
                <option value="jpg">🖼️ JPG</option>
                <option value="jpeg">🖼️ JPEG</option>
                <option value="png">🖼️ PNG</option>
                <option value="csv">📊 CSV</option>
                <option value="txt">📄 TXT</option>
                <option value="zip">🗜️ ZIP</option>
                <option value="other">📎 Other</option>
              </select>
            </div>
            <div class="md:col-span-2">
              <label class="field-label">Description</label>
              <textarea v-model="addForm.description" class="input-field" rows="2" placeholder="Brief description of the document..."></textarea>
            </div>
            <div>
              <label class="field-label">Filename</label>
              <input v-model="addForm.fileName" type="text" class="input-field" placeholder="e.g., Tax_Return_2025.pdf" />
            </div>
            <div>
              <label class="field-label">File Size (bytes)</label>
              <input v-model.number="addForm.fileSize" type="number" class="input-field" placeholder="e.g., 2458624" min="0" />
            </div>
            <div>
              <label class="field-label">Source</label>
              <select v-model="addForm.source" class="input-field">
                <option value="upload">Upload</option>
                <option value="email">Email</option>
                <option value="download">Download</option>
                <option value="scanned">Scanned</option>
                <option value="other">Other</option>
              </select>
            </div>
            <div>
              <label class="field-label">Status</label>
              <select v-model="addForm.status" class="input-field">
                <option value="active">Active</option>
                <option value="draft">Draft</option>
                <option value="archived">Archived</option>
              </select>
            </div>
          </div>
        </div>

        <!-- Dates -->
        <div>
          <h4 class="text-sm font-semibold text-surface-900 dark:text-white mb-3">Dates</h4>
          <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label class="field-label">Document Date</label>
              <input v-model="addForm.documentDate" type="date" class="input-field" />
            </div>
            <div>
              <label class="field-label">Expiry Date</label>
              <input v-model="addForm.expiryDate" type="date" class="input-field" />
            </div>
            <div>
              <label class="field-label">Reminder Before (days)</label>
              <input v-model.number="addForm.reminderBeforeDays" type="number" class="input-field" placeholder="30" min="0" />
            </div>
          </div>
        </div>

        <!-- Tags & Flags -->
        <div>
          <h4 class="text-sm font-semibold text-surface-900 dark:text-white mb-3">Tags & Flags</h4>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label class="field-label">Tags (comma-separated)</label>
              <input v-model="addForm.tags" type="text" class="input-field" placeholder="e.g., tax, nbr, fy2025" />
            </div>
            <div class="flex items-end gap-4">
              <label class="flex items-center gap-2 cursor-pointer">
                <input type="checkbox" v-model="addForm.isFavorite" class="rounded border-surface-300 dark:border-surface-600 text-primary-600 focus:ring-primary-500" />
                <span class="text-sm text-surface-700 dark:text-surface-300">⭐ Favorite</span>
              </label>
              <label class="flex items-center gap-2 cursor-pointer">
                <input type="checkbox" v-model="addForm.isImportant" class="rounded border-surface-300 dark:border-surface-600 text-primary-600 focus:ring-primary-500" />
                <span class="text-sm text-surface-700 dark:text-surface-300">🔴 Important</span>
              </label>
              <label class="flex items-center gap-2 cursor-pointer">
                <input type="checkbox" v-model="addForm.isEncrypted" class="rounded border-surface-300 dark:border-surface-600 text-primary-600 focus:ring-primary-500" />
                <span class="text-sm text-surface-700 dark:text-surface-300">🔐 Encrypted</span>
              </label>
            </div>
          </div>
        </div>

        <!-- Linked Entity -->
        <div>
          <h4 class="text-sm font-semibold text-surface-900 dark:text-white mb-3">Linked Entity (Optional)</h4>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label class="field-label">Entity Type</label>
              <select v-model="addForm.linkedEntityType" class="input-field">
                <option value="">— None —</option>
                <option value="insurance">Insurance Policy</option>
                <option value="loan">Loan</option>
                <option value="mortgage">Mortgage</option>
                <option value="asset">Asset</option>
                <option value="investment">Investment</option>
                <option value="lending">Lending</option>
                <option value="invoice">Invoice</option>
                <option value="other">Other</option>
              </select>
            </div>
            <div>
              <label class="field-label">Entity ID</label>
              <input v-model="addForm.linkedEntityId" type="text" class="input-field" placeholder="e.g., ins_001, ast_001" :disabled="!addForm.linkedEntityType" />
            </div>
          </div>
        </div>

        <!-- Notes -->
        <div>
          <label class="field-label">Notes</label>
          <textarea v-model="addForm.notes" class="input-field" rows="2" placeholder="Any additional notes..."></textarea>
        </div>

        <!-- Submit -->
        <div class="flex justify-end gap-3 pt-2 border-t border-surface-200 dark:border-surface-700">
          <button class="btn-secondary" @click="showAddModal = false">Cancel</button>
          <button class="btn-primary" @click="submitAddDocument" :disabled="!addForm.name">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/></svg>
            Add Document
          </button>
        </div>
      </div>
    </Modal>

    <!-- ======================== DELETE CONFIRM MODAL ======================== -->
    <Modal :is-open="showDeleteConfirm" title="Delete Document" size="sm" @close="showDeleteConfirm = false">
      <div class="space-y-4">
        <div class="flex items-center gap-3 p-4 bg-danger-50 dark:bg-danger-500/10 rounded-lg">
          <svg class="w-6 h-6 text-danger-500 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z"/></svg>
          <p class="text-sm text-danger-700 dark:text-danger-300">
            Are you sure you want to delete <strong>"{{ selectedDoc?.name }}"</strong>? This action cannot be undone.
          </p>
        </div>
        <div class="flex justify-end gap-3">
          <button class="btn-secondary" @click="showDeleteConfirm = false">Cancel</button>
          <button class="btn-danger" @click="confirmDelete">Delete</button>
        </div>
      </div>
    </Modal>
  </div>
</template>

<style scoped>
.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.sort-btn {
  font-size: 0.75rem;
  line-height: 1rem;
  padding: 0.375rem 0.625rem;
  border-radius: 0.5rem;
  color: var(--color-surface-500, #6b7280);
  font-weight: 500;
  transition: all 0.15s;
  background: transparent;
  border: none;
  cursor: pointer;
}
.sort-btn:hover {
  color: var(--color-surface-900, #111827);
  background: var(--color-surface-100, #f3f4f6);
}
:deep(.dark) .sort-btn:hover {
  color: var(--color-dark-white, #fff);
  background: var(--color-dark-surface-700, #1e293b);
}
.sort-btn.active {
  color: var(--color-primary-600, #2563eb);
  background: var(--color-primary-100, #dbeafe);
}
:deep(.dark) .sort-btn.active {
  color: var(--color-dark-primary-400, #60a5fa);
  background: var(--color-dark-primary-500/20, rgba(59, 130, 246, 0.2));
}
</style>
