import '../lib/pinia-init';
import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import type { Currency } from '../types';
import { mockExchangeRates as defaultRates } from '../mock-data/exchange-rates';
import type { ExchangeRate } from '../mock-data/exchange-rates';

export const useCurrencyStore = defineStore('currency', () => {
  // Reactive exchange rates — can be edited from Settings
  const rates = ref<Record<string, ExchangeRate>>(
    Object.fromEntries(Object.entries(defaultRates).map(([k, v]) => [k, { ...v }]))
  );

  const baseCurrency = ref<Currency>('BDT');

  function convertToBase(amount: number, currency: Currency): number {
    if (!currency || currency === baseCurrency.value) return amount;
    const rate = rates.value[currency]?.rate;
    if (!rate) return amount;
    return Math.round(amount * rate);
  }

  function convertFromBase(amount: number, currency: Currency): number {
    if (!currency || currency === baseCurrency.value) return amount;
    const rate = rates.value[currency]?.rate;
    if (!rate || rate === 0) return amount;
    return Math.round((amount / rate) * 100) / 100;
  }

  function getRate(currency: Currency): number {
    return rates.value[currency]?.rate ?? 1;
  }

  function getSymbol(currency: Currency): string {
    return rates.value[currency]?.symbol ?? '৳';
  }

  function formatWithCurrency(amount: number, currency: Currency): string {
    const sym = getSymbol(currency);
    const formatted = new Intl.NumberFormat('en-US', {
      minimumFractionDigits: currency === 'BDT' || currency === 'INR' ? 0 : 2,
      maximumFractionDigits: currency === 'BDT' || currency === 'INR' ? 0 : 2,
    }).format(amount);
    return `${sym}${formatted}`;
  }

  // Update a single exchange rate
  function updateRate(currency: Currency, newRate: number) {
    if (rates.value[currency]) {
      rates.value[currency] = { ...rates.value[currency], rate: newRate };
    }
  }

  // Get all rates as a list (for Settings UI)
  const allRates = computed<ExchangeRate[]>(() => Object.values(rates.value));

  // Currency list for dropdowns — components should use this instead of importing mock-data
  const currencyList = computed<ExchangeRate[]>(() => Object.values(rates.value));

  // Set base currency
  function setBaseCurrency(currency: Currency) {
    baseCurrency.value = currency;
  }

  // Reset rates to defaults
  function resetRates() {
    rates.value = Object.fromEntries(
      Object.entries(defaultRates).map(([k, v]) => [k, { ...v }])
    );
  }

  return {
    baseCurrency,
    rates,
    convertToBase,
    convertFromBase,
    getRate,
    getSymbol,
    formatWithCurrency,
    allRates,
    currencyList,
    updateRate,
    setBaseCurrency,
    resetRates,
  };
});
