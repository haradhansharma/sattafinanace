import '../lib/pinia-init';
import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import type { DocumentVaultItem, DocumentCategory, DocumentStatus, DocumentVersion } from '../types';
import { mockDocuments } from '../mock-data';
import { generateId } from '../utils/formatters';

export const useDocumentStore = defineStore('document', () => {
  const documents = ref<DocumentVaultItem[]>(mockDocuments.map(d => ({
    ...d,
    versions: d.versions.map(v => ({ ...v })),
    tags: [...d.tags],
  })));

  // ==================== Computed ====================

  const totalDocuments = computed(() => documents.value.length);
  const totalFileSize = computed(() =>
    documents.value.reduce((sum, d) => sum + d.fileSize, 0)
  );

  const activeDocuments = computed(() =>
    documents.value.filter(d => d.status === 'active')
  );

  const favoriteDocuments = computed(() =>
    documents.value.filter(d => d.isFavorite)
  );

  const importantDocuments = computed(() =>
    documents.value.filter(d => d.isImportant)
  );

  const archivedDocuments = computed(() =>
    documents.value.filter(d => d.status === 'archived')
  );

  const expiredDocuments = computed(() =>
    documents.value.filter(d => d.status === 'expired')
  );

  const draftDocuments = computed(() =>
    documents.value.filter(d => d.status === 'draft')
  );

  // Documents expiring soon (within N days, default 30)
  const documentsExpiringSoon = computed(() => {
    const now = new Date();
    const thirtyDays = 30 * 24 * 60 * 60 * 1000;
    return documents.value.filter(d => {
      if (!d.expiryDate) return false;
      const exp = new Date(d.expiryDate);
      const daysBefore = d.reminderBeforeDays || 30;
      const alertDate = new Date(exp.getTime() - daysBefore * 24 * 60 * 60 * 1000);
      return alertDate <= now && exp > now && d.status === 'active';
    });
  });

  // Already expired active documents
  const overdueDocuments = computed(() => {
    const now = new Date();
    return documents.value.filter(d => {
      if (!d.expiryDate || d.status !== 'active') return false;
      return new Date(d.expiryDate) <= now;
    });
  });

  // Category breakdown
  const documentsByCategory = computed(() => {
    const map: Record<string, DocumentVaultItem[]> = {};
    documents.value.forEach(d => {
      if (!map[d.category]) map[d.category] = [];
      map[d.category].push(d);
    });
    return map;
  });

  const categoryCounts = computed(() => {
    const map = {} as Record<string, number>;
    documents.value.forEach(d => {
      map[d.category] = (map[d.category] || 0) + 1;
    });
    return map;
  });

  // Format breakdown
  const formatCounts = computed(() => {
    const map = {} as Record<string, number>;
    documents.value.forEach(d => {
      map[d.format] = (map[d.format] || 0) + 1;
    });
    return map;
  });

  // Total encrypted
  const encryptedCount = computed(() =>
    documents.value.filter(d => d.isEncrypted).length
  );

  // Shared documents
  const sharedDocuments = computed(() =>
    documents.value.filter(d => d.sharedWith && d.sharedWith.length > 0)
  );

  // Search
  function searchDocuments(query: string): DocumentVaultItem[] {
    const q = query.toLowerCase().trim();
    if (!q) return documents.value;
    return documents.value.filter(d =>
      d.name.toLowerCase().includes(q) ||
      d.description?.toLowerCase().includes(q) ||
      d.tags.some(t => t.toLowerCase().includes(q)) ||
      d.fileName?.toLowerCase().includes(q) ||
      d.notes?.toLowerCase().includes(q)
    );
  }

  // ==================== CRUD ====================

  function addDocument(data: Omit<DocumentVaultItem, 'id' | 'createdAt' | 'updatedAt' | 'versions' | 'currentVersion' | 'tags'>) {
    const now = new Date().toISOString();
    const doc: DocumentVaultItem = {
      ...data,
      versions: data.fileSize ? [{ versionNumber: 1, date: now.split('T')[0], fileSize: data.fileSize }] : [],
      currentVersion: 1,
      tags: data.tags || [],
      id: generateId('doc'),
      createdAt: now,
      updatedAt: now,
    };
    documents.value.unshift(doc); // newest first
    return doc;
  }

  function updateDocument(id: string, data: Partial<DocumentVaultItem>) {
    const index = documents.value.findIndex(d => d.id === id);
    if (index === -1) return null;
    documents.value[index] = {
      ...documents.value[index],
      ...data,
      id: documents.value[index].id,
      createdAt: documents.value[index].createdAt,
      versions: data.versions ?? documents.value[index].versions,
      tags: data.tags ?? documents.value[index].tags,
      updatedAt: new Date().toISOString(),
    };
    return documents.value[index];
  }

  function deleteDocument(id: string) {
    const index = documents.value.findIndex(d => d.id === id);
    if (index !== -1) documents.value.splice(index, 1);
  }

  function toggleFavorite(id: string) {
    const doc = documents.value.find(d => d.id === id);
    if (doc) {
      doc.isFavorite = !doc.isFavorite;
      doc.updatedAt = new Date().toISOString();
    }
  }

  function toggleImportant(id: string) {
    const doc = documents.value.find(d => d.id === id);
    if (doc) {
      doc.isImportant = !doc.isImportant;
      doc.updatedAt = new Date().toISOString();
    }
  }

  function addVersion(docId: string, version: Omit<DocumentVersion, 'versionNumber'>) {
    const doc = documents.value.find(d => d.id === docId);
    if (!doc) return;
    const newVersion: DocumentVersion = {
      ...version,
      versionNumber: doc.currentVersion + 1,
    };
    doc.versions.push(newVersion);
    doc.currentVersion = newVersion.versionNumber;
    doc.fileSize = version.fileSize;
    doc.updatedAt = new Date().toISOString();
    return doc;
  }

  function updateStatus(id: string, status: DocumentStatus) {
    const doc = documents.value.find(d => d.id === id);
    if (!doc) return;
    doc.status = status;
    doc.updatedAt = new Date().toISOString();
  }

  function archiveDocument(id: string) {
    updateStatus(id, 'archived');
  }

  function restoreDocument(id: string) {
    updateStatus(id, 'active');
  }

  function getDocumentById(id: string): DocumentVaultItem | undefined {
    return documents.value.find(d => d.id === id);
  }

  // Filter by category
  function getByCategory(category: DocumentCategory): DocumentVaultItem[] {
    return documents.value.filter(d => d.category === category);
  }

  // Filter by format
  function getByFormat(format: string): DocumentVaultItem[] {
    return documents.value.filter(d => d.format === format);
  }

  return {
    documents,
    totalDocuments,
    totalFileSize,
    activeDocuments,
    favoriteDocuments,
    importantDocuments,
    archivedDocuments,
    expiredDocuments,
    draftDocuments,
    documentsExpiringSoon,
    overdueDocuments,
    documentsByCategory,
    categoryCounts,
    formatCounts,
    encryptedCount,
    sharedDocuments,
    searchDocuments,
    addDocument,
    updateDocument,
    deleteDocument,
    toggleFavorite,
    toggleImportant,
    addVersion,
    updateStatus,
    archiveDocument,
    restoreDocument,
    getDocumentById,
    getByCategory,
    getByFormat,
  };
});
