/**
 * FinLife Services barrel export
 * =============================
 * Re-exports all service singletons for convenient importing.
 * Note: Domain-specific services (bank, income, expense, card, loan, budget)
 * are legacy mock-based wrappers. Stores now call api-bridge directly.
 * They are kept here only for backward compatibility — do NOT use them
 * for new code.
 */

export { api, ApiError, fetchAllPages } from './api-bridge';
export type { PaginatedResponse } from './api-bridge';
export { dataService } from './data-service';
export { invoiceService } from './invoice-service';
export { bankService } from './bank-service';
export { incomeService } from './income-service';
export { expenseService } from './expense-service';
export { cardService } from './card-service';
export { loanService } from './loan-service';
export { budgetService } from './budget-service';
export { dashboardService } from './dashboard-service';
