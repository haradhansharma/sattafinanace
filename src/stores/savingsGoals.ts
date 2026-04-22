import '../lib/pinia-init';
import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import type { SavingsGoal, SavingsGoalCategory, SavingsGoalStatus, SavingsGoalContribution, SavingsGoalMilestone } from '../types';
import { mockSavingsGoals } from '../mock-data';
import { generateId } from '../utils/formatters';

export const useSavingsGoalStore = defineStore('savingsGoal', () => {
  const goals = ref<SavingsGoal[]>(mockSavingsGoals.map(g => ({
    ...g,
    tags: g.tags || [],
    contributions: g.contributions || [],
    milestones: g.milestones || [],
  })));

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

  // Goals by category
  const goalsByCategory = computed(() => {
    const map: Record<string, SavingsGoal[]> = {};
    goals.value.forEach(g => {
      if (!map[g.category]) map[g.category] = [];
      map[g.category].push(g);
    });
    return map;
  });

  // Total contributed this month
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

  // Goals closest to completion
  const almostThereGoals = computed(() =>
    activeGoals.value
      .filter(g => {
        const pct = (g.currentAmount / g.targetAmount) * 100;
        return pct >= 70 && pct < 100;
      })
      .sort((a, b) => (b.currentAmount / b.targetAmount) - (a.currentAmount / a.targetAmount))
  );

  // ==================== Motivational Helpers ====================

  function getMotivationalMessage(progress: number): { message: string; emoji: string } {
    if (progress >= 100) return { message: 'Congratulations! You did it!', emoji: '🎉' };
    if (progress >= 75) return { message: "You're almost there! Keep pushing!", emoji: '🔥' };
    if (progress >= 50) return { message: "Halfway there! You're doing amazing!", emoji: '💪' };
    if (progress >= 25) return { message: "Great start! Keep the momentum going!", emoji: '🚀' };
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
    const monthsRemaining = Math.max(0, (target.getFullYear() - now.getFullYear()) * 12 + (target.getMonth() - now.getMonth()));
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
    return goals.value.filter(g =>
      g.name.toLowerCase().includes(q) ||
      g.description?.toLowerCase().includes(q) ||
      g.tags?.some(t => t.toLowerCase().includes(q)) ||
      g.notes?.toLowerCase().includes(q)
    );
  }

  function getGoalById(id: string): SavingsGoal | undefined {
    return goals.value.find(g => g.id === id);
  }

  // ==================== Milestone Helpers ====================

  function checkAndUpdateMilestones(goal: SavingsGoal): SavingsGoalMilestone[] {
    const progress = getGoalProgress(goal);
    return goal.milestones.map(m => {
      if (!m.achieved && progress >= m.percent) {
        return { ...m, achieved: true, achievedDate: new Date().toISOString() };
      }
      return m;
    });
  }

  function getLatestMilestone(goal: SavingsGoal): SavingsGoalMilestone | null {
    const achieved = goal.milestones.filter(m => m.achieved);
    if (achieved.length === 0) return null;
    return achieved.reduce((latest, m) => m.percent > latest.percent ? m : latest);
  }

  // ==================== CRUD ====================

  function addGoal(data: Omit<SavingsGoal, 'id' | 'createdAt' | 'updatedAt'>): SavingsGoal {
    const now = new Date().toISOString();
    const goal: SavingsGoal = {
      ...data,
      tags: data.tags || [],
      contributions: data.contributions || [],
      milestones: data.milestones || [
        { id: 'ms_25', percent: 25, label: 'Getting Started!', achieved: false },
        { id: 'ms_50', percent: 50, label: 'Halfway There!', achieved: false },
        { id: 'ms_75', percent: 75, label: 'Almost There!', achieved: false },
        { id: 'ms_100', percent: 100, label: 'Goal Complete!', achieved: false },
      ],
      totalContributed: data.totalContributed || data.currentAmount,
      totalWithdrawn: data.totalWithdrawn || 0,
      contributionCount: data.contributionCount || 0,
      currentStreak: data.currentStreak || 0,
      longestStreak: data.longestStreak || 0,
      id: generateId('sg'),
      createdAt: now,
      updatedAt: now,
    };
    goals.value.push(goal);
    return goal;
  }

  function updateGoal(id: string, data: Partial<SavingsGoal>): SavingsGoal | null {
    const index = goals.value.findIndex(g => g.id === id);
    if (index === -1) return null;
    goals.value[index] = {
      ...goals.value[index],
      ...data,
      id: goals.value[index].id,
      createdAt: goals.value[index].createdAt,
      tags: data.tags ?? goals.value[index].tags,
      contributions: data.contributions ?? goals.value[index].contributions,
      milestones: data.milestones ?? goals.value[index].milestones,
      updatedAt: new Date().toISOString(),
    };
    return goals.value[index];
  }

  function deleteGoal(id: string) {
    const index = goals.value.findIndex(g => g.id === id);
    if (index !== -1) goals.value.splice(index, 1);
  }

  // ==================== Contribution Actions ====================

  function addContribution(goalId: string, amount: number, note?: string, bankAccountId?: string) {
    const goal = goals.value.find(g => g.id === goalId);
    if (!goal || amount <= 0) return;

    const contribution: SavingsGoalContribution = {
      id: generateId('sgc'),
      amount,
      date: new Date().toISOString(),
      note,
      bankAccountId,
    };

    goal.contributions.push(contribution);
    goal.totalContributed += amount;
    goal.contributionCount += 1;
    goal.currentAmount += amount;
    goal.updatedAt = new Date().toISOString();

    // Update streak
    const lastMonth = new Date();
    lastMonth.setMonth(lastMonth.getMonth() - 1);
    const hasLastMonth = goal.contributions.some(c => {
      const d = new Date(c.date);
      return d.getFullYear() === lastMonth.getFullYear() && d.getMonth() === lastMonth.getMonth();
    });
    goal.currentStreak = hasLastMonth ? goal.currentStreak + 1 : 1;
    goal.longestStreak = Math.max(goal.longestStreak, goal.currentStreak);

    // Check milestones
    goal.milestones = checkAndUpdateMilestones(goal);

    // Auto-complete if target reached
    if (goal.currentAmount >= goal.targetAmount) {
      goal.currentAmount = goal.targetAmount;
      goal.status = 'completed';
      goal.completedDate = new Date().toISOString();
    }
  }

  function withdrawFromGoal(goalId: string, amount: number, note?: string) {
    const goal = goals.value.find(g => g.id === goalId);
    if (!goal || amount <= 0 || amount > goal.currentAmount) return;

    goal.currentAmount -= amount;
    goal.totalWithdrawn += amount;
    goal.updatedAt = new Date().toISOString();

    // Reset milestones if went below threshold
    goal.milestones = checkAndUpdateMilestones(goal);

    // If was completed, go back to active
    if (goal.status === 'completed') {
      goal.status = 'active';
      goal.completedDate = undefined;
    }
  }

  function pauseGoal(id: string) {
    const goal = goals.value.find(g => g.id === id);
    if (!goal) return;
    goal.status = 'paused';
    goal.autoContributeEnabled = false;
    goal.updatedAt = new Date().toISOString();
  }

  function resumeGoal(id: string) {
    const goal = goals.value.find(g => g.id === id);
    if (!goal) return;
    goal.status = 'active';
    goal.updatedAt = new Date().toISOString();
  }

  function abandonGoal(id: string) {
    const goal = goals.value.find(g => g.id === id);
    if (!goal) return;
    goal.status = 'abandoned';
    goal.autoContributeEnabled = false;
    goal.updatedAt = new Date().toISOString();
  }

  function toggleAutoContribute(id: string) {
    const goal = goals.value.find(g => g.id === id);
    if (!goal) return;
    goal.autoContributeEnabled = !goal.autoContributeEnabled;
    goal.updatedAt = new Date().toISOString();
  }

  return {
    goals,
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
    getMotivationalMessage,
    getGoalProgress,
    getRemainingAmount,
    getProjectedCompletionDate,
    isOnTrack,
    getTrackStatus,
    getDaysRemaining,
    getGoalsByCategory,
    searchGoals,
    getGoalById,
    getLatestMilestone,
    addGoal,
    updateGoal,
    deleteGoal,
    addContribution,
    withdrawFromGoal,
    pauseGoal,
    resumeGoal,
    abandonGoal,
    toggleAutoContribute,
  };
});
