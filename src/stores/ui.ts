import '../lib/pinia-init';
import { defineStore } from 'pinia';
import { ref } from 'vue';

export const useUiStore = defineStore('ui', () => {
  const sidebarOpen = ref(true);
  const sidebarCollapsed = ref(false);
  const activeModal = ref<string | null>(null);
  const activeModalData = ref<any>(null);
  const loading = ref(false);
  const searchQuery = ref('');
  const currentPage = ref('dashboard');

  function toggleSidebar() {
    sidebarOpen.value = !sidebarOpen.value;
  }

  function toggleCollapse() {
    sidebarCollapsed.value = !sidebarCollapsed.value;
  }

  function openModal(modalId: string, data?: any) {
    activeModal.value = modalId;
    activeModalData.value = data || null;
  }

  function closeModal() {
    activeModal.value = null;
    activeModalData.value = null;
  }

  function setLoading(state: boolean) {
    loading.value = state;
  }

  return {
    sidebarOpen,
    sidebarCollapsed,
    activeModal,
    activeModalData,
    loading,
    searchQuery,
    currentPage,
    toggleSidebar,
    toggleCollapse,
    openModal,
    closeModal,
    setLoading,
  };
});
