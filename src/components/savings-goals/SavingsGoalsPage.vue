<script setup lang="ts">
import { ref, computed } from 'vue';
import { useSavingsGoalStore } from '../../stores/savingsGoals';
import { useBankStore } from '../../stores/bank';
import { formatCurrency, formatDate } from '../../utils/formatters';
import { PageHeader, StatCard, Badge, Modal, Tabs, SearchInput, EmptyState } from '../ui';
import type { SavingsGoal, SavingsGoalCategory, SavingsGoalStatus } from '../../types';

const store = useSavingsGoalStore();
const bankStore = useBankStore();

// ============ Tabs ============
type TabKey = 'all' | 'active' | 'completed' | 'paused' | SavingsGoalCategory;
const activeTab = ref<TabKey>('all');
const tabs = [
  { key: 'all', label: 'All Goals', icon: '🎯' },
  { key: 'active', label: 'Active', icon: '🔥' },
  { key: 'completed', label: 'Completed', icon: '✅' },
  { key: 'paused', label: 'Paused', icon: '⏸️' },
  { key: 'emergency_fund', label: 'Emergency', icon: '🛡️' },
  { key: 'vacation', label: 'Travel', icon: '✈️' },
  { key: 'home', label: 'Home', icon: '🏠' },
  { key: 'car', label: 'Car', icon: '🚗' },
  { key: 'education', label: 'Education', icon: '🎓' },
  { key: 'wedding', label: 'Wedding', icon: '💍' },
  { key: 'retirement', label: 'Retirement', icon: '🏖️' },
  { key: 'gadget', label: 'Gadgets', icon: '📱' },
  { key: 'gift', label: 'Gifts', icon: '🎁' },
  { key: 'medical', label: 'Medical', icon: '🏥' },
  { key: 'other', label: 'Other', icon: '📎' },
];

// ============ Search & Sort ============
const searchQuery = ref('');
const sortBy = ref<'progress' | 'amount' | 'name' | 'remaining'>('progress');
const sortDir = ref<'asc' | 'desc'>('desc');

// ============ Modals ============
const showDetailModal = ref(false);
const showAddModal = ref(false);
const showContributeModal = ref(false);
const showWithdrawModal = ref(false);
const showDeleteConfirm = ref(false);
const selectedGoalId = ref<string | null>(null);
const isEditMode = ref(false);

// ============ Config ============
const categoryConfig: Record<SavingsGoalCategory, { label: string; icon: string; color: string }> = {
  emergency_fund: { label: 'Emergency Fund', icon: '🛡️', color: '#10b981' },
  vacation: { label: 'Travel / Vacation', icon: '✈️', color: '#06b6d4' },
  home: { label: 'Home', icon: '🏠', color: '#f59e0b' },
  car: { label: 'Car', icon: '🚗', color: '#f97316' },
  education: { label: 'Education', icon: '🎓', color: '#6366f1' },
  wedding: { label: 'Wedding', icon: '💍', color: '#ec4899' },
  retirement: { label: 'Retirement', icon: '🏖️', color: '#14b8a6' },
  gadget: { label: 'Gadget', icon: '📱', color: '#3b82f6' },
  gift: { label: 'Gift', icon: '🎁', color: '#a855f7' },
  medical: { label: 'Medical', icon: '🏥', color: '#ef4444' },
  other: { label: 'Other', icon: '📎', color: '#64748b' },
};

const statusConfig: Record<SavingsGoalStatus, { variant: 'success' | 'danger' | 'warning' | 'info' | 'neutral'; label: string }> = {
  active: { variant: 'success', label: 'Active' },
  paused: { variant: 'warning', label: 'Paused' },
  completed: { variant: 'info', label: 'Completed' },
  abandoned: { variant: 'neutral', label: 'Abandoned' },
};

const priorityConfig = {
  high: { label: 'High', color: 'text-danger-500', dot: 'bg-danger-500' },
  medium: { label: 'Medium', color: 'text-warning-500', dot: 'bg-warning-500' },
  low: { label: 'Low', color: 'text-surface-400', dot: 'bg-surface-300' },
};

// ============ Helpers ============
function fmtCur(amount: number): string {
  return formatCurrency(amount, 'BDT');
}

// ============ Computed: Filtered ============
const filteredGoals = computed(() => {
  let list: SavingsGoal[];

  switch (activeTab.value) {
    case 'active': list = store.activeGoals; break;
    case 'completed': list = store.completedGoals; break;
    case 'paused': list = store.pausedGoals; break;
    default:
      if (activeTab.value === 'all') {
        list = store.goals;
      } else {
        list = store.getGoalsByCategory(activeTab.value as SavingsGoalCategory);
      }
  }

  if (searchQuery.value.trim()) {
    const q = searchQuery.value.toLowerCase();
    list = list.filter(g =>
      g.name.toLowerCase().includes(q) ||
      g.description?.toLowerCase().includes(q) ||
      g.tags?.some(t => t.toLowerCase().includes(q))
    );
  }

  list.sort((a, b) => {
    let cmp = 0;
    if (sortBy.value === 'progress') cmp = store.getGoalProgress(a) - store.getGoalProgress(b);
    else if (sortBy.value === 'amount') cmp = a.targetAmount - b.targetAmount;
    else if (sortBy.value === 'remaining') cmp = store.getRemainingAmount(a) - store.getRemainingAmount(b);
    else cmp = a.name.localeCompare(b.name);
    return sortDir.value === 'asc' ? cmp : -cmp;
  });

  return list;
});

const selectedGoal = computed(() => {
  if (!selectedGoalId.value) return null;
  return store.getGoalById(selectedGoalId.value) || null;
});

// ============ Add/Edit Form ============
interface GoalForm {
  name: string;
  description: string;
  category: SavingsGoalCategory;
  targetAmount: number;
  currentAmount: number;
  startDate: string;
  targetDate: string;
  monthlyContributionAmount: number;
  autoContributeEnabled: boolean;
  autoContributeDayOfMonth: number;
  motivationalQuote: string;
  coverColor: string;
  coverIcon: string;
  priority: 'low' | 'medium' | 'high';
  bankAccountId: string;
  notes: string;
  tags: string;
}

const form = ref<GoalForm>({
  name: '', description: '', category: 'emergency_fund', targetAmount: 0, currentAmount: 0,
  startDate: new Date().toISOString().split('T')[0],
  targetDate: '', monthlyContributionAmount: 0,
  autoContributeEnabled: false, autoContributeDayOfMonth: 1,
  motivationalQuote: '', coverColor: '#10b981', coverIcon: '🎯',
  priority: 'medium', bankAccountId: '', notes: '', tags: '',
});

function resetForm() {
  form.value = {
    name: '', description: '', category: 'emergency_fund', targetAmount: 0, currentAmount: 0,
    startDate: new Date().toISOString().split('T')[0],
    targetDate: '', monthlyContributionAmount: 0,
    autoContributeEnabled: false, autoContributeDayOfMonth: 1,
    motivationalQuote: '', coverColor: '#10b981', coverIcon: '🎯',
    priority: 'medium', bankAccountId: '', notes: '', tags: '',
  };
  isEditMode.value = false;
}

function openAddModal() {
  resetForm();
  showAddModal.value = true;
}

function openEditModal(goal: SavingsGoal) {
  isEditMode.value = true;
  showAddModal.value = true;
  showDetailModal.value = false;
  form.value = {
    name: goal.name,
    description: goal.description || '',
    category: goal.category,
    targetAmount: goal.targetAmount,
    currentAmount: goal.currentAmount,
    startDate: goal.startDate.split('T')[0],
    targetDate: goal.targetDate ? goal.targetDate.split('T')[0] : '',
    monthlyContributionAmount: goal.monthlyContributionAmount,
    autoContributeEnabled: goal.autoContributeEnabled,
    autoContributeDayOfMonth: goal.autoContributeDayOfMonth || 1,
    motivationalQuote: goal.motivationalQuote || '',
    coverColor: goal.coverColor || '#10b981',
    coverIcon: goal.coverIcon || '🎯',
    priority: goal.priority,
    bankAccountId: goal.bankAccountId || '',
    notes: goal.notes || '',
    tags: (goal.tags || []).join(', '),
  };
  editingGoalId.value = goal.id;
}

const editingGoalId = ref<string | null>(null);

function saveGoal() {
  if (!form.value.name.trim() || form.value.targetAmount <= 0) return;
  const tags = form.value.tags ? form.value.tags.split(',').map(t => t.trim()).filter(Boolean) : [];

  const baseData = {
    name: form.value.name.trim(),
    description: form.value.description.trim() || undefined,
    category: form.value.category,
    status: 'active' as SavingsGoalStatus,
    targetAmount: form.value.targetAmount,
    currentAmount: form.value.currentAmount || 0,
    currency: 'BDT' as const,
    startDate: new Date(form.value.startDate).toISOString(),
    targetDate: form.value.targetDate ? new Date(form.value.targetDate).toISOString() : undefined,
    monthlyContributionAmount: form.value.monthlyContributionAmount,
    autoContributeEnabled: form.value.autoContributeEnabled,
    autoContributeDayOfMonth: form.value.autoContributeEnabled ? form.value.autoContributeDayOfMonth : undefined,
    contributions: [],
    totalContributed: form.value.currentAmount || 0,
    totalWithdrawn: 0,
    contributionCount: 0,
    milestones: [],
    motivationalQuote: form.value.motivationalQuote.trim() || undefined,
    coverColor: form.value.coverColor,
    coverIcon: form.value.coverIcon,
    currentStreak: 0,
    longestStreak: 0,
    priority: form.value.priority,
    bankAccountId: form.value.bankAccountId || undefined,
    notes: form.value.notes.trim() || undefined,
    tags,
  };

  if (isEditMode.value && editingGoalId.value) {
    store.updateGoal(editingGoalId.value, baseData);
  } else {
    store.addGoal(baseData);
  }

  showAddModal.value = false;
  resetForm();
  editingGoalId.value = null;
}

// ============ Contribute / Withdraw ============
const contributeForm = ref({ amount: 0, note: '', bankAccountId: '' });
const withdrawForm = ref({ amount: 0, note: '' });
const contributingGoalId = ref<string | null>(null);
const withdrawingGoalId = ref<string | null>(null);

function openContributeModal(goal: SavingsGoal) {
  contributeForm.value = { amount: goal.monthlyContributionAmount, note: '', bankAccountId: goal.bankAccountId || '' };
  contributingGoalId.value = goal.id;
  showContributeModal.value = true;
  showDetailModal.value = false;
}

function openWithdrawModal(goal: SavingsGoal) {
  withdrawForm.value = { amount: 0, note: '' };
  withdrawingGoalId.value = goal.id;
  showWithdrawModal.value = true;
  showDetailModal.value = false;
}

function submitContribution() {
  if (!contributingGoalId.value || contributeForm.value.amount <= 0) return;
  store.addContribution(
    contributingGoalId.value,
    contributeForm.value.amount,
    contributeForm.value.note.trim() || undefined,
    contributeForm.value.bankAccountId || undefined,
  );
  showContributeModal.value = false;
  contributingGoalId.value = null;
}

function submitWithdrawal() {
  if (!withdrawingGoalId.value || withdrawForm.value.amount <= 0) return;
  store.withdrawFromGoal(
    withdrawingGoalId.value,
    withdrawForm.value.amount,
    withdrawForm.value.note.trim() || undefined,
  );
  showWithdrawModal.value = false;
  withdrawingGoalId.value = null;
}

// ============ Actions ============
function openDetail(id: string) {
  selectedGoalId.value = id;
  showDetailModal.value = true;
}

function confirmDelete() {
  if (!selectedGoalId.value) return;
  store.deleteGoal(selectedGoalId.value);
  showDeleteConfirm.value = false;
  showDetailModal.value = false;
  selectedGoalId.value = null;
}

function handlePause(goalId: string) {
  store.pauseGoal(goalId);
  showDetailModal.value = false;
  selectedGoalId.value = null;
}

function handleResume(goalId: string) {
  store.resumeGoal(goalId);
  showDetailModal.value = false;
  selectedGoalId.value = null;
}

function handleAbandon(goalId: string) {
  store.abandonGoal(goalId);
  showDetailModal.value = false;
  selectedGoalId.value = null;
}

// ============ Celebrate ============
const justCompletedId = ref<string | null>(null);

function celebrate(goal: SavingsGoal) {
  store.addContribution(goal.id, store.getRemainingAmount(goal), 'Final contribution - Goal reached!');
  justCompletedId.value = goal.id;
  setTimeout(() => { justCompletedId.value = null; }, 5000);
}
</script>

<template>
  <div class="animate-fade-in space-y-6">
    <!-- Page Header -->
    <PageHeader title="Savings Goals" subtitle="Set goals, track progress, and stay motivated on your financial journey!">
      <template #actions>
        <button class="btn-primary" @click="openAddModal()">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/></svg>
          New Goal
        </button>
      </template>
    </PageHeader>

    <!-- Motivational Banner -->
    <div class="relative overflow-hidden rounded-2xl bg-gradient-to-r from-primary-600 via-accent-500 to-primary-700 p-6 text-white">
      <div class="absolute inset-0 opacity-10" style="background-image: radial-gradient(circle at 25% 50%, white 1px, transparent 1px), radial-gradient(circle at 75% 50%, white 1px, transparent 1px); background-size: 50px 50px;"></div>
      <div class="relative flex flex-col md:flex-row items-center gap-6">
        <div class="flex-1 text-center md:text-left">
          <h2 class="text-2xl font-bold mb-2">
            {{ store.getMotivationalMessage(store.overallProgress).emoji }}
            {{ store.getMotivationalMessage(store.overallProgress).message }}
          </h2>
          <p class="text-white/80 text-sm">You have saved {{ fmtCur(store.totalSaved) }} towards your dreams. Keep it up!</p>
        </div>
        <div class="flex-shrink-0">
          <svg :width="100" :height="100" viewBox="0 0 100 100" class="transform -rotate-90">
            <circle cx="50" cy="50" r="42" stroke="rgba(255,255,255,0.2)" stroke-width="8" fill="none"/>
            <circle cx="50" cy="50" r="42" stroke="white" stroke-width="8" fill="none"
              stroke-linecap="round"
              :stroke-dasharray="2 * Math.PI * 42"
              :stroke-dashoffset="2 * Math.PI * 42 * (1 - Math.min(store.overallProgress, 100) / 100)"
              class="transition-all duration-1000"
            />
            <text x="50" y="48" text-anchor="middle" fill="white" font-size="18" font-weight="bold" class="transform rotate-90 origin-center">{{ store.overallProgress }}%</text>
            <text x="50" y="62" text-anchor="middle" fill="rgba(255,255,255,0.7)" font-size="8" class="transform rotate-90 origin-center">overall</text>
          </svg>
        </div>
      </div>
    </div>

    <!-- Stat Cards -->
    <div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-4">
      <StatCard title="Total Saved" :value="fmtCur(store.totalSaved)" icon="💰" color="primary" />
      <StatCard title="Total Target" :value="fmtCur(store.totalTarget)" icon="🎯" color="accent" />
      <StatCard title="Active Goals" :value="String(store.activeGoals.length)" icon="🔥" color="warning" />
      <StatCard title="Completed" :value="String(store.completedCount)" icon="✅" color="success" />
      <StatCard title="Monthly Plan" :value="fmtCur(store.totalMonthlyContributions)" icon="📅" color="info" />
    </div>

    <!-- Almost There Alert -->
    <div v-if="store.almostThereGoals.length > 0" class="bg-accent-50 dark:bg-accent-500/10 border border-accent-200 dark:border-accent-500/30 rounded-xl p-4">
      <div class="flex items-center gap-3 mb-2">
        <span class="text-2xl">🔥</span>
        <h4 class="font-semibold text-accent-700 dark:text-accent-300">Almost There! ({{ store.almostThereGoals.length }} goals at 70%+)</h4>
      </div>
      <div class="space-y-2">
        <div v-for="goal in store.almostThereGoals.slice(0, 3)" :key="goal.id" class="flex items-center justify-between text-sm">
          <span class="text-accent-600 dark:text-accent-400">
            {{ goal.coverIcon }} {{ goal.name }}
            <span class="ml-1 font-medium">{{ store.getGoalProgress(goal) }}%</span>
            <span class="ml-1 text-xs text-accent-500">- {{ fmtCur(store.getRemainingAmount(goal)) }} left</span>
          </span>
          <button @click="openContributeModal(goal)" class="text-accent-600 dark:text-accent-400 hover:underline text-xs font-medium">Contribute</button>
        </div>
      </div>
    </div>

    <!-- Tabs -->
    <Tabs :tabs="tabs" v-model:activeTab="activeTab" />

    <!-- Search + Sort -->
    <div class="flex flex-col sm:flex-row gap-3">
      <div class="flex-1">
        <SearchInput v-model="searchQuery" placeholder="Search goals by name, description, tags..." />
      </div>
      <div class="flex gap-2">
        <select v-model="sortBy" class="input-field w-auto text-sm">
          <option value="progress">Sort: Progress</option>
          <option value="amount">Sort: Target</option>
          <option value="remaining">Sort: Remaining</option>
          <option value="name">Sort: Name</option>
        </select>
        <button @click="sortDir = sortDir === 'asc' ? 'desc' : 'asc'" class="px-3 py-2 rounded-lg border border-surface-200 dark:border-surface-700 text-surface-600 dark:text-surface-300 hover:bg-surface-100 dark:hover:bg-surface-700 transition-colors text-sm">
          {{ sortDir === 'asc' ? '↑' : '↓' }}
        </button>
      </div>
    </div>

    <!-- Goal Cards Grid -->
    <div v-if="filteredGoals.length === 0">
      <EmptyState icon="🎯" title="No savings goals found" :description="searchQuery ? 'Try adjusting your search or filter' : 'Create your first savings goal to start your journey!'">
        <template #action>
          <button class="btn-primary" @click="openAddModal()">Create Goal</button>
        </template>
      </EmptyState>
    </div>

    <div v-else class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-5">
      <div
        v-for="goal in filteredGoals"
        :key="goal.id"
        class="card overflow-hidden hover:shadow-lg transition-all duration-300 cursor-pointer group"
        :class="{ 'ring-2 ring-accent-500': justCompletedId === goal.id }"
        @click="openDetail(goal.id)"
      >
        <!-- Card Header with accent color -->
        <div class="h-2" :style="{ backgroundColor: goal.coverColor || categoryConfig[goal.category]?.color }"></div>

        <div class="p-5">
          <!-- Top: Icon + Status + Priority -->
          <div class="flex items-start justify-between mb-4">
            <div class="flex items-center gap-3">
              <div class="w-12 h-12 rounded-xl flex items-center justify-center text-2xl" :style="{ backgroundColor: (goal.coverColor || categoryConfig[goal.category]?.color) + '18' }">
                {{ goal.coverIcon || categoryConfig[goal.category]?.icon }}
              </div>
              <div>
                <h3 class="font-bold text-surface-900 dark:text-white text-sm leading-tight">{{ goal.name }}</h3>
                <div class="flex items-center gap-2 mt-1 flex-wrap">
                  <span class="text-xs px-1.5 py-0.5 rounded-full" :style="{ backgroundColor: (goal.coverColor || categoryConfig[goal.category]?.color) + '18', color: goal.coverColor || categoryConfig[goal.category]?.color }">
                    {{ categoryConfig[goal.category]?.icon }} {{ categoryConfig[goal.category]?.label }}
                  </span>
                  <Badge :variant="statusConfig[goal.status]?.variant || 'neutral'" size="sm">
                    {{ statusConfig[goal.status]?.label }}
                  </Badge>
                </div>
              </div>
            </div>
            <div v-if="goal.priority === 'high'" class="w-2.5 h-2.5 rounded-full bg-danger-500 mt-1" title="High Priority"></div>
          </div>

          <!-- Circular Progress -->
          <div class="flex items-center gap-5 my-4">
            <div class="relative flex-shrink-0">
              <svg :width="80" :height="80" viewBox="0 0 80 80" class="transform -rotate-90">
                <circle cx="40" cy="40" r="34" stroke-width="5" fill="none" class="stroke-surface-200 dark:stroke-surface-700"/>
                <circle
                  cx="40" cy="40" r="34"
                  :stroke="goal.coverColor || categoryConfig[goal.category]?.color"
                  stroke-width="5" fill="none"
                  stroke-linecap="round"
                  :stroke-dasharray="2 * Math.PI * 34"
                  :stroke-dashoffset="2 * Math.PI * 34 * (1 - Math.min(store.getGoalProgress(goal), 100) / 100)"
                  class="transition-all duration-700"
                />
              </svg>
              <div class="absolute inset-0 flex items-center justify-center">
                <span class="text-lg font-bold text-surface-900 dark:text-white">{{ store.getGoalProgress(goal) }}%</span>
              </div>
            </div>
            <div class="flex-1 min-w-0">
              <div class="space-y-1.5">
                <div class="flex items-baseline justify-between">
                  <span class="text-xs text-surface-400">Saved</span>
                  <span class="font-bold text-surface-900 dark:text-white text-sm tabular-nums">{{ fmtCur(goal.currentAmount) }}</span>
                </div>
                <div class="flex items-baseline justify-between">
                  <span class="text-xs text-surface-400">Target</span>
                  <span class="text-surface-500 text-xs tabular-nums">{{ fmtCur(goal.targetAmount) }}</span>
                </div>
                <div class="flex items-baseline justify-between">
                  <span class="text-xs text-surface-400">Remaining</span>
                  <span class="font-medium text-xs tabular-nums" :class="store.getRemainingAmount(goal) > 0 ? 'text-warning-500' : 'text-green-500'">{{ fmtCur(store.getRemainingAmount(goal)) }}</span>
                </div>
              </div>
            </div>
          </div>

          <!-- Motivational Message -->
          <div class="bg-surface-50 dark:bg-surface-700/50 rounded-lg px-3 py-2 mb-3">
            <p class="text-xs text-surface-600 dark:text-surface-400 text-center">
              {{ store.getMotivationalMessage(store.getGoalProgress(goal)).emoji }}
              {{ goal.motivationalQuote || store.getMotivationalMessage(store.getGoalProgress(goal)).message }}
            </p>
          </div>

          <!-- Milestones -->
          <div class="flex items-center gap-1 mb-2">
            <div
              v-for="ms in goal.milestones"
              :key="ms.id"
              class="flex-1 h-1.5 rounded-full transition-all duration-500"
              :class="ms.achieved ? '' : 'bg-surface-200 dark:bg-surface-700'"
              :style="ms.achieved ? { backgroundColor: goal.coverColor || categoryConfig[goal.category]?.color } : {}"
              :title="ms.label + (ms.achieved ? ' - Achieved!' : '')"
            ></div>
          </div>
          <div class="flex items-center justify-between text-xs text-surface-400 mb-3">
            <span>Progress Milestones</span>
            <span v-if="store.getLatestMilestone(goal)" class="font-medium" :style="{ color: goal.coverColor || categoryConfig[goal.category]?.color }">
              {{ store.getLatestMilestone(goal)?.label }}
            </span>
          </div>

          <!-- Footer: Meta -->
          <div class="flex items-center justify-between text-xs text-surface-400 border-t border-surface-100 dark:border-surface-700 pt-3">
            <div class="flex items-center gap-3">
              <span v-if="goal.monthlyContributionAmount > 0" class="flex items-center gap-1">
                <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/></svg>
                {{ fmtCur(goal.monthlyContributionAmount) }}/mo
              </span>
              <span :class="store.getTrackStatus(goal).css">
                {{ store.getTrackStatus(goal).label }}
              </span>
            </div>
            <div class="flex items-center gap-2">
              <span v-if="goal.currentStreak > 0" class="flex items-center gap-1 text-orange-500">
                🔥 {{ goal.currentStreak }}mo
              </span>
              <span v-if="store.getDaysRemaining(goal) !== null">
                {{ store.getDaysRemaining(goal) }}d left
              </span>
            </div>
          </div>

          <!-- Quick Actions -->
          <div class="flex gap-2 mt-3" @click.stop>
            <button
              v-if="goal.status === 'active' && store.getRemainingAmount(goal) > 0"
              @click.stop="openContributeModal(goal)"
              class="flex-1 text-xs px-3 py-2 rounded-lg bg-accent-50 dark:bg-accent-500/20 text-accent-600 dark:text-accent-400 hover:bg-accent-100 dark:hover:bg-accent-500/30 transition-colors font-medium text-center"
            >
              + Contribute
            </button>
            <button
              v-if="goal.status === 'active' && goal.currentAmount > 0"
              @click.stop="openWithdrawModal(goal)"
              class="text-xs px-3 py-2 rounded-lg bg-surface-100 dark:bg-surface-700 text-surface-500 hover:bg-surface-200 dark:hover:bg-surface-600 transition-colors font-medium"
            >
              Withdraw
            </button>
            <button
              @click.stop="openDetail(goal.id)"
              class="text-xs px-3 py-2 rounded-lg bg-surface-100 dark:bg-surface-700 text-surface-500 hover:bg-surface-200 dark:hover:bg-surface-600 transition-colors font-medium"
            >
              View
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- ==================== DETAIL MODAL ==================== -->
    <Modal v-if="selectedGoal" :is-open="showDetailModal" :title="selectedGoal.name" size="xl" @close="showDetailModal = false">
      <div class="space-y-5" v-if="selectedGoal">
        <!-- Header -->
        <div class="flex items-center gap-4 pb-4 border-b border-surface-200 dark:border-surface-700">
          <div class="w-14 h-14 rounded-xl flex items-center justify-center text-2xl" :style="{ backgroundColor: (selectedGoal.coverColor || categoryConfig[selectedGoal.category]?.color) + '20' }">
            {{ selectedGoal.coverIcon || categoryConfig[selectedGoal.category]?.icon }}
          </div>
          <div class="flex-1">
            <h3 class="text-lg font-bold text-surface-900 dark:text-white">{{ selectedGoal.name }}</h3>
            <p class="text-sm text-surface-500">
              {{ categoryConfig[selectedGoal.category]?.label }}
              <span class="mx-1">&middot;</span>
              <span :class="priorityConfig[selectedGoal.priority]?.color">{{ priorityConfig[selectedGoal.priority]?.label }} priority</span>
            </p>
          </div>
          <Badge :variant="statusConfig[selectedGoal.status]?.variant || 'neutral'" size="lg">
            {{ statusConfig[selectedGoal.status]?.label }}
          </Badge>
        </div>

        <!-- Large Progress Ring -->
        <div class="flex flex-col items-center py-4">
          <div class="relative">
            <svg :width="140" :height="140" viewBox="0 0 140 140" class="transform -rotate-90">
              <circle cx="70" cy="70" r="58" stroke-width="10" fill="none" class="stroke-surface-200 dark:stroke-surface-700"/>
              <circle
                cx="70" cy="70" r="58"
                :stroke="selectedGoal.coverColor || categoryConfig[selectedGoal.category]?.color"
                stroke-width="10" fill="none"
                stroke-linecap="round"
                :stroke-dasharray="2 * Math.PI * 58"
                :stroke-dashoffset="2 * Math.PI * 58 * (1 - Math.min(store.getGoalProgress(selectedGoal), 100) / 100)"
                class="transition-all duration-700"
              />
            </svg>
            <div class="absolute inset-0 flex flex-col items-center justify-center">
              <span class="text-3xl font-bold text-surface-900 dark:text-white">{{ store.getGoalProgress(selectedGoal) }}%</span>
              <span class="text-xs text-surface-400 mt-0.5">Complete</span>
            </div>
          </div>
          <div class="mt-3 text-center">
            <p class="text-2xl font-bold text-surface-900 dark:text-white tabular-nums">{{ fmtCur(selectedGoal.currentAmount) }}</p>
            <p class="text-sm text-surface-400">of {{ fmtCur(selectedGoal.targetAmount) }}</p>
          </div>
        </div>

        <!-- Motivational Quote -->
        <div class="rounded-xl p-4 text-center" :style="{ backgroundColor: (selectedGoal.coverColor || categoryConfig[selectedGoal.category]?.color) + '12' }">
          <p class="text-sm font-medium" :style="{ color: selectedGoal.coverColor || categoryConfig[selectedGoal.category]?.color }">
            {{ store.getMotivationalMessage(store.getGoalProgress(selectedGoal)).emoji }}
            {{ selectedGoal.motivationalQuote || store.getMotivationalMessage(store.getGoalProgress(selectedGoal)).message }}
          </p>
        </div>

        <!-- Stats Grid -->
        <div class="grid grid-cols-2 md:grid-cols-3 gap-3">
          <div class="bg-surface-50 dark:bg-surface-700/50 rounded-lg p-3">
            <p class="text-xs text-surface-400 mb-1">Monthly Plan</p>
            <p class="font-bold text-surface-900 dark:text-white text-sm tabular-nums">{{ fmtCur(selectedGoal.monthlyContributionAmount) }}/mo</p>
          </div>
          <div class="bg-surface-50 dark:bg-surface-700/50 rounded-lg p-3">
            <p class="text-xs text-surface-400 mb-1">Remaining</p>
            <p class="font-bold text-warning-500 text-sm tabular-nums">{{ fmtCur(store.getRemainingAmount(selectedGoal)) }}</p>
          </div>
          <div class="bg-surface-50 dark:bg-surface-700/50 rounded-lg p-3">
            <p class="text-xs text-surface-400 mb-1">Track Status</p>
            <p class="font-bold text-sm" :class="store.getTrackStatus(selectedGoal).css">{{ store.getTrackStatus(selectedGoal).label }}</p>
          </div>
          <div class="bg-surface-50 dark:bg-surface-700/50 rounded-lg p-3">
            <p class="text-xs text-surface-400 mb-1">Projected Completion</p>
            <p class="font-semibold text-surface-900 dark:text-white text-sm">{{ store.getProjectedCompletionDate(selectedGoal) || 'N/A' }}</p>
          </div>
          <div v-if="store.getDaysRemaining(selectedGoal) !== null" class="bg-surface-50 dark:bg-surface-700/50 rounded-lg p-3">
            <p class="text-xs text-surface-400 mb-1">Days Remaining</p>
            <p class="font-bold text-surface-900 dark:text-white text-sm">{{ store.getDaysRemaining(selectedGoal) }} days</p>
          </div>
          <div class="bg-surface-50 dark:bg-surface-700/50 rounded-lg p-3">
            <p class="text-xs text-surface-400 mb-1">Streak</p>
            <p class="font-bold text-orange-500 text-sm">🔥 {{ selectedGoal.currentStreak }} mo (best: {{ selectedGoal.longestStreak }})</p>
          </div>
          <div class="bg-surface-50 dark:bg-surface-700/50 rounded-lg p-3">
            <p class="text-xs text-surface-400 mb-1">Total Contributed</p>
            <p class="font-bold text-green-500 text-sm tabular-nums">{{ fmtCur(selectedGoal.totalContributed) }}</p>
          </div>
          <div v-if="selectedGoal.totalWithdrawn > 0" class="bg-surface-50 dark:bg-surface-700/50 rounded-lg p-3">
            <p class="text-xs text-surface-400 mb-1">Total Withdrawn</p>
            <p class="font-bold text-danger-500 text-sm tabular-nums">{{ fmtCur(selectedGoal.totalWithdrawn) }}</p>
          </div>
          <div class="bg-surface-50 dark:bg-surface-700/50 rounded-lg p-3">
            <p class="text-xs text-surface-400 mb-1">Auto-Contribute</p>
            <div class="flex items-center gap-2">
              <span class="w-2 h-2 rounded-full" :class="selectedGoal.autoContributeEnabled ? 'bg-green-500' : 'bg-surface-300'"></span>
              <p class="font-semibold text-surface-900 dark:text-white text-sm">{{ selectedGoal.autoContributeEnabled ? 'On (day ' + selectedGoal.autoContributeDayOfMonth + ')' : 'Off' }}</p>
            </div>
          </div>
        </div>

        <!-- Milestones -->
        <div>
          <h4 class="text-sm font-semibold text-surface-700 dark:text-surface-300 mb-3">Milestones</h4>
          <div class="grid grid-cols-4 gap-3">
            <div
              v-for="ms in selectedGoal.milestones"
              :key="ms.id"
              class="rounded-lg p-3 text-center transition-all duration-300"
              :class="ms.achieved ? '' : 'opacity-40'"
              :style="ms.achieved ? { backgroundColor: (selectedGoal.coverColor || categoryConfig[selectedGoal.category]?.color) + '15', border: '1px solid ' + (selectedGoal.coverColor || categoryConfig[selectedGoal.category]?.color) + '40' } : { border: '1px solid rgba(100,116,139,0.2)' }"
            >
              <div class="text-xl mb-1">{{ ms.achieved ? '✅' : '⬜' }}</div>
              <p class="text-xs font-bold text-surface-900 dark:text-white">{{ ms.percent }}%</p>
              <p class="text-[10px] text-surface-500 mt-0.5">{{ ms.label }}</p>
              <p v-if="ms.achievedDate" class="text-[10px] text-surface-400 mt-0.5">{{ formatDate(ms.achievedDate, 'short') }}</p>
            </div>
          </div>
        </div>

        <!-- Description -->
        <div v-if="selectedGoal.description">
          <h4 class="text-sm font-semibold text-surface-700 dark:text-surface-300 mb-1">Description</h4>
          <p class="text-sm text-surface-600 dark:text-surface-400">{{ selectedGoal.description }}</p>
        </div>

        <!-- Tags -->
        <div v-if="selectedGoal.tags && selectedGoal.tags.length > 0">
          <div class="flex flex-wrap gap-2">
            <span v-for="tag in selectedGoal.tags" :key="tag" class="text-sm px-2.5 py-1 rounded-lg bg-primary-50 dark:bg-primary-500/10 text-primary-600 dark:text-primary-400">{{ tag }}</span>
          </div>
        </div>

        <!-- Notes -->
        <div v-if="selectedGoal.notes">
          <h4 class="text-sm font-semibold text-surface-700 dark:text-surface-300 mb-1">Notes</h4>
          <p class="text-sm text-surface-600 dark:text-surface-400">{{ selectedGoal.notes }}</p>
        </div>

        <!-- Actions -->
        <div class="flex flex-wrap gap-3 pt-4 border-t border-surface-200 dark:border-surface-700">
          <button v-if="selectedGoal.status === 'active' && store.getRemainingAmount(selectedGoal) > 0" class="btn-primary" @click="openContributeModal(selectedGoal)">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/></svg>
            Contribute
          </button>
          <button v-if="selectedGoal.status === 'active' && store.getRemainingAmount(selectedGoal) > 0 && store.getRemainingAmount(selectedGoal) <= 50000" class="px-4 py-2 rounded-lg bg-accent-100 dark:bg-accent-500/30 text-accent-600 dark:text-accent-400 hover:bg-accent-200 dark:hover:bg-accent-500/40 transition-colors font-medium text-sm" @click="celebrate(selectedGoal)">
            🎉 Quick Complete
          </button>
          <button v-if="selectedGoal.status === 'active' && selectedGoal.currentAmount > 0" class="btn-secondary text-sm" @click="openWithdrawModal(selectedGoal)">
            Withdraw
          </button>
          <button class="btn-secondary text-sm" @click="openEditModal(selectedGoal)">
            <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"/></svg>
            Edit
          </button>
          <button v-if="selectedGoal.status === 'active'" class="btn-secondary text-sm" @click="handlePause(selectedGoal.id)">Pause</button>
          <button v-if="selectedGoal.status === 'paused'" class="btn-secondary text-sm" @click="handleResume(selectedGoal.id)">Resume</button>
          <button v-if="selectedGoal.status === 'active' || selectedGoal.status === 'paused'" class="text-sm px-4 py-2 rounded-lg bg-danger-50 dark:bg-danger-500/20 text-danger-600 dark:text-danger-400 hover:bg-danger-100 dark:hover:bg-danger-500/30 transition-colors font-medium" @click="handleAbandon(selectedGoal.id)">Abandon</button>
          <button class="text-sm px-4 py-2 rounded-lg bg-surface-100 dark:bg-surface-700 text-surface-500 dark:text-surface-400 hover:bg-surface-200 dark:hover:bg-surface-600 transition-colors font-medium" @click="showDeleteConfirm = true">Delete</button>
        </div>
      </div>
    </Modal>

    <!-- ==================== ADD/EDIT GOAL MODAL ==================== -->
    <Modal :is-open="showAddModal" :title="isEditMode ? 'Edit Goal' : 'Create New Savings Goal'" size="xl" @close="showAddModal = false">
      <form @submit.prevent="saveGoal" class="space-y-5">
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div class="md:col-span-2">
            <label class="field-label">Goal Name <span class="text-danger-500">*</span></label>
            <input v-model="form.name" type="text" class="input-field" placeholder="e.g., Emergency Fund, Hajj, New Laptop" />
          </div>
          <div>
            <label class="field-label">Category <span class="text-danger-500">*</span></label>
            <select v-model="form.category" class="input-field">
              <option v-for="(cfg, key) in categoryConfig" :key="key" :value="key">{{ cfg.icon }} {{ cfg.label }}</option>
            </select>
          </div>
          <div>
            <label class="field-label">Priority</label>
            <select v-model="form.priority" class="input-field">
              <option value="high">High</option>
              <option value="medium">Medium</option>
              <option value="low">Low</option>
            </select>
          </div>
        </div>
        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label class="field-label">Target Amount (BDT) <span class="text-danger-500">*</span></label>
            <input v-model.number="form.targetAmount" type="number" class="input-field" placeholder="0" min="0" />
          </div>
          <div v-if="isEditMode">
            <label class="field-label">Current Amount</label>
            <input v-model.number="form.currentAmount" type="number" class="input-field" placeholder="0" min="0" :max="form.targetAmount" />
          </div>
          <div>
            <label class="field-label">Monthly Contribution</label>
            <input v-model.number="form.monthlyContributionAmount" type="number" class="input-field" placeholder="0" min="0" />
          </div>
        </div>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label class="field-label">Start Date</label>
            <input v-model="form.startDate" type="date" class="input-field" />
          </div>
          <div>
            <label class="field-label">Target Date (optional)</label>
            <input v-model="form.targetDate" type="date" class="input-field" />
          </div>
        </div>
        <div>
          <h4 class="text-sm font-semibold text-surface-900 dark:text-white mb-3">Personalization</h4>
          <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div>
              <label class="field-label">Icon Emoji</label>
              <input v-model="form.coverIcon" type="text" class="input-field" placeholder="🎯" maxlength="4" />
            </div>
            <div>
              <label class="field-label">Accent Color</label>
              <div class="flex gap-2 flex-wrap">
                <button v-for="color in ['#10b981', '#3b82f6', '#6366f1', '#8b5cf6', '#ec4899', '#f59e0b', '#f97316', '#ef4444', '#06b6d4', '#14b8a6', '#64748b']" :key="color" type="button" @click="form.coverColor = color" class="w-7 h-7 rounded-full border-2 transition-transform hover:scale-110" :class="form.coverColor === color ? 'border-surface-900 dark:border-white scale-110' : 'border-transparent'" :style="{ backgroundColor: color }"></button>
              </div>
            </div>
            <div>
              <label class="field-label">Motivational Quote</label>
              <input v-model="form.motivationalQuote" type="text" class="input-field" placeholder="Your personal mantra..." />
            </div>
          </div>
        </div>
        <div>
          <h4 class="text-sm font-semibold text-surface-900 dark:text-white mb-3">Automation</h4>
          <div class="flex items-center gap-6">
            <div class="flex items-center gap-3">
              <label class="relative inline-flex items-center cursor-pointer">
                <input type="checkbox" v-model="form.autoContributeEnabled" class="sr-only peer">
                <div class="w-9 h-5 bg-surface-200 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-primary-600"></div>
              </label>
              <span class="text-sm text-surface-700 dark:text-surface-300">Auto-Contribute</span>
            </div>
            <div v-if="form.autoContributeEnabled">
              <label class="field-label">Day of Month</label>
              <input v-model.number="form.autoContributeDayOfMonth" type="number" class="input-field w-20" min="1" max="28" />
            </div>
          </div>
        </div>
        <div>
          <label class="field-label">Description</label>
          <textarea v-model="form.description" class="input-field" rows="2" placeholder="Why is this goal important to you?"></textarea>
        </div>
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label class="field-label">Tags (comma separated)</label>
            <input v-model="form.tags" type="text" class="input-field" placeholder="essential, long-term, priority" />
          </div>
          <div>
            <label class="field-label">Notes</label>
            <input v-model="form.notes" type="text" class="input-field" placeholder="Additional notes..." />
          </div>
        </div>
        <div class="flex justify-end gap-3 pt-4 border-t border-surface-200 dark:border-surface-700">
          <button type="button" class="btn-secondary" @click="showAddModal = false">Cancel</button>
          <button type="submit" class="btn-primary" :disabled="!form.name.trim() || form.targetAmount <= 0">
            {{ isEditMode ? 'Update Goal' : 'Create Goal' }}
          </button>
        </div>
      </form>
    </Modal>

    <!-- ==================== CONTRIBUTE MODAL ==================== -->
    <Modal :is-open="showContributeModal" title="Add Contribution" size="md" @close="showContributeModal = false">
      <form @submit.prevent="submitContribution" class="space-y-4">
        <div v-if="contributingGoalId" class="bg-surface-50 dark:bg-surface-700/50 rounded-lg p-4 text-center">
          <p class="text-sm text-surface-500">Adding to</p>
          <p class="font-bold text-surface-900 dark:text-white">{{ store.getGoalById(contributingGoalId)?.name }}</p>
          <p class="text-xs text-surface-400 mt-1">
            Current: {{ fmtCur(store.getGoalById(contributingGoalId)?.currentAmount || 0) }}
            &middot; Target: {{ fmtCur(store.getGoalById(contributingGoalId)?.targetAmount || 0) }}
            &middot; Need: {{ fmtCur(store.getRemainingAmount(store.getGoalById(contributingGoalId)!) || 0) }}
          </p>
        </div>
        <div>
          <label class="field-label">Amount (BDT) <span class="text-danger-500">*</span></label>
          <input v-model.number="contributeForm.amount" type="number" class="input-field" placeholder="0" min="1" />
        </div>
        <div>
          <label class="field-label">From Account</label>
          <select v-model="contributeForm.bankAccountId" class="input-field">
            <option value="">Select Account</option>
            <option v-for="acc in bankStore.bankAccounts" :key="acc.id" :value="acc.id">{{ acc.bankName }} - {{ acc.accountNumber }}</option>
          </select>
        </div>
        <div>
          <label class="field-label">Note (optional)</label>
          <input v-model="contributeForm.note" type="text" class="input-field" placeholder="What motivated this contribution?" />
        </div>
        <div class="flex justify-end gap-3 pt-4 border-t border-surface-200 dark:border-surface-700">
          <button type="button" class="btn-secondary" @click="showContributeModal = false">Cancel</button>
          <button type="submit" class="btn-primary" :disabled="!contributeForm.amount || contributeForm.amount <= 0">Add Money</button>
        </div>
      </form>
    </Modal>

    <!-- ==================== WITHDRAW MODAL ==================== -->
    <Modal :is-open="showWithdrawModal" title="Withdraw from Goal" size="sm" @close="showWithdrawModal = false">
      <form @submit.prevent="submitWithdrawal" class="space-y-4">
        <div v-if="withdrawingGoalId" class="bg-warning-50 dark:bg-warning-500/10 rounded-lg p-4 text-center">
          <p class="text-sm text-warning-600 dark:text-warning-400">Warning: Withdrawing may reset milestones</p>
          <p class="font-bold text-surface-900 dark:text-white mt-1">{{ store.getGoalById(withdrawingGoalId)?.name }}</p>
          <p class="text-xs text-surface-400 mt-1">Available: {{ fmtCur(store.getGoalById(withdrawingGoalId)?.currentAmount || 0) }}</p>
        </div>
        <div>
          <label class="field-label">Amount (BDT) <span class="text-danger-500">*</span></label>
          <input v-model.number="withdrawForm.amount" type="number" class="input-field" placeholder="0" min="1" :max="withdrawingGoalId ? store.getGoalById(withdrawingGoalId)?.currentAmount || 0 : undefined" />
        </div>
        <div>
          <label class="field-label">Reason (optional)</label>
          <input v-model="withdrawForm.note" type="text" class="input-field" placeholder="Reason for withdrawal" />
        </div>
        <div class="flex justify-end gap-3 pt-4 border-t border-surface-200 dark:border-surface-700">
          <button type="button" class="btn-secondary" @click="showWithdrawModal = false">Cancel</button>
          <button type="submit" class="px-4 py-2 rounded-lg bg-warning-500 hover:bg-warning-600 text-white font-medium text-sm transition-colors" :disabled="!withdrawForm.amount || withdrawForm.amount <= 0">Withdraw</button>
        </div>
      </form>
    </Modal>

    <!-- ==================== DELETE CONFIRM ==================== -->
    <Modal :is-open="showDeleteConfirm" title="Delete Goal" size="sm" @close="showDeleteConfirm = false">
      <div class="space-y-4">
        <p class="text-sm text-surface-600 dark:text-surface-400">Are you sure you want to delete this goal? This action cannot be undone and all contribution history will be lost.</p>
        <div class="flex justify-end gap-3">
          <button class="btn-secondary text-sm" @click="showDeleteConfirm = false">Cancel</button>
          <button class="px-4 py-2 rounded-lg bg-danger-500 hover:bg-danger-600 text-white font-medium text-sm transition-colors" @click="confirmDelete">Delete</button>
        </div>
      </div>
    </Modal>
  </div>
</template>
