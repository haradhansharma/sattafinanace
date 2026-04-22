import type { Currency } from '../types';

export interface ExchangeRate {
  currency: Currency;
  rate: number; // how many BDT per 1 unit of this currency
  symbol: string;
  name: string;
  flag: string;
}

export const mockExchangeRates: Record<Currency, ExchangeRate> = {
  BDT: { currency: 'BDT', rate: 1, symbol: '৳', name: 'Bangladeshi Taka', flag: '🇧🇩' },
  USD: { currency: 'USD', rate: 109.85, symbol: '$', name: 'US Dollar', flag: '🇺🇸' },
  EUR: { currency: 'EUR', rate: 119.50, symbol: '€', name: 'Euro', flag: '🇪🇺' },
  GBP: { currency: 'GBP', rate: 139.20, symbol: '£', name: 'British Pound', flag: '🇬🇧' },
  INR: { currency: 'INR', rate: 1.31, symbol: '₹', name: 'Indian Rupee', flag: '🇮🇳' },
  SGD: { currency: 'SGD', rate: 81.45, symbol: 'S$', name: 'Singapore Dollar', flag: '🇸🇬' },
  SAR: { currency: 'SAR', rate: 29.29, symbol: '﷼', name: 'Saudi Riyal', flag: '🇸🇦' },
};

export const currencyList: ExchangeRate[] = Object.values(mockExchangeRates);