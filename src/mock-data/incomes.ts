import type { Income } from '../types';

export const mockIncomes: Income[] = [
  // Monthly Salary - January 2026
  {
    id: 'inc_001',
    sourceId: 'incs_001',
    amount: 80000,
    date: '2026-01-01T09:00:00.000Z',
    bankAccountId: 'ba_003',
    categoryId: 'inc_cat_001',       // Salary
    description: 'Monthly Salary - ABC Corporation',
    isRecurring: true,
    recurringCycle: 'monthly',
    currency: 'BDT',
    createdAt: '2026-01-01T09:00:00.000Z',
    updatedAt: '2026-01-01T09:00:00.000Z',
  },
  // Monthly Salary - February 2026
  {
    id: 'inc_002',
    sourceId: 'incs_001',
    amount: 80000,
    date: '2026-02-01T09:00:00.000Z',
    bankAccountId: 'ba_003',
    categoryId: 'inc_cat_001',       // Salary
    description: 'Monthly Salary - ABC Corporation',
    isRecurring: true,
    recurringCycle: 'monthly',
    currency: 'BDT',
    createdAt: '2026-02-01T09:00:00.000Z',
    updatedAt: '2026-02-01T09:00:00.000Z',
  },
  // Monthly Salary - March 2026
  {
    id: 'inc_003',
    sourceId: 'incs_001',
    amount: 80000,
    date: '2026-03-01T09:00:00.000Z',
    bankAccountId: 'ba_003',
    categoryId: 'inc_cat_001',       // Salary
    description: 'Monthly Salary - ABC Corporation',
    isRecurring: true,
    recurringCycle: 'monthly',
    currency: 'BDT',
    createdAt: '2026-03-01T09:00:00.000Z',
    updatedAt: '2026-03-01T09:00:00.000Z',
  },
  // Monthly Salary - April 2026
  {
    id: 'inc_004',
    sourceId: 'incs_001',
    amount: 80000,
    date: '2026-04-01T09:00:00.000Z',
    bankAccountId: 'ba_003',
    categoryId: 'inc_cat_001',       // Salary
    transactionId: 'txn_001',        // Links to bank transaction
    description: 'Monthly Salary - ABC Corporation',
    isRecurring: true,
    recurringCycle: 'monthly',
    currency: 'BDT',
    createdAt: '2026-04-01T09:00:00.000Z',
    updatedAt: '2026-04-01T09:00:00.000Z',
  },
  // Freelance - E-commerce Website (January 2026)
  {
    id: 'inc_005',
    sourceId: 'incs_002',
    amount: 35000,
    date: '2026-01-15T14:30:00.000Z',
    bankAccountId: 'ba_002',
    categoryId: 'inc_cat_002',       // Freelance
    description: 'Freelance Payment - E-commerce Website Project',
    isRecurring: false,
    currency: 'USD',
    createdAt: '2026-01-15T14:30:00.000Z',
    updatedAt: '2026-01-15T14:30:00.000Z',
  },
  // Freelance - Mobile App UI Design (March 2026)
  {
    id: 'inc_006',
    sourceId: 'incs_002',
    amount: 45000,
    date: '2026-03-20T16:00:00.000Z',
    bankAccountId: 'ba_002',
    categoryId: 'inc_cat_002',       // Freelance
    description: 'Freelance Payment - Mobile App UI Design',
    isRecurring: false,
    currency: 'BDT',
    createdAt: '2026-03-20T16:00:00.000Z',
    updatedAt: '2026-03-20T16:00:00.000Z',
  },
  // Freelance - WordPress Plugin (April 2026)
  {
    id: 'inc_007',
    sourceId: 'incs_002',
    amount: 28000,
    date: '2026-04-10T12:00:00.000Z',
    bankAccountId: 'ba_002',
    categoryId: 'inc_cat_002',       // Freelance
    transactionId: 'txn_002',        // Links to bank transaction
    description: 'Freelance Payment - WordPress Plugin Development',
    isRecurring: false,
    currency: 'USD',
    createdAt: '2026-04-10T12:00:00.000Z',
    updatedAt: '2026-04-10T12:00:00.000Z',
  },
  // Stock Dividend - Grameenphone (February 2026)
  {
    id: 'inc_008',
    sourceId: 'incs_003',
    amount: 5500,
    date: '2026-02-10T11:00:00.000Z',
    bankAccountId: 'ba_001',
    categoryId: 'inc_cat_004',       // Investment Returns
    description: 'Stock Dividend - Grameenphone',
    isRecurring: false,
    currency: 'BDT',
    createdAt: '2026-02-10T11:00:00.000Z',
    updatedAt: '2026-02-10T11:00:00.000Z',
  },
  // Stock Dividend - Robi Axiata (April 2026)
  {
    id: 'inc_009',
    sourceId: 'incs_003',
    amount: 3200,
    date: '2026-04-12T11:00:00.000Z',
    bankAccountId: 'ba_001',
    categoryId: 'inc_cat_004',       // Investment Returns
    transactionId: 'txn_003',        // Links to bank transaction
    description: 'Stock Dividend - Robi Axiata',
    isRecurring: false,
    currency: 'BDT',
    createdAt: '2026-04-12T11:00:00.000Z',
    updatedAt: '2026-04-12T11:00:00.000Z',
  },
  // Rental Income - February 2026
  {
    id: 'inc_010',
    sourceId: 'incs_004',
    amount: 15000,
    date: '2026-02-05T10:00:00.000Z',
    bankAccountId: 'ba_001',
    categoryId: 'inc_cat_005',       // Rental Income
    description: 'Rental Income - Mirpur Apartment',
    isRecurring: true,
    recurringCycle: 'monthly',
    currency: 'BDT',
    createdAt: '2026-02-05T10:00:00.000Z',
    updatedAt: '2026-02-05T10:00:00.000Z',
  },
  // Rental Income - March 2026
  {
    id: 'inc_011',
    sourceId: 'incs_004',
    amount: 15000,
    date: '2026-03-05T10:00:00.000Z',
    bankAccountId: 'ba_001',
    categoryId: 'inc_cat_005',       // Rental Income
    description: 'Rental Income - Mirpur Apartment',
    isRecurring: true,
    recurringCycle: 'monthly',
    currency: 'BDT',
    createdAt: '2026-03-05T10:00:00.000Z',
    updatedAt: '2026-03-05T10:00:00.000Z',
  },
  // Rental Income - April 2026
  {
    id: 'inc_012',
    sourceId: 'incs_004',
    amount: 15000,
    date: '2026-04-05T10:00:00.000Z',
    bankAccountId: 'ba_001',
    categoryId: 'inc_cat_005',       // Rental Income
    transactionId: 'txn_004',        // Links to bank transaction
    description: 'Rental Income - Mirpur Apartment',
    isRecurring: true,
    recurringCycle: 'monthly',
    currency: 'BDT',
    createdAt: '2026-04-05T10:00:00.000Z',
    updatedAt: '2026-04-05T10:00:00.000Z',
  },
];
