import type { DashboardStats } from '../types';

export const dashboardService = {
  /**
   * Compute dashboard stats from data already loaded by stores.
   * Call this AFTER the relevant stores have fetched their data.
   */
  async getStats(): Promise<DashboardStats> {
    // Dynamic imports to avoid circular deps and ensure stores are initialized
    const { useBankStore } = await import('../stores/bank');
    const { useIncomeStore } = await import('../stores/income');
    const { useExpenseStore } = await import('../stores/expense');
    const { useLoanStore } = await import('../stores/loan');
    const { useInvestmentStore } = await import('../stores/investment');

    const bankStore = useBankStore();
    const incomeStore = useIncomeStore();
    const expenseStore = useExpenseStore();
    const loanStore = useLoanStore();
    const investmentStore = useInvestmentStore();

    const totalBalance = bankStore.totalBalance;
    const totalIncome = incomeStore.totalMonthlyIncome;
    const totalExpense = expenseStore.totalMonthlyExpense;
    const totalSavings = totalIncome - totalExpense;
    const totalDebt = loanStore.totalDebt;
    const netWorth = totalBalance + investmentStore.totalCurrentValue - totalDebt;

    return {
      totalBalance,
      totalIncome,
      totalExpense,
      totalSavings,
      incomeChangePercent: 0,
      expenseChangePercent: 0,
      savingsChangePercent: 0,
      totalDebt,
      netWorth,
    };
  },

  /**
   * Get monthly income/expense trend from current month and previous months.
   * Uses store data filtered by month.
   */
  async getMonthlyTrend(months: number = 6) {
    const { useIncomeStore } = await import('../stores/income');
    const { useExpenseStore } = await import('../stores/expense');

    const incomeStore = useIncomeStore();
    const expenseStore = useExpenseStore();

    const now = new Date();
    const monthsData = [];

    for (let i = months - 1; i >= 0; i--) {
      const date = new Date(now.getFullYear(), now.getMonth() - i, 1);
      const monthStr = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`;
      const label = date.toLocaleDateString('en-US', { month: 'short', year: '2-digit' });

      // Filter incomes and expenses for this month
      const monthIncomes = incomeStore.incomes.filter(inc => {
        const incMonth = inc.date?.slice(0, 7);
        return incMonth === monthStr;
      });
      const monthExpenses = expenseStore.expenses.filter(exp => {
        const expMonth = exp.date?.slice(0, 7);
        return expMonth === monthStr;
      });

      monthsData.push({
        month: monthStr,
        label,
        income: monthIncomes.reduce((sum, inc) => sum + inc.amount, 0),
        expense: monthExpenses.reduce((sum, exp) => sum + exp.amount, 0),
      });
    }

    return monthsData;
  },

  /**
   * Get expense category breakdown using store data.
   */
  async getCategoryBreakdown() {
    const { useExpenseStore } = await import('../stores/expense');
    const expenseStore = useExpenseStore();

    // Use the category breakdown from the store if available, otherwise compute locally
    if (expenseStore.categoryBreakdown && expenseStore.categoryBreakdown.length > 0) {
      return expenseStore.categoryBreakdown;
    }

    // Fallback: compute from local data
    const categories = expenseStore.categories;
    const expenses = expenseStore.expenses;

    return categories.map(cat => {
      const total = expenses
        .filter(e => e.categoryId === cat.id)
        .reduce((sum, e) => sum + e.amount, 0);
      return { ...cat, total };
    }).filter(c => c.total > 0).sort((a, b) => b.total - a.total);
  },
};
