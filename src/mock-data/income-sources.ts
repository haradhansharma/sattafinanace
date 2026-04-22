import type { IncomeSource } from '../types';

export const mockIncomeSources: IncomeSource[] = [
  {
    id: 'incs_001',
    name: 'ABC Corporation',
    type: 'salary',
    isActive: true,
    monthlyAmount: 80000,
    createdAt: '2025-04-01T10:00:00.000Z',
    updatedAt: '2025-04-01T10:00:00.000Z',
  },
  {
    id: 'incs_002',
    name: 'Freelance Web Dev',
    type: 'freelance',
    isActive: true,
    createdAt: '2025-04-01T10:00:00.000Z',
    updatedAt: '2025-04-01T10:00:00.000Z',
  },
  {
    id: 'incs_003',
    name: 'Stock Dividends',
    type: 'investment',
    isActive: true,
    createdAt: '2025-06-15T10:00:00.000Z',
    updatedAt: '2025-06-15T10:00:00.000Z',
  },
  {
    id: 'incs_004',
    name: 'Rental Property',
    type: 'rental',
    isActive: true,
    monthlyAmount: 15000,
    createdAt: '2025-04-01T10:00:00.000Z',
    updatedAt: '2025-04-01T10:00:00.000Z',
  },
];
