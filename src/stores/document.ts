import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import type { DocumentVaultItem, DocumentVersion, DocumentCategory, DocumentStatus } from '../types';
import { api, fetchAllPages } from '../services/api-bridge';
import { ApiError } from '../services/api-bridge';

export const useDocumentStore = defineStore('document', () => {
  // ==================== State ====================
  const documents = ref<DocumentVaultItem[]>([]);
  const loading = ref(false);
  const error = ref<string | null>(null);

  // ==================== Fetchers ====================

  async function fetchDocuments(params?: {
    category?: string;
    status?: string;
    format?: string;
  }): Promise<void> {
    loading.value = true;
    error.value = null;
    try {
      documents.value = await fetchAllPages<DocumentVaultItem>('/document/', { params });
    } catch (err) {
      error.value = err instanceof ApiError ? err.message : 'Failed to fetch documents';
      throw err;
    } finally {
      loading.value = false;
    }
  }

  async function fetchDocumentById(id: string): Promise<DocumentVaultItem> {
    loading.value = true;
    error.value = null;
    try {
      const doc = await api.get<DocumentVaultItem>(`/document/${id}/`);
      const index = documents.value.findIndex(d => d.id === id);
      if (index !== -1) {
        documents.value[index] = doc;
      } else {
        documents.value.push(doc);
      }
      return doc;
    } catch (err) {
      error.value = err instanceof ApiError ? err.message : 'Failed to fetch document';
      throw err;
    } finally {
      loading.value = false;
    }
  }

  async function fetchDocumentVersions(documentId: string): Promise<DocumentVersion[]> {
    loading.value = true;
    error.value = null;
    try {
      return await fetchAllPages<DocumentVersion>(`/document/${documentId}/versions/`);
    } catch (err) {
      error.value = err instanceof ApiError ? err.message : 'Failed to fetch document versions';
      throw err;
    } finally {
      loading.value = false;
    }
  }

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

  const documentsExpiringSoon = computed(() => {
    const now = new Date();
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

  // ==================== CRUD ====================

  async function addDocument(data: Omit<DocumentVaultItem, 'id' | 'createdAt' | 'updatedAt' | 'versions' | 'currentVersion'>): Promise<DocumentVaultItem> {
    error.value = null;
    try {
      const doc = await api.post<DocumentVaultItem>('/document/', data);
      documents.value.unshift(doc);
      return doc;
    } catch (err) {
      error.value = err instanceof ApiError ? err.message : 'Failed to create document';
      throw err;
    }
  }

  async function updateDocument(id: string, data: Partial<DocumentVaultItem>): Promise<DocumentVaultItem | null> {
    error.value = null;
    try {
      const updated = await api.put<DocumentVaultItem>(`/document/${id}/`, data);
      const index = documents.value.findIndex(d => d.id === id);
      if (index !== -1) {
        documents.value[index] = updated;
      }
      return updated;
    } catch (err) {
      error.value = err instanceof ApiError ? err.message : 'Failed to update document';
      throw err;
    }
  }

  async function deleteDocument(id: string): Promise<void> {
    error.value = null;
    try {
      await api.delete(`/document/${id}/`);
      const index = documents.value.findIndex(d => d.id === id);
      if (index !== -1) {
        documents.value.splice(index, 1);
      }
    } catch (err) {
      error.value = err instanceof ApiError ? err.message : 'Failed to delete document';
      throw err;
    }
  }

  // ==================== Version Sub-Resource ====================

  async function addVersion(
    docId: string,
    data: Omit<DocumentVersion, 'versionNumber'>
  ): Promise<DocumentVaultItem | null> {
    error.value = null;
    try {
      await api.post<DocumentVersion>(`/document/${docId}/versions/`, data);
      return await fetchDocumentById(docId);
    } catch (err) {
      error.value = err instanceof ApiError ? err.message : 'Failed to add document version';
      throw err;
    }
  }

  // ==================== Toggle & Status Helpers ====================

  async function toggleFavorite(id: string): Promise<DocumentVaultItem | null> {
    const doc = documents.value.find(d => d.id === id);
    if (!doc) return null;
    return updateDocument(id, { isFavorite: !doc.isFavorite });
  }

  async function toggleImportant(id: string): Promise<DocumentVaultItem | null> {
    const doc = documents.value.find(d => d.id === id);
    if (!doc) return null;
    return updateDocument(id, { isImportant: !doc.isImportant });
  }

  async function updateStatus(id: string, status: DocumentStatus): Promise<DocumentVaultItem | null> {
    return updateDocument(id, { status });
  }

  async function archiveDocument(id: string): Promise<DocumentVaultItem | null> {
    return updateStatus(id, 'archived');
  }

  async function restoreDocument(id: string): Promise<DocumentVaultItem | null> {
    return updateStatus(id, 'active');
  }

  // ==================== Helpers ====================

  function getDocumentById(id: string): DocumentVaultItem | undefined {
    return documents.value.find(d => d.id === id);
  }

  function getByCategory(category: DocumentCategory): DocumentVaultItem[] {
    return documents.value.filter(d => d.category === category);
  }

  function getByFormat(format: string): DocumentVaultItem[] {
    return documents.value.filter(d => d.format === format);
  }

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

  function clearError() {
    error.value = null;
  }

  return {
    // State
    documents,
    loading,
    error,
    // Fetchers
    fetchDocuments,
    fetchDocumentById,
    fetchDocumentVersions,
    // Computed
    totalDocuments,
    totalFileSize,
    activeDocuments,
    favoriteDocuments,
    importantDocuments,
    archivedDocuments,
    expiredDocuments,
    documentsExpiringSoon,
    overdueDocuments,
    // CRUD
    addDocument,
    updateDocument,
    deleteDocument,
    // Version sub-resource
    addVersion,
    // Toggle & status
    toggleFavorite,
    toggleImportant,
    updateStatus,
    archiveDocument,
    restoreDocument,
    // Helpers
    getDocumentById,
    getByCategory,
    getByFormat,
    searchDocuments,
    clearError,
  };
});
