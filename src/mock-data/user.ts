import type { User } from '../types';

export const mockUser: User = {
  id: 'usr_001',
  name: 'Rahim Uddin',
  email: 'rahim@example.com',
  avatar: '',
  currency: 'BDT',
  dateFormat: 'dd/MM/yyyy',
  darkMode: false,
  notifications: {
    email: true,
    push: true,
    budgetAlert: true,
    lowBalance: true,
    loanReminder: true,
  },
};
