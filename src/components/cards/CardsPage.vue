<script setup lang="ts">
import { ref, computed } from 'vue';
import { useCardStore } from '../../stores/card';
import { useBankStore } from '../../stores/bank';
import { useCurrencyStore } from '../../stores/currency';
import { formatCurrency, formatDate } from '../../utils/formatters';
import type { Currency } from '../../types';
import { PageHeader, StatCard, Badge, Modal, ProgressBar } from '../ui';

const cardStore = useCardStore();
const bankStore = useBankStore();
const currencyStore = useCurrencyStore();
const currencyList = currencyStore.currencyList;

// ==================== State ====================
const selectedCardId = ref<string | null>(null);
const showAddCardModal = ref(false);
const showUpdateBalanceModal = ref(false);
const showRecordPaymentModal = ref(false);

const balanceForm = ref({ amount: 0 });
const paymentForm = ref({ amount: 0, date: new Date().toISOString().split('T')[0] });

// ==================== Computed: Summary Stats ====================
const totalCreditLimit = computed(() => cardStore.totalCreditLimit);
const totalCreditUsed = computed(() => cardStore.totalCreditBalance);
const creditUtilization = computed(() => cardStore.totalCreditUtilization);
const activeCardsCount = computed(() => cardStore.cards.filter(c => c.isActive).length);

const utilizationColor = computed(() => {
  if (creditUtilization.value < 30) return 'accent' as const;
  if (creditUtilization.value < 70) return 'warning' as const;
  return 'danger' as const;
});

// ==================== Computed: Selected Card ====================
const selectedCard = computed(() => {
  if (!selectedCardId.value) return null;
  return cardStore.getCardById(selectedCardId.value) || null;
});

const selectedCardBank = computed(() => {
  if (!selectedCard.value) return null;
  return bankStore.bankAccounts.find(a => a.id === selectedCard.value!.bankAccountId) || null;
});

// ==================== Card Transactions (from bank store, filtered by cardId on expense transactions) ====================
// Note: Expenses in the bank transaction model don't have cardId directly,
// but we can show the linked bank account's transactions
const selectedCardTransactions = computed(() => {
  if (!selectedCard.value) return [];
  // Show transactions from the linked bank account
  return bankStore.getAccountTransactions(selectedCard.value.bankAccountId).slice(0, 10);
});

const monthlySpending = computed(() => {
  if (!selectedCard.value) return 0;
  const now = new Date();
  const currencyStore = useCurrencyStore();
  return bankStore.transactions
    .filter(t => {
      const d = new Date(t.date);
      return t.bankAccountId === selectedCard.value!.bankAccountId &&
        d.getMonth() === now.getMonth() &&
        d.getFullYear() === now.getFullYear() &&
        t.direction === 'debit';
    })
    .reduce((sum, t) => sum + currencyStore.convertToBase(t.amount, t.currency || 'BDT'), 0);
});

// ==================== Card Gradient ====================
function cardGradient(color: string): string {
  return `linear-gradient(135deg, ${color} 0%, ${adjustColor(color, -40)} 100%)`;
}

function adjustColor(hex: string, amount: number): string {
  const num = parseInt(hex.replace('#', ''), 16);
  const r = Math.min(255, Math.max(0, (num >> 16) + amount));
  const g = Math.min(255, Math.max(0, ((num >> 8) & 0x00FF) + amount));
  const b = Math.min(255, Math.max(0, (num & 0x0000FF) + amount));
  return `#${(1 << 24 | r << 16 | g << 8 | b).toString(16).slice(1)}`;
}

function getBrandLogo(brand: string): string {
  switch (brand) {
    case 'visa': return 'VISA';
    case 'mastercard': return 'MASTERCARD';
    case 'amex': return 'AMEX';
    case 'discover': return 'DISCOVER';
    default: return brand.toUpperCase();
  }
}

function getAvailableCredit(card: any): number {
  if (card.type !== 'credit' || !card.creditLimit) return 0;
  return card.creditLimit - card.currentBalance;
}

function openUpdateBalance(card: any) {
  selectedCardId.value = card.id;
  balanceForm.value.amount = card.currentBalance;
  showUpdateBalanceModal.value = true;
}

function submitUpdateBalance() {
  if (!selectedCardId.value) return;
  cardStore.updateCard(selectedCardId.value, { currentBalance: balanceForm.value.amount } as any);
  showUpdateBalanceModal.value = false;
}

function openRecordPayment(card: any) {
  selectedCardId.value = card.id;
  paymentForm.value = { amount: card.currentBalance * 0.05, date: new Date().toISOString().split('T')[0] };
  showRecordPaymentModal.value = true;
}

function submitCardPayment() {
  if (!selectedCardId.value) return;
  const card = cardStore.getCardById(selectedCardId.value);
  if (!card) return;
  const newBalance = Math.max(0, card.currentBalance - paymentForm.value.amount);
  cardStore.updateCard(selectedCardId.value, { currentBalance: newBalance } as any);
  showRecordPaymentModal.value = false;
}

// ==================== Add Card Form ====================
const cardForm = ref({
  name: '',
  type: 'credit' as 'debit' | 'credit',
  bankAccountId: '',
  cardNumber: '',
  holderName: '',
  expiryDate: '',
  brand: 'visa' as 'visa' | 'mastercard' | 'amex' | 'discover',
  creditLimit: '',
  billingCycleStart: 1,
  billingCycleEnd: 30,
  dueDate: 15,
  color: '#7c3aed',
  currency: 'BDT' as Currency,
  secondaryCurrency: '' as string | Currency,
});

function resetCardForm() {
  cardForm.value = {
    name: '',
    type: 'credit',
    bankAccountId: bankStore.bankAccounts[0]?.id || '',
    cardNumber: '',
    holderName: '',
    expiryDate: '',
    brand: 'visa',
    creditLimit: '',
    billingCycleStart: 1,
    billingCycleEnd: 30,
    dueDate: 15,
    color: '#7c3aed',
    currency: 'BDT' as Currency,
    secondaryCurrency: '' as string | Currency,
  };
}

function handleSaveCard() {
  if (!cardForm.value.name || !cardForm.value.cardNumber || !cardForm.value.holderName || !cardForm.value.expiryDate) return;

  cardStore.addCard({
    bankAccountId: cardForm.value.bankAccountId || bankStore.bankAccounts[0]?.id || '',
    name: cardForm.value.name,
    type: cardForm.value.type,
    cardNumber: cardForm.value.cardNumber,
    holderName: cardForm.value.holderName,
    expiryDate: cardForm.value.expiryDate,
    brand: cardForm.value.brand,
    creditLimit: cardForm.value.type === 'credit' ? (parseFloat(cardForm.value.creditLimit) || 0) : undefined,
    currentBalance: 0,
    billingCycle: {
      start: cardForm.value.billingCycleStart,
      end: cardForm.value.billingCycleEnd,
    },
    dueDate: cardForm.value.type === 'credit' ? cardForm.value.dueDate : 0,
    isActive: true,
    color: cardForm.value.color,
    currency: cardForm.value.currency,
    secondaryCurrency: cardForm.value.secondaryCurrency || undefined,
  });

  showAddCardModal.value = false;
  resetCardForm();
}

// ==================== Credit Card Color for Utilization ====================
function cardUtilColor(balance: number, limit: number): string {
  if (!limit) return 'bg-accent-500';
  const pct = (balance / limit) * 100;
  if (pct < 30) return 'bg-accent-500';
  if (pct < 70) return 'bg-amber-500';
  return 'bg-danger-500';
}
</script>

<template>
  <div class="animate-fade-in space-y-6">
    <!-- Page Header -->
    <PageHeader title="Cards" subtitle="Manage your credit and debit cards">
      <template #actions>
        <button @click="resetCardForm(); showAddCardModal = true" class="btn-primary">
          <span>+ Add Card</span>
        </button>
      </template>
    </PageHeader>

    <!-- Summary Stats -->
    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      <StatCard
        title="Total Credit Limit"
        :value="formatCurrency(totalCreditLimit)"
        icon="💳"
        color="primary"
      />
      <StatCard
        title="Total Credit Used"
        :value="formatCurrency(totalCreditUsed)"
        icon="📊"
        color="warning"
      />
      <StatCard
        title="Credit Utilization"
        :value="`${creditUtilization.toFixed(1)}%`"
        :icon="creditUtilization < 30 ? '✅' : creditUtilization < 70 ? '⚠️' : '🔴'"
        :color="utilizationColor"
      />
      <StatCard
        title="Active Cards"
        :value="String(activeCardsCount)"
        icon="🏦"
        color="info"
      />
    </div>

    <!-- Credit Utilization Bar -->
    <div class="card p-4">
      <p class="text-sm font-medium text-surface-700 dark:text-surface-300 mb-2">Overall Credit Utilization</p>
      <ProgressBar
        :value="totalCreditUsed"
        :max="totalCreditLimit || 1"
        :color="utilizationColor"
        :show-label="true"
      />
      <p class="text-xs mt-1.5" :class="creditUtilization < 30 ? 'text-accent-600 dark:text-accent-400' : creditUtilization < 70 ? 'text-amber-600 dark:text-amber-400' : 'text-danger-500 dark:text-danger-400'">
        {{ creditUtilization < 30 ? 'Great! Your credit utilization is healthy.' : creditUtilization < 70 ? 'Moderate utilization. Try to keep it below 30%.' : 'High utilization! Consider paying down your balance.' }}
      </p>
    </div>

    <!-- Card Display Grid -->
    <div v-if="cardStore.cards.length === 0">
      <div class="card p-12 text-center animate-fade-in">
        <div class="text-4xl mb-3">💳</div>
        <h3 class="text-lg font-semibold text-surface-700 dark:text-surface-300">No cards added</h3>
        <p class="text-sm text-surface-500 dark:text-surface-400 mt-1">Add your first credit or debit card</p>
        <button @click="resetCardForm(); showAddCardModal = true" class="btn-primary mt-4">
          <span>+ Add Card</span>
        </button>
      </div>
    </div>

    <div v-else>
      <!-- Visual Cards Grid -->
      <div class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6 mb-6">
        <div
          v-for="card in cardStore.cards.filter(c => c.isActive)"
          :key="card.id"
          @click="selectedCardId = selectedCardId === card.id ? null : card.id"
          class="cursor-pointer group"
        >
          <!-- Credit Card Visual -->
          <div
            class="relative rounded-2xl p-6 text-white shadow-lg transition-all duration-300 group-hover:shadow-xl group-hover:-translate-y-1"
            :class="{ 'ring-2 ring-white/50 ring-offset-2 ring-offset-surface-100 dark:ring-offset-surface-900': selectedCardId === card.id }"
            :style="{ background: cardGradient(card.color || '#7c3aed'), aspectRatio: '1.586 / 1' }"
          >
            <!-- Decorative circles -->
            <div class="absolute top-0 right-0 w-32 h-32 bg-white/10 rounded-full -translate-y-1/2 translate-x-1/2" />
            <div class="absolute bottom-0 left-0 w-24 h-24 bg-white/5 rounded-full translate-y-1/2 -translate-x-1/2" />

            <!-- Card content -->
            <div class="relative z-10 h-full flex flex-col justify-between">
              <!-- Top row: Name + Brand -->
              <div class="flex items-start justify-between">
                <div>
                  <p class="text-xs font-medium text-white/70 uppercase tracking-wider">{{ card.type === 'credit' ? 'Credit Card' : 'Debit Card' }}<span v-if="card.currency && card.currency !== 'BDT'" class="text-[10px] font-medium px-1.5 py-0.5 bg-white/20 rounded ml-2">{{ card.currency }}</span><span v-if="card.secondaryCurrency" class="text-[10px] font-medium px-1.5 py-0.5 bg-white/20 rounded">{{ card.secondaryCurrency }}</span></p>
                  <p class="text-sm font-semibold mt-0.5">{{ card.name }}</p>
                </div>
                <span class="text-lg font-bold tracking-wider opacity-90">{{ getBrandLogo(card.brand) }}</span>
              </div>

              <!-- Card Number -->
              <div>
                <p class="text-xl font-mono tracking-[0.2em] text-white/90">{{ card.cardNumber }}</p>
              </div>

              <!-- Bottom row: Holder + Expiry -->
              <div class="flex items-end justify-between">
                <div>
                  <p class="text-[10px] text-white/50 uppercase tracking-wider">Card Holder</p>
                  <p class="text-sm font-medium">{{ card.holderName }}</p>
                </div>
                <div class="text-right">
                  <p class="text-[10px] text-white/50 uppercase tracking-wider">Expires</p>
                  <p class="text-sm font-medium">{{ card.expiryDate }}</p>
                </div>
              </div>
            </div>
          </div>

          <!-- Card Info Below -->
          <div class="mt-3 px-1">
            <div v-if="card.type === 'credit'" class="flex items-center justify-between">
              <div>
                <p class="text-xs text-surface-500 dark:text-surface-400">Balance / Limit</p>
                <p class="text-sm font-semibold text-surface-900 dark:text-white tabular-nums">
                  {{ currencyStore.formatWithCurrency(card.currentBalance, card.currency || 'BDT') }} / {{ currencyStore.formatWithCurrency(card.creditLimit || 0, card.currency || 'BDT') }}
                </p>
              </div>
              <Badge :variant="((card.currentBalance / (card.creditLimit || 1)) * 100) < 30 ? 'success' : ((card.currentBalance / (card.creditLimit || 1)) * 100) < 70 ? 'warning' : 'danger'" size="sm">
                {{ ((card.currentBalance / (card.creditLimit || 1)) * 100).toFixed(0) }}% used
              </Badge>
            </div>
            <div v-else class="flex items-center justify-between">
              <div>
                <p class="text-xs text-surface-500 dark:text-surface-400">Linked Account</p>
                <p class="text-sm font-semibold text-surface-900 dark:text-white">
                  {{ bankStore.bankAccounts.find(a => a.id === card.bankAccountId)?.bankName || 'N/A' }}
                </p>
              </div>
              <Badge variant="info" size="sm">Debit</Badge>
            </div>
          </div>
        </div>
      </div>

      <!-- ==================== Card Detail View ==================== -->
      <Transition name="slide">
        <div v-if="selectedCard" class="space-y-4">
          <div class="flex items-center justify-between">
            <h2 class="text-lg font-semibold text-surface-900 dark:text-white">
              Card Details — {{ selectedCard.name }}
            </h2>
            <button @click="selectedCardId = null" class="text-sm text-surface-500 hover:text-surface-700 dark:hover:text-surface-300 transition-colors">
              ✕ Close
            </button>
          </div>

          <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <!-- Left: Card Info -->
            <div class="lg:col-span-1 space-y-4">
              <!-- Full Card Visual (larger) -->
              <div
                class="rounded-2xl p-6 text-white shadow-lg"
                :style="{ background: cardGradient(selectedCard.color || '#7c3aed'), aspectRatio: '1.586 / 1' }"
              >
                <div class="absolute top-0 right-0 w-32 h-32 bg-white/10 rounded-full -translate-y-1/2 translate-x-1/2" style="position:absolute" />
                <div class="relative z-10 h-full flex flex-col justify-between">
                  <div class="flex items-start justify-between">
                    <div>
                      <p class="text-xs font-medium text-white/70 uppercase tracking-wider">{{ selectedCard.type === 'credit' ? 'Credit Card' : 'Debit Card' }}</p>
                      <p class="text-sm font-semibold mt-0.5">{{ selectedCard.name }}</p>
                    </div>
                    <span class="text-lg font-bold tracking-wider opacity-90">{{ getBrandLogo(selectedCard.brand) }}</span>
                  </div>
                  <div>
                    <p class="text-xl font-mono tracking-[0.2em] text-white/90">{{ selectedCard.cardNumber }}</p>
                  </div>
                  <div class="flex items-end justify-between">
                    <div>
                      <p class="text-[10px] text-white/50 uppercase tracking-wider">Card Holder</p>
                      <p class="text-sm font-medium">{{ selectedCard.holderName }}</p>
                    </div>
                    <div class="text-right">
                      <p class="text-[10px] text-white/50 uppercase tracking-wider">Expires</p>
                      <p class="text-sm font-medium">{{ selectedCard.expiryDate }}</p>
                    </div>
                  </div>
                </div>
              </div>

              <!-- Card Details Panel -->
              <div class="card p-5 space-y-4">
                <h3 class="font-semibold text-surface-900 dark:text-white">Card Information</h3>

                <div v-if="selectedCard.type === 'credit'" class="space-y-3">
                  <div class="flex justify-between">
                    <span class="text-sm text-surface-500 dark:text-surface-400">Credit Limit</span>
                    <span class="text-sm font-semibold text-surface-900 dark:text-white tabular-nums">{{ currencyStore.formatWithCurrency(selectedCard.creditLimit || 0, selectedCard.currency || 'BDT') }}</span>
                  </div>
                  <div class="flex justify-between">
                    <span class="text-sm text-surface-500 dark:text-surface-400">Current Balance</span>
                    <span class="text-sm font-semibold text-danger-500 dark:text-danger-400 tabular-nums">{{ currencyStore.formatWithCurrency(selectedCard.currentBalance, selectedCard.currency || 'BDT') }}</span>
                  </div>
                  <div class="flex justify-between">
                    <span class="text-sm text-surface-500 dark:text-surface-400">Available Credit</span>
                    <span class="text-sm font-semibold text-accent-600 dark:text-accent-400 tabular-nums">{{ currencyStore.formatWithCurrency(getAvailableCredit(selectedCard), selectedCard.currency || 'BDT') }}</span>
                  </div>
                  <ProgressBar
                    :value="selectedCard.currentBalance"
                    :max="selectedCard.creditLimit || 1"
                    :color="((selectedCard.currentBalance / (selectedCard.creditLimit || 1)) * 100) < 30 ? 'accent' : ((selectedCard.currentBalance / (selectedCard.creditLimit || 1)) * 100) < 70 ? 'warning' : 'danger'"
                    size="sm"
                  />
                  <div class="flex justify-between">
                    <span class="text-sm text-surface-500 dark:text-surface-400">Min Payment Due</span>
                    <span class="text-sm font-semibold text-warning-600 dark:text-warning-400 tabular-nums">{{ currencyStore.formatWithCurrency(selectedCard.currentBalance * 0.05, selectedCard.currency || 'BDT') }}</span>
                  </div>
                </div>

                <div v-else class="space-y-3">
                  <div class="flex justify-between">
                    <span class="text-sm text-surface-500 dark:text-surface-400">Linked Account</span>
                    <span class="text-sm font-semibold text-surface-900 dark:text-white">{{ selectedCardBank?.bankName || 'N/A' }}</span>
                  </div>
                  <div class="flex justify-between">
                    <span class="text-sm text-surface-500 dark:text-surface-400">Account Balance</span>
                    <span class="text-sm font-semibold text-surface-900 dark:text-white tabular-nums">
                      {{ formatCurrency(selectedCardBank ? bankStore.getAccountBalance(selectedCardBank.id) : 0) }}
                    </span>
                  </div>
                </div>

                <!-- Secondary Currency -->
                <div v-if="selectedCard.secondaryCurrency" class="pt-3 border-t border-surface-200 dark:border-surface-700 space-y-2">
                  <h4 class="text-sm font-medium text-surface-700 dark:text-surface-300">Secondary Currency — {{ selectedCard.secondaryCurrency }}</h4>
                  <p class="text-xs text-surface-400">Dual-currency card. Transactions in {{ selectedCard.secondaryCurrency }} are converted automatically.</p>
                </div>

                <!-- Billing Cycle -->
                <div v-if="selectedCard.type === 'credit'" class="pt-3 border-t border-surface-200 dark:border-surface-700 space-y-2">
                  <h4 class="text-sm font-medium text-surface-700 dark:text-surface-300">Billing Cycle</h4>
                  <div class="flex justify-between">
                    <span class="text-sm text-surface-500 dark:text-surface-400">Cycle</span>
                    <span class="text-sm text-surface-700 dark:text-surface-300">{{ selectedCard.billingCycle.start }}th — {{ selectedCard.billingCycle.end }}th</span>
                  </div>
                  <div class="flex justify-between">
                    <span class="text-sm text-surface-500 dark:text-surface-400">Payment Due</span>
                    <span class="text-sm font-medium text-danger-500 dark:text-danger-400">{{ selectedCard.dueDate }}th of month</span>
                  </div>
                </div>

                <!-- Status -->
                <div class="pt-3 border-t border-surface-200 dark:border-surface-700 flex items-center justify-between">
                  <span class="text-sm text-surface-500 dark:text-surface-400">Status</span>
                  <Badge :variant="selectedCard.isActive ? 'success' : 'neutral'" size="sm">
                    {{ selectedCard.isActive ? 'Active' : 'Inactive' }}
                  </Badge>
                </div>

                <!-- Action Buttons -->
                <div v-if="selectedCard.type === 'credit'" class="pt-3 border-t border-surface-200 dark:border-surface-700 space-y-2">
                  <button @click="openUpdateBalance(selectedCard)" class="btn-secondary w-full text-sm justify-center">
                    ✏️ Update Balance
                  </button>
                  <button @click="openRecordPayment(selectedCard)" class="btn-primary w-full text-sm justify-center">
                    💳 Record Payment
                  </button>
                </div>
              </div>
            </div>

            <!-- Right: Spending & Transactions -->
            <div class="lg:col-span-2 space-y-4">
              <!-- Spending Stats -->
              <div class="card p-5">
                <h3 class="font-semibold text-surface-900 dark:text-white mb-3">Spending This Month</h3>
                <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
                  <div class="bg-surface-50 dark:bg-surface-700/50 rounded-xl p-4">
                    <p class="text-xs text-surface-500 dark:text-surface-400">Total Spent</p>
                    <p class="text-lg font-bold text-surface-900 dark:text-white tabular-nums mt-1">{{ formatCurrency(monthlySpending) }}</p>
                  </div>
                  <div class="bg-surface-50 dark:bg-surface-700/50 rounded-xl p-4">
                    <p class="text-xs text-surface-500 dark:text-surface-400">Transactions</p>
                    <p class="text-lg font-bold text-surface-900 dark:text-white tabular-nums mt-1">{{ selectedCardTransactions.length }}</p>
                  </div>
                  <div class="bg-surface-50 dark:bg-surface-700/50 rounded-xl p-4">
                    <p class="text-xs text-surface-500 dark:text-surface-400">Avg Transaction</p>
                    <p class="text-lg font-bold text-surface-900 dark:text-white tabular-nums mt-1">
                      {{ selectedCardTransactions.length ? formatCurrency(monthlySpending / selectedCardTransactions.length) : formatCurrency(0) }}
                    </p>
                  </div>
                </div>
              </div>

              <!-- Recent Transactions -->
              <div class="card overflow-hidden">
                <div class="px-5 py-4 border-b border-surface-200 dark:border-surface-700">
                  <h3 class="font-semibold text-surface-900 dark:text-white">Recent Transactions</h3>
                </div>
                <div v-if="selectedCardTransactions.length === 0" class="p-8 text-center">
                  <p class="text-sm text-surface-400 dark:text-surface-500">No recent transactions for this card's linked account</p>
                </div>
                <div v-else>
                  <div
                    v-for="txn in selectedCardTransactions"
                    :key="txn.id"
                    class="flex items-center justify-between px-5 py-3.5 border-b border-surface-100 dark:border-surface-700/50 last:border-0 hover:bg-surface-50 dark:hover:bg-surface-700/30 transition-colors"
                  >
                    <div class="flex items-center gap-3 min-w-0">
                      <div class="w-9 h-9 rounded-lg flex items-center justify-center text-sm shrink-0" :class="txn.direction === 'credit' ? 'bg-accent-100 dark:bg-accent-500/20' : 'bg-danger-100 dark:bg-danger-500/20'">
                        {{ txn.type === 'income' ? '💰' : txn.type === 'transfer' ? '🔄' : '🛒' }}
                      </div>
                      <div class="min-w-0">
                        <p class="text-sm font-medium text-surface-900 dark:text-white truncate">{{ txn.description }}</p>
                        <p class="text-xs text-surface-500 dark:text-surface-400">{{ formatDate(txn.date, 'short') }}</p>
                      </div>
                    </div>
                    <div class="text-right shrink-0 ml-3">
                      <p class="text-sm font-semibold tabular-nums" :class="txn.direction === 'credit' ? 'text-accent-600 dark:text-accent-400' : 'text-danger-500 dark:text-danger-400'">
                        {{ txn.direction === 'credit' ? '+' : '-' }}{{ currencyStore.formatWithCurrency(txn.amount, txn.currency || 'BDT') }}
                      </p>
                      <span v-if="txn.currency && txn.currency !== 'BDT'" class="text-[10px] text-surface-400 block tabular-nums">
                        ≈ {{ formatCurrency(currencyStore.convertToBase(txn.amount, txn.currency)) }}
                      </span>
                      <Badge
                        :variant="txn.type === 'income' ? 'success' : txn.type === 'expense' ? 'danger' : 'warning'"
                        size="sm"
                      >
                        {{ txn.type }}
                      </Badge>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </Transition>
    </div>

    <!-- ==================== Add Card Modal ==================== -->
    <Modal
      :is-open="showAddCardModal"
      title="Add Card"
      size="lg"
      @close="showAddCardModal = false"
    >
      <form @submit.prevent="handleSaveCard" class="space-y-4">
        <!-- Card Name & Type -->
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label class="field-label">Card Name <span class="text-danger-500">*</span></label>
            <input v-model="cardForm.name" type="text" placeholder="e.g., City Bank Visa Credit Card" class="input-field" />
          </div>
          <div>
            <label class="field-label">Card Type <span class="text-danger-500">*</span></label>
            <select v-model="cardForm.type" class="input-field">
              <option value="credit">Credit Card</option>
              <option value="debit">Debit Card</option>
            </select>
          </div>
        </div>

        <!-- Linked Account & Card Number -->
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label class="field-label">Linked Bank Account</label>
            <select v-model="cardForm.bankAccountId" class="input-field">
              <option value="">Select Account</option>
              <option v-for="acc in bankStore.bankAccounts" :key="acc.id" :value="acc.id">
                {{ acc.bankName }} — {{ acc.accountNumber }}
              </option>
            </select>
          </div>
          <div>
            <label class="field-label">Card Number <span class="text-danger-500">*</span></label>
            <input v-model="cardForm.cardNumber" type="text" placeholder="**** **** **** 1234" class="input-field" />
          </div>
        </div>

        <!-- Currency -->
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label class="field-label">Card Currency</label>
            <select v-model="cardForm.currency" class="input-field">
              <option v-for="c in currencyList" :key="c.currency" :value="c.currency">{{ c.flag }} {{ c.currency }} ({{ c.symbol }})</option>
            </select>
          </div>
          <div v-if="cardForm.type === 'credit'">
            <label class="field-label">Secondary Currency (optional)</label>
            <select v-model="cardForm.secondaryCurrency" class="input-field">
              <option value="">None</option>
              <option v-for="c in currencyList.filter(x => x.currency !== cardForm.currency)" :key="c.currency" :value="c.currency">{{ c.flag }} {{ c.currency }} ({{ c.symbol }})</option>
            </select>
          </div>
        </div>

        <!-- Holder Name & Brand -->
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label class="field-label">Card Holder Name <span class="text-danger-500">*</span></label>
            <input v-model="cardForm.holderName" type="text" placeholder="Full name on card" class="input-field" />
          </div>
          <div>
            <label class="field-label">Brand</label>
            <select v-model="cardForm.brand" class="input-field">
              <option value="visa">VISA</option>
              <option value="mastercard">MASTERCARD</option>
              <option value="amex">AMEX</option>
              <option value="discover">DISCOVER</option>
            </select>
          </div>
        </div>

        <!-- Expiry Date & Credit Limit -->
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label class="field-label">Expiry Date <span class="text-danger-500">*</span></label>
            <input v-model="cardForm.expiryDate" type="text" placeholder="MM/YY" class="input-field" />
          </div>
          <div v-if="cardForm.type === 'credit'">
            <label class="field-label">Credit Limit ({{ currencyStore.getSymbol(cardForm.currency) }})</label>
            <input v-model="cardForm.creditLimit" type="number" min="0" step="1000" placeholder="e.g., 100000" class="input-field" />
          </div>
        </div>

        <!-- Billing Cycle (credit only) -->
        <template v-if="cardForm.type === 'credit'">
          <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div>
              <label class="field-label">Billing Cycle Start</label>
              <input v-model.number="cardForm.billingCycleStart" type="number" min="1" max="31" class="input-field" />
            </div>
            <div>
              <label class="field-label">Billing Cycle End</label>
              <input v-model.number="cardForm.billingCycleEnd" type="number" min="1" max="31" class="input-field" />
            </div>
            <div>
              <label class="field-label">Payment Due Day</label>
              <input v-model.number="cardForm.dueDate" type="number" min="1" max="31" class="input-field" />
            </div>
          </div>
        </template>

        <!-- Color -->
        <div>
          <label class="field-label">Card Color</label>
          <div class="flex items-center gap-3">
            <input v-model="cardForm.color" type="color" class="w-10 h-10 rounded-lg border border-surface-300 dark:border-surface-600 cursor-pointer" />
            <span class="text-sm text-surface-500 dark:text-surface-400 font-mono">{{ cardForm.color }}</span>
            <!-- Preview mini card -->
            <div class="w-16 h-10 rounded-lg ml-2" :style="{ background: cardGradient(cardForm.color) }" />
          </div>
        </div>

        <!-- Actions -->
        <div class="flex justify-end gap-3 pt-4 border-t border-surface-200 dark:border-surface-700">
          <button type="button" @click="showAddCardModal = false" class="btn-secondary">Cancel</button>
          <button type="submit" class="btn-primary">
            <span>Add Card</span>
          </button>
        </div>
      </form>
    </Modal>

    <!-- ==================== Update Balance Modal ==================== -->
    <Modal
      :is-open="showUpdateBalanceModal"
      title="Update Card Balance"
      size="sm"
      @close="showUpdateBalanceModal = false"
    >
      <div class="space-y-4">
        <p class="text-sm text-surface-500 dark:text-surface-400">
          Set the current outstanding balance on this credit card.
        </p>
        <div>
          <label class="block text-sm font-medium text-surface-700 dark:text-surface-300 mb-1">Current Balance ({{ selectedCard.currency || 'BDT' }})</label>
          <input v-model.number="balanceForm.amount" type="number" min="0" step="100" class="input-field tabular-nums" placeholder="0" />
        </div>
        <div class="flex justify-end gap-3 pt-2">
          <button class="btn-secondary" @click="showUpdateBalanceModal = false">Cancel</button>
          <button class="btn-primary" @click="submitUpdateBalance">Update</button>
        </div>
      </div>
    </Modal>

    <!-- ==================== Record Payment Modal ==================== -->
    <Modal
      :is-open="showRecordPaymentModal"
      title="Record Card Payment"
      size="sm"
      @close="showRecordPaymentModal = false"
    >
      <div class="space-y-4">
        <div v-if="selectedCard" class="bg-surface-50 dark:bg-surface-700/50 rounded-lg p-3 flex items-center justify-between">
          <span class="text-sm text-surface-600 dark:text-surface-400">Current Balance</span>
          <span class="text-sm font-bold text-danger-500 tabular-nums">{{ currencyStore.formatWithCurrency(selectedCard.currentBalance, selectedCard.currency || 'BDT') }}</span>
        </div>
        <div>
          <label class="block text-sm font-medium text-surface-700 dark:text-surface-300 mb-1">Payment Amount ({{ selectedCard.currency || 'BDT' }})</label>
          <input v-model.number="paymentForm.amount" type="number" min="0" step="100" class="input-field tabular-nums" placeholder="0" />
        </div>
        <div>
          <label class="block text-sm font-medium text-surface-700 dark:text-surface-300 mb-1">Payment Date</label>
          <input v-model="paymentForm.date" type="date" class="input-field" />
        </div>
        <div v-if="selectedCard" class="bg-accent-50 dark:bg-accent-500/10 border border-accent-200 dark:border-accent-500/30 rounded-lg p-3">
          <p class="text-xs text-accent-600 dark:text-accent-400">
            New balance will be: <strong class="tabular-nums">{{ currencyStore.formatWithCurrency(Math.max(0, selectedCard.currentBalance - paymentForm.amount), selectedCard.currency || 'BDT') }}</strong>
          </p>
        </div>
        <div class="flex justify-end gap-3 pt-2">
          <button class="btn-secondary" @click="showRecordPaymentModal = false">Cancel</button>
          <button class="btn-primary" @click="submitCardPayment">Record Payment</button>
        </div>
      </div>
    </Modal>
  </div>
</template>

<style scoped>
.slide-enter-active {
  transition: all 0.3s ease-out;
}
.slide-leave-active {
  transition: all 0.2s ease-in;
}
.slide-enter-from {
  opacity: 0;
  transform: translateY(10px);
}
.slide-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}
</style>
