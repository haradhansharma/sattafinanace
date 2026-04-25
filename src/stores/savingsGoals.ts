import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import type { SavingsGoal, SavingsGoalCategory, SavingsGoalStatus, SavingsGoalContribution, SavingsGoalMilestone } from '../types';
import { api, fetchAllPages, ApiError } from '../services/api-bridge';

export const useSavingsGoalStore = defineStore('savingsGoal', () => {
  // ==================== State ====================
  const goals = ref<SavingsGoal[]>([]);
  const loading = ref(false);
  const error = ref<string | null>(null);

  // ==================== Computed ====================

  const totalGoals = computed(() => goals.value.length);

  const activeGoals = computed(() =>
    goals.value.filter(g => g.status === 'active')
  );

  const completedGoals = computed(() =>
    goals.value.filter(g => g.status === 'completed')
  );

  const pausedGoals = computed(() =>
    goals.value.filter(g => g.status === 'paused')
  );

  const totalSaved = computed(() =>
    goals.value
      .filter(g => g.status !== 'abandoned')
      .reduce((sum, g) => sum + g.currentAmount, 0)
  );

  const totalTarget = computed(() =>
    goals.value
      .filter(g => g.status !== 'abandoned')
      .reduce((sum, g) => sum + g.targetAmount, 0)
  );

  const overallProgress = computed(() => {
    if (totalTarget.value === 0) return 0;
    return Math.round((totalSaved.value / totalTarget.value) * 100);
  });

  const totalMonthlyContributions = computed(() =>
    activeGoals.value.reduce((sum, g) => sum + g.monthlyContributionAmount, 0)
  );

  const completedCount = computed(() => completedGoals.value.length);

  const goalsByCategory = computed(() => {
    const map: Record<string, SavingsGoal[]> = {};
    goals.value.forEach(g => {
      if (!map[g.category]) map[g.category] = [];
      map[g.category].push(g);
    });
    return map;
  });

  const contributedThisMonth = computed(() => {
    const now = new Date();
    const year = now.getFullYear();
    const month = now.getMonth();
    return goals.value
      .flatMap(g => g.contributions)
      .filter(c => {
        const d = new Date(c.date);
        return d.getFullYear() === year && d.getMonth() === month;
      })
      .reduce((sum, c) => sum + c.amount, 0);
  });

  const almostThereGoals = computed(() =>
    activeGoals.value
      .filter(g => {
        const pct = (g.currentAmount / g.targetAmount) * 100;
        return pct >= 70 && pct < 100;
      })
      .sort((a, b) => (b.currentAmount / b.targetAmount) - (a.currentAmount / a.targetAmount))
  );

  // ==================== Fetch Methods ====================

  async function fetchGoals(params?: { category?: SavingsGoalCategory; status?: SavingsGoalStatus }): Promise<void> {
    loading.value = true;
    error.value = null;
    try {
      const query: Record<string, string | undefined> = {};
      if (params?.category) query.category = params.category;
      if (params?.status) query.status = params.status;
      goals.value = await fetchAllPages<SavingsGoal>('/savings-goal/', { params: query });
    } catch (err) {
      error.value = err instanceof ApiError ? err.message : 'Failed to fetch savings goals';
      throw err;
    } finally {
      loading.value = false;
    }
  }

  async function fetchGoalById(id: string): Promise<SavingsGoal> {
    loading.value = true;
    error.value = null;
    try {
      const goal = await api.get<SavingsGoal>(`/savings-goal/${id}/`);
      const idx = goals.value.findIndex(g => g.id === goal.id);
      if (idx !== -1) {
        goals.value[idx] = goal;
      } else {
        goals.value.push(goal);
      }
      return goal;
    } catch (err) {
      error.value = err instanceof ApiError ? err.message : 'Failed to fetch savings goal';
      throw err;
    } finally {
      loading.value = false;
    }
  }

  // ==================== Helper Functions ====================

  function getMotivationalMessage(progress: number): { message: string; emoji: string } {
    if (progress >= 100) return { message: 'Congratulations! You did it!', emoji: '🎉' };
    if (progress >= 75) return { message: "You're almost there! Keep pushing!", emoji: '🔥' };
    if (progress >= 50) return { message: "Halfway there! You're doing amazing!", emoji: '💪' };
    if (progress >= 25) return { message: 'Great start! Keep the momentum going!', emoji: '🚀' };
    if (progress >= 10) return { message: "You've started! Every taka counts!", emoji: '✨' };
    return { message: 'The journey of a thousand miles begins with a single step!', emoji: '🌟' };
  }

  function getGoalProgress(goal: SavingsGoal): number {
    if (goal.targetAmount === 0) return 0;
    return Math.round((goal.currentAmount / goal.targetAmount) * 100);
  }

  function getRemainingAmount(goal: SavingsGoal): number {
    return Math.max(0, goal.targetAmount - goal.currentAmount);
  }

  function getProjectedCompletionDate(goal: SavingsGoal): string | null {
    if (goal.status !== 'active' || goal.monthlyContributionAmount <= 0) return null;
    const remaining = goal.targetAmount - goal.currentAmount;
    if (remaining <= 0) return 'Goal reached!';
    const monthsNeeded = Math.ceil(remaining / goal.monthlyContributionAmount);
    const projected = new Date();
    projected.setMonth(projected.getMonth() + monthsNeeded);
    return projected.toLocaleDateString('en-US', { month: 'long', year: 'numeric' });
  }

  function isOnTrack(goal: SavingsGoal): boolean {
    if (!goal.targetDate || goal.monthlyContributionAmount <= 0) return true;
    const now = new Date();
    const target = new Date(goal.targetDate);
    const monthsRemaining = Math.max(
      0,
      (target.getFullYear() - now.getFullYear()) * 12 + (target.getMonth() - now.getMonth()),
    );
    if (monthsRemaining === 0) return goal.currentAmount >= goal.targetAmount;
    const remaining = goal.targetAmount - goal.currentAmount;
    const requiredMonthly = remaining / monthsRemaining;
    return goal.monthlyContributionAmount >= requiredMonthly;
  }

  function getTrackStatus(goal: SavingsGoal): { label: string; css: string } {
    const progress = getGoalProgress(goal);
    if (progress >= 100) return { label: 'Completed', css: 'text-accent-600 dark:text-accent-400' };
    if (isOnTrack(goal)) return { label: 'On Track', css: 'text-green-500' };
    return { label: 'Behind Schedule', css: 'text-warning-500' };
  }

  function getDaysRemaining(goal: SavingsGoal): number | null {
    if (!goal.targetDate) return null;
    const now = new Date();
    now.setHours(0, 0, 0, 0);
    const target = new Date(goal.targetDate);
    target.setHours(0, 0, 0, 0);
    return Math.max(0, Math.ceil((target.getTime() - now.getTime()) / (1000 * 60 * 60 * 24)));
  }

  // ==================== Query Methods ====================

  function getGoalsByCategory(category: SavingsGoalCategory): SavingsGoal[] {
    return goals.value.filter(g => g.category === category);
  }

  function searchGoals(query: string): SavingsGoal[] {
    const q = query.toLowerCase().trim();
    if (!q) return goals.value;
    return goals.value.filter(
      g =>
        g.name.toLowerCase().includes(q) ||
        g.description?.toLowerCase().includes(q) ||
        g.tags?.some(t => t.toLowerCase().includes(q)) ||
        g.notes?.toLowerCase().includes(q),
    );
  }

  function getGoalById(id: string): SavingsGoal | undefined {
    return goals.value.find(g => g.id === id);
  }

  // ==================== Milestone Helpers ====================

  function getLatestMilestone(goal: SavingsGoal): SavingsGoalMilestone | null {
    const achieved = goal.milestones.filter(m => m.achieved);
    if (achieved.length === 0) return null;
    return achieved.reduce((latest, m) => (m.percent > latest.percent ? m : latest));
  }

  // ==================== CRUD ====================

  async function addGoal(data: any): Promise<SavingsGoal> {
    error.value = null;
    try {
      const goal = await api.post<SavingsGoal>('/savings-goal/', data);
      goals.value.push(goal);
      return goal;
    } catch (err) {
      error.value = err instanceof ApiError ? err.message : 'Failed to create savings goal';
      throw err;
    }
  }

  async function updateGoal(id: string, data: Partial<SavingsGoal>): Promise<SavingsGoal | null> {
    error.value = null;
    try {
      const updated = await api.put<SavingsGoal>(`/savings-goal/${id}/`, data);
      const index = goals.value.findIndex(g => g.id === id);
      if (index !== -1) {
        goals.value[index] = updated;
      }
      return updated;
    } catch (err) {
      error.value = err instanceof ApiError ? err.message : 'Failed to update savings goal';
      throw err;
    }
  }

  async function deleteGoal(id: string): Promise<void> {
    error.value = null;
    try {
      await api.delete(`/savings-goal/${id}/`);
      const index = goals.value.findIndex(g => g.id === id);
      if (index !== -1) {
        goals.value.splice(index, 1);
      }
    } catch (err) {
      error.value = err instanceof ApiError ? err.message : 'Failed to delete savings goal';
      throw err;
    }
  }

  // ==================== Contribution Actions ====================

  async function addContribution(
    goalId: string,
    data: { amount: number; note?: string; bankAccountId?: string },
  ): Promise<SavingsGoalContribution> {
    error.value = null;
    try {
      const contribution = await api.post<SavingsGoalContribution>(
        `/savings-goal/${goalId}/contributions/`,
        data,
      );
      // Re-fetch goal so computed fields (totals, milestones, streak) are in sync
      await fetchGoalById(goalId);
      return contribution;
    } catch (err) {
      error.value = err instanceof ApiError ? err.message : 'Failed to add contribution';
      throw err;
    }
  }

  async function fetchContributions(goalId: string): Promise<SavingsGoalContribution[]> {
    loading.value = true;
    error.value = null;
    try {
      return await fetchAllPages<SavingsGoalContribution>(
        `/savings-goal/${goalId}/contributions/`,
      );
    } catch (err) {
      error.value = err instanceof ApiError ? err.message : 'Failed to fetch contributions';
      throw err;
    } finally {
      loading.value = false;
    }
  }

  // ==================== Status Helpers (delegate to updateGoal) ====================

  async function pauseGoal(id: string): Promise<SavingsGoal | null> {
    return updateGoal(id, { status: 'paused', autoContributeEnabled: false });
  }

  async function resumeGoal(id: string): Promise<SavingsGoal | null> {
    return updateGoal(id, { status: 'active' });
  }

  async function abandonGoal(id: string): Promise<SavingsGoal | null> {
    return updateGoal(id, { status: 'abandoned', autoContributeEnabled: false });
  }

  async function toggleAutoContribute(id: string): Promise<SavingsGoal | null> {
    const goal = goals.value.find(g => g.id === id);
    if (!goal) return null;
    return updateGoal(id, { autoContributeEnabled: !goal.autoContributeEnabled });
  }

  return {
    // State
    goals,
    loading,
    error,
    // Computed
    totalGoals,
    activeGoals,
    completedGoals,
    pausedGoals,
    totalSaved,
    totalTarget,
    overallProgress,
    totalMonthlyContributions,
    completedCount,
    goalsByCategory,
    contributedThisMonth,
    almostThereGoals,
    // Fetch
    fetchGoals,
    fetchGoalById,
    // Helpers
    getMotivationalMessage,
    getGoalProgress,
    getRemainingAmount,
    getProjectedCompletionDate,
    isOnTrack,
    getTrackStatus,
    getDaysRemaining,
    // Query
    getGoalsByCategory,
    searchGoals,
    getGoalById,
    getLatestMilestone,
    // CRUD
    addGoal,
    updateGoal,
    deleteGoal,
    // Contributions
    addContribution,
    fetchContributions,
    // Status
    pauseGoal,
    resumeGoal,
    abandonGoal,
    toggleAutoContribute,
  };
});
