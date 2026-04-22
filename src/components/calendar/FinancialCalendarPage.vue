<script setup lang="ts">
import { ref, computed } from 'vue';
import { useCalendarStore } from '../../stores/calendar';
import { useCurrencyStore } from '../../stores/currency';
import { formatCurrency, formatDate } from '../../utils/formatters';
import { PageHeader, StatCard, Badge, Modal, EmptyState, Tabs } from '../ui';
import type { CalendarEvent, CalendarEventCategory, CalendarEventStatus, RecurrencePattern } from '../../types';

const store = useCalendarStore();
const currencyStore = useCurrencyStore();

// ============ View State ============
type ViewMode = 'calendar' | 'list';
type TabKey = 'all' | 'upcoming' | 'overdue' | CalendarEventCategory;
const viewMode = ref<ViewMode>('calendar');
const activeTab = ref<TabKey>('all');

const tabItems = [
  { key: 'all', label: 'All', icon: '📅' },
  { key: 'upcoming', label: 'Upcoming', icon: '📋' },
  { key: 'overdue', label: 'Overdue', icon: '🔴' },
  { key: 'emi_payment', label: 'EMI', icon: '💰' },
  { key: 'insurance_premium', label: 'Insurance', icon: '🛡️' },
  { key: 'bill_payment', label: 'Bills', icon: '📄' },
  { key: 'salary', label: 'Salary', icon: '💵' },
  { key: 'rental_income', label: 'Rental', icon: '🏠' },
  { key: 'investment_deposit', label: 'Deposit', icon: '🏦' },
  { key: 'investment_maturity', label: 'Maturity', icon: '🎯' },
  { key: 'dividend', label: 'Dividend', icon: '📈' },
  { key: 'tax_deadline', label: 'Tax', icon: '🧾' },
  { key: 'lending_payment', label: 'Lending', icon: '🤝' },
  { key: 'subscription', label: 'Subscriptions', icon: '📺' },
  { key: 'maintenance', label: 'Maintenance', icon: '🔧' },
  { key: 'document_renewal', label: 'Renewals', icon: '📝' },
  { key: 'milestone', label: 'Milestones', icon: '⭐' },
];

// ============ Calendar State ============
const today = new Date();
const currentYear = ref(today.getFullYear());
const currentMonth = ref(today.getMonth());

const monthNames = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'];
const dayNames = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];

function prevMonth() { currentMonth.value--; if (currentMonth.value < 0) { currentMonth.value = 11; currentYear.value--; } }
function nextMonth() { currentMonth.value++; if (currentMonth.value > 11) { currentMonth.value = 0; currentYear.value++; } }
function goToday() { currentYear.value = today.getFullYear(); currentMonth.value = today.getMonth(); }

// ============ Modal State ============
const selectedEvent = ref<CalendarEvent | null>(null);
const showDetailModal = ref(false);
const showAddModal = ref(false);
const showDeleteConfirm = ref(false);
const selectedDate = ref<string | null>(null);

// ============ Config ============
const categoryConfig: Record<CalendarEventCategory, { label: string; icon: string; color: string }> = {
  emi_payment: { label: 'EMI Payment', icon: '💰', color: 'danger' },
  insurance_premium: { label: 'Insurance Premium', icon: '🛡️', color: 'success' },
  bill_payment: { label: 'Bill Payment', icon: '📄', color: 'warning' },
  investment_maturity: { label: 'Investment Maturity', icon: '🎯', color: 'info' },
  investment_deposit: { label: 'Investment Deposit', icon: '🏦', color: 'primary' },
  dividend: { label: 'Dividend / Interest', icon: '📈', color: 'success' },
  tax_deadline: { label: 'Tax Deadline', icon: '🧾', color: 'danger' },
  salary: { label: 'Salary', icon: '💵', color: 'success' },
  rental_income: { label: 'Rental Income', icon: '🏠', color: 'success' },
  rental_payment: { label: 'Rental Payment', icon: '🏠', color: 'warning' },
  lending_payment: { label: 'Lending Payment', icon: '🤝', color: 'info' },
  subscription: { label: 'Subscription', icon: '📺', color: 'neutral' },
  maintenance: { label: 'Maintenance', icon: '🔧', color: 'warning' },
  document_renewal: { label: 'Document Renewal', icon: '📝', color: 'info' },
  milestone: { label: 'Milestone', icon: '⭐', color: 'primary' },
  other: { label: 'Other', icon: '📎', color: 'neutral' },
};

const statusConfig: Record<CalendarEventStatus, { variant: 'success' | 'danger' | 'warning' | 'info' | 'neutral'; label: string }> = {
  upcoming: { variant: 'info', label: 'Upcoming' },
  completed: { variant: 'success', label: 'Completed' },
  overdue: { variant: 'danger', label: 'Overdue' },
  cancelled: { variant: 'neutral', label: 'Cancelled' },
};

const priorityConfig = { high: { label: 'High', color: 'text-danger-500' }, medium: { label: 'Medium', color: 'text-warning-500' }, low: { label: 'Low', color: 'text-surface-400' } };

const linkedEntityLabels: Record<string, string> = {
  loan: 'Loan', mortgage: 'Mortgage', insurance: 'Insurance',
  investment: 'Investment', lending: 'Lending', invoice: 'Invoice',
  document: 'Document', card: 'Card', other: 'Other',
};

// ============ Helpers ============
function fmtCur(amount: number, currency?: string): string {
  if (currency && currency !== 'BDT') return currencyStore.formatWithCurrency(amount, currency as any);
  return formatCurrency(amount, 'BDT');
}

function isToday(dateStr: string): boolean {
  const d = new Date(dateStr);
  const t = new Date();
  return d.getFullYear() === t.getFullYear() && d.getMonth() === t.getMonth() && d.getDate() === t.getDate();
}

function isPast(dateStr: string): boolean {
  const d = new Date(dateStr);
  d.setHours(0, 0, 0, 0);
  const t = new Date();
  t.setHours(0, 0, 0, 0);
  return d < t;
}

function daysUntil(dateStr: string): number {
  const now = new Date();
  now.setHours(0, 0, 0, 0);
  const target = new Date(dateStr);
  target.setHours(0, 0, 0, 0);
  return Math.ceil((target.getTime() - now.getTime()) / (1000 * 60 * 60 * 24));
}

// ============ Calendar Grid ============
const calendarDays = computed(() => {
  const year = currentYear.value;
  const month = currentMonth.value;
  const firstDay = new Date(year, month, 1).getDay();
  const daysInMonth = new Date(year, month + 1, 0).getDate();
  const daysInPrevMonth = new Date(year, month, 0).getDate();

  const days: { date: number; month: number; year: number; isCurrentMonth: boolean }[] = [];

  // Previous month days
  for (let i = firstDay - 1; i >= 0; i--) {
    days.push({ date: daysInPrevMonth - i, month: month - 1, year: month === 0 ? year - 1 : year, isCurrentMonth: false });
  }

  // Current month days
  for (let i = 1; i <= daysInMonth; i++) {
    days.push({ date: i, month, year, isCurrentMonth: true });
  }

  // Next month days
  const remaining = 42 - days.length;
  for (let i = 1; i <= remaining; i++) {
    days.push({ date: i, month: month + 1, year: month === 11 ? year + 1 : year, isCurrentMonth: false });
  }

  return days;
});

function getEventsForDay(day: number): CalendarEvent[] {
  const year = currentYear.value;
  const month = currentMonth.value;
  const dateStr = `${year}-${String(month + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
  return store.getEventsForDate(dateStr);
}

function isIncomeCategory(cat: CalendarEventCategory): boolean {
  return ['salary', 'rental_income', 'dividend'].includes(cat);
}

// ============ Filtered Events ============
const filteredEvents = computed(() => {
  if (activeTab.value === 'all') return store.events;
  if (activeTab.value === 'upcoming') return store.upcomingEvents;
  if (activeTab.value === 'overdue') return store.overdueEvents;
  return store.getByCategory(activeTab.value as CalendarEventCategory);
});

const filteredUpcoming = computed(() => {
  if (activeTab.value === 'all') return store.upcomingEvents;
  if (activeTab.value === 'overdue') return [];
  if (activeTab.value === 'upcoming') return store.upcomingEvents;
  return store.upcomingEvents.filter(e => e.category === activeTab.value);
});

const filteredOverdue = computed(() => {
  if (activeTab.value === 'all') return store.overdueEvents;
  if (activeTab.value === 'overdue') return store.overdueEvents;
  return store.overdueEvents.filter(e => e.category === activeTab.value);
});

// ============ Add Event Form ============
const addForm = ref({
  title: '',
  description: '',
  category: 'bill_payment' as CalendarEventCategory,
  status: 'upcoming' as CalendarEventStatus,
  amount: 0,
  currency: 'BDT' as string,
  eventDate: new Date().toISOString().split('T')[0],
  endDate: '' as string,
  recurrence: 'none' as RecurrencePattern,
  recurrenceDayOfMonth: 1,
  reminderDaysBefore: 3,
  reminderEnabled: true,
  secondReminderDaysBefore: 0,
  color: '#3b82f6',
  linkedEntityId: '',
  linkedEntityType: '' as string,
  priority: 'medium' as 'low' | 'medium' | 'high',
  notes: '',
  tags: '' as string,
});

const incomeCategories: CalendarEventCategory[] = ['salary', 'rental_income', 'dividend'];

// ============ Actions ============
function openDetail(ev: CalendarEvent) {
  selectedEvent.value = ev;
  showDetailModal.value = true;
}

function openAddModal(dateStr?: string) {
  resetAddForm();
  if (dateStr) {
    addForm.value.eventDate = dateStr;
    selectedDate.value = dateStr;
  }
  showAddModal.value = true;
}

function resetAddForm() {
  addForm.value = {
    title: '', description: '', category: 'bill_payment', status: 'upcoming',
    amount: 0, currency: 'BDT', eventDate: new Date().toISOString().split('T')[0],
    endDate: '', recurrence: 'none', recurrenceDayOfMonth: 1,
    reminderDaysBefore: 3, reminderEnabled: true, secondReminderDaysBefore: 0,
    color: '#3b82f6', linkedEntityId: '', linkedEntityType: '',
    priority: 'medium', notes: '', tags: '',
  };
}

function submitAddEvent() {
  const f = addForm.value;
  if (!f.title) return;
  const tags = f.tags ? f.tags.split(',').map(t => t.trim()).filter(Boolean) : [];

  store.addEvent({
    title: f.title,
    description: f.description || undefined,
    category: f.category,
    status: f.status,
    amount: f.amount || undefined,
    currency: f.currency as any,
    eventDate: new Date(f.eventDate).toISOString(),
    endDate: f.endDate ? new Date(f.endDate).toISOString() : undefined,
    recurrence: f.recurrence,
    recurrenceDayOfMonth: f.recurrence !== 'none' ? f.recurrenceDayOfMonth : undefined,
    reminderDaysBefore: f.reminderDaysBefore,
    reminderEnabled: f.reminderEnabled,
    secondReminderDaysBefore: f.secondReminderDaysBefore || undefined,
    color: f.color,
    linkedEntityId: f.linkedEntityId || undefined,
    linkedEntityType: (f.linkedEntityType as any) || undefined,
    priority: f.priority,
    notes: f.notes || undefined,
    tags,
  });
  showAddModal.value = false;
}

function confirmDelete() {
  if (!selectedEvent.value) return;
  store.deleteEvent(selectedEvent.value.id);
  showDeleteConfirm.value = false;
  showDetailModal.value = false;
  selectedEvent.value = null;
}

function handleComplete(id: string) { store.completeEvent(id); }
function handleCancel(id: string) { store.cancelEvent(id); }
function handleRestore(id: string) { store.markAsUpcoming(id); }

const recurrenceLabels: Record<string, string> = {
  none: 'One-time', daily: 'Daily', weekly: 'Weekly', biweekly: 'Bi-weekly',
  monthly: 'Monthly', quarterly: 'Quarterly', semiannually: 'Semi-annually',
  annually: 'Annually', custom: 'Custom',
};
</script>

<template>
  <div class="animate-fade-in space-y-6">
    <!-- Page Header -->
    <PageHeader title="Financial Calendar" subtitle="Track bills, EMIs, deadlines, income, and all your financial events">
      <template #actions>
        <div class="flex items-center gap-2">
          <!-- View Toggle -->
          <div class="flex rounded-lg border border-surface-200 dark:border-surface-700 overflow-hidden">
            <button @click="viewMode = 'calendar'" :class="viewMode === 'calendar' ? 'bg-primary-600 text-white' : 'text-surface-600 dark:text-surface-300 hover:bg-surface-100 dark:hover:bg-surface-700'" class="px-3 py-2 text-sm font-medium transition-colors">
              Calendar
            </button>
            <button @click="viewMode = 'list'" :class="viewMode === 'list' ? 'bg-primary-600 text-white' : 'text-surface-600 dark:text-surface-300 hover:bg-surface-100 dark:hover:bg-surface-700'" class="px-3 py-2 text-sm font-medium transition-colors">
              List
            </button>
          </div>
          <button class="btn-primary" @click="openAddModal()">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/></svg>
            Add Event
          </button>
        </div>
      </template>
    </PageHeader>

    <!-- Tabs -->
    <Tabs :tabs="tabItems" :active-tab="activeTab" @update:active-tab="(k: string) => activeTab = k as TabKey" />

    <!-- Summary Stats -->
    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      <StatCard title="This Month" :value="String(store.eventsThisMonth.length) + ' events'" icon="📅" color="primary" />
      <StatCard title="Upcoming" :value="String(store.upcomingEvents.length)" icon="📋" color="info" />
      <StatCard title="Overdue" :value="String(store.overdueEvents.length)" icon="🔴" :color="store.overdueEvents.length > 0 ? 'danger' : 'success'" />
      <StatCard title="Recurring" :value="String(store.recurringEvents.length)" icon="🔄" color="warning" />
    </div>

    <!-- Overdue Alert -->
    <div v-if="filteredOverdue.length > 0" class="bg-danger-50 dark:bg-danger-500/10 border border-danger-200 dark:border-danger-500/30 rounded-xl p-4">
      <div class="flex items-center gap-3 mb-2">
        <svg class="w-5 h-5 text-danger-500 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z"/></svg>
        <h4 class="font-semibold text-danger-700 dark:text-danger-300">Overdue Events ({{ filteredOverdue.length }})</h4>
      </div>
      <div class="space-y-2">
        <div v-for="ev in filteredOverdue.slice(0, 5)" :key="ev.id" class="flex items-center justify-between text-sm">
          <span class="text-danger-600 dark:text-danger-400">
            {{ categoryConfig[ev.category]?.icon }} {{ ev.title }}
            <span v-if="ev.amount" class="ml-1 font-medium">{{ fmtCur(ev.amount, ev.currency) }}</span>
          </span>
          <button @click="openDetail(ev)" class="text-danger-600 dark:text-danger-400 hover:underline text-xs font-medium">View</button>
        </div>
      </div>
    </div>

    <!-- ==================== CALENDAR VIEW ==================== -->
    <div v-if="viewMode === 'calendar'">
      <!-- Month Navigation -->
      <div class="flex items-center justify-between mb-4">
        <button @click="prevMonth" class="p-2 rounded-lg hover:bg-surface-100 dark:hover:bg-surface-700 transition-colors">
          <svg class="w-5 h-5 text-surface-600 dark:text-surface-300" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"/></svg>
        </button>
        <div class="flex items-center gap-3">
          <h2 class="text-xl font-bold text-surface-900 dark:text-white">{{ monthNames[currentMonth] }} {{ currentYear }}</h2>
          <button @click="goToday" class="text-xs px-2.5 py-1 rounded-lg bg-primary-50 dark:bg-primary-500/10 text-primary-600 dark:text-primary-400 font-medium hover:bg-primary-100 dark:hover:bg-primary-500/20 transition-colors">Today</button>
        </div>
        <button @click="nextMonth" class="p-2 rounded-lg hover:bg-surface-100 dark:hover:bg-surface-700 transition-colors">
          <svg class="w-5 h-5 text-surface-600 dark:text-surface-300" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/></svg>
        </button>
      </div>

      <!-- Calendar Grid -->
      <div class="bg-white dark:bg-surface-800 rounded-xl border border-surface-200 dark:border-surface-700 overflow-hidden">
        <!-- Day Headers -->
        <div class="grid grid-cols-7 border-b border-surface-200 dark:border-surface-700">
          <div v-for="day in dayNames" :key="day" class="py-2.5 text-center text-xs font-semibold text-surface-500 dark:text-surface-400 uppercase">{{ day }}</div>
        </div>

        <!-- Calendar Days -->
        <div class="grid grid-cols-7">
          <div v-for="(day, idx) in calendarDays" :key="idx"
            class="min-h-[100px] border-b border-r border-surface-100 dark:border-surface-700/50 p-1.5 transition-colors"
            :class="{
              'bg-surface-50 dark:bg-surface-900/50': !day.isCurrentMonth,
              'bg-primary-50 dark:bg-primary-500/5': day.isCurrentMonth && isToday(`${day.year}-${String(day.month + 1).padStart(2, '0')}-${String(day.date).padStart(2, '0')}`),
            }"
          >
            <!-- Day Number -->
            <div class="flex items-center justify-between mb-1">
              <span class="text-xs font-medium" :class="{
                'text-surface-300 dark:text-surface-600': !day.isCurrentMonth,
                'text-primary-600 dark:text-primary-400 font-bold': day.isCurrentMonth && isToday(`${day.year}-${String(day.month + 1).padStart(2, '0')}-${String(day.date).padStart(2, '0')}`),
                'text-surface-700 dark:text-surface-300': day.isCurrentMonth && !isToday(`${day.year}-${String(day.month + 1).padStart(2, '0')}-${String(day.date).padStart(2, '0')}`),
              }">{{ day.date }}</span>
              <button v-if="day.isCurrentMonth" @click="openAddModal(`${day.year}-${String(day.month + 1).padStart(2, '0')}-${String(day.date).padStart(2, '0')}`)" class="w-5 h-5 rounded-full hover:bg-surface-200 dark:hover:bg-surface-600 flex items-center justify-center text-surface-400 hover:text-surface-600 transition-colors opacity-0 hover:opacity-100" style="font-size: 14px;">+</button>
            </div>

            <!-- Events on this day -->
            <div v-if="day.isCurrentMonth" class="space-y-0.5">
              <div
                v-for="ev in getEventsForDay(day.date).slice(0, 3)"
                :key="ev.id"
                class="truncate text-xs px-1.5 py-0.5 rounded cursor-pointer hover:opacity-80 transition-opacity font-medium"
                :style="{ backgroundColor: ev.color + '20', color: ev.color }"
                :class="{ 'line-through opacity-50': ev.status === 'completed' || ev.status === 'cancelled' }"
                @click="openDetail(ev)"
                :title="ev.title + (ev.amount ? ' — ' + fmtCur(ev.amount, ev.currency) : '')"
              >
                {{ ev.title }}
              </div>
              <div v-if="getEventsForDay(day.date).length > 3" class="text-xs text-surface-400 px-1.5 truncate">
                +{{ getEventsForDay(day.date).length - 3 }} more
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- ==================== LIST VIEW ==================== -->
    <div v-else>
      <!-- Upcoming Events -->
      <div v-if="filteredUpcoming.length > 0">
        <h3 class="text-sm font-semibold text-surface-700 dark:text-surface-300 mb-3">Upcoming Events ({{ filteredUpcoming.length }})</h3>
        <div class="space-y-2 mb-6">
          <div v-for="ev in filteredUpcoming" :key="ev.id"
            class="card-hover p-4 cursor-pointer flex items-center gap-4 animate-fade-in"
            @click="openDetail(ev)"
          >
            <div class="w-12 h-12 rounded-lg flex flex-col items-center justify-center shrink-0" :style="{ backgroundColor: ev.color + '15' }">
              <span class="text-xs text-surface-400 leading-none">{{ new Date(ev.eventDate).toLocaleDateString('en-US', { month: 'short' }) }}</span>
              <span class="text-lg font-bold leading-tight" :style="{ color: ev.color }">{{ new Date(ev.eventDate).getDate() }}</span>
            </div>
            <div class="flex-1 min-w-0">
              <div class="flex items-center gap-2 mb-0.5">
                <h4 class="font-semibold text-surface-900 dark:text-white text-sm truncate">{{ ev.title }}</h4>
                <span v-if="ev.recurrence !== 'none'" class="text-xs px-1.5 py-0.5 rounded bg-surface-100 dark:bg-surface-700 text-surface-500 shrink-0">🔄 {{ recurrenceLabels[ev.recurrence] }}</span>
                <Badge :variant="priorityConfig[ev.priority]?.variant || 'neutral'" class="text-xs shrink-0">{{ priorityConfig[ev.priority]?.label }}</Badge>
              </div>
              <div class="flex items-center gap-3 text-xs text-surface-400">
                <span>{{ categoryConfig[ev.category]?.icon }} {{ categoryConfig[ev.category]?.label }}</span>
                <span v-if="ev.amount" class="font-medium" :class="isIncomeCategory(ev.category) ? 'text-green-600 dark:text-green-400' : 'text-surface-700 dark:text-surface-300'">
                  {{ isIncomeCategory(ev.category) ? '+' : '-' }}{{ fmtCur(ev.amount, ev.currency) }}
                </span>
                <span v-if="daysUntil(ev.eventDate) <= 7 && daysUntil(ev.eventDate) >= 0" class="font-medium" :class="daysUntil(ev.eventDate) === 0 ? 'text-danger-500' : 'text-warning-500'">
                  {{ daysUntil(ev.eventDate) === 0 ? 'Today' : daysUntil(ev.eventDate) + 'd left' }}
                </span>
                <span v-else>{{ daysUntil(ev.eventDate) }} days away</span>
              </div>
            </div>
            <button @click.stop="handleComplete(ev.id)" class="p-1.5 rounded-lg hover:bg-green-50 dark:hover:bg-green-500/10 text-green-500 transition-colors shrink-0" title="Mark complete">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/></svg>
            </button>
          </div>
        </div>
      </div>

      <!-- Overdue Events -->
      <div v-if="filteredOverdue.length > 0">
        <h3 class="text-sm font-semibold text-danger-600 dark:text-danger-400 mb-3">Overdue Events ({{ filteredOverdue.length }})</h3>
        <div class="space-y-2 mb-6">
          <div v-for="ev in filteredOverdue" :key="ev.id"
            class="p-4 border border-danger-200 dark:border-danger-500/30 bg-danger-50 dark:bg-danger-500/5 rounded-xl cursor-pointer flex items-center gap-4 animate-fade-in"
            @click="openDetail(ev)"
          >
            <div class="w-12 h-12 rounded-lg flex flex-col items-center justify-center shrink-0 bg-danger-100 dark:bg-danger-500/20">
              <span class="text-xs text-danger-400 leading-none">{{ new Date(ev.eventDate).toLocaleDateString('en-US', { month: 'short' }) }}</span>
              <span class="text-lg font-bold leading-tight text-danger-600 dark:text-danger-400">{{ new Date(ev.eventDate).getDate() }}</span>
            </div>
            <div class="flex-1 min-w-0">
              <div class="flex items-center gap-2 mb-0.5">
                <h4 class="font-semibold text-danger-700 dark:text-danger-300 text-sm truncate">{{ ev.title }}</h4>
                <Badge variant="danger" class="text-xs shrink-0">{{ Math.abs(daysUntil(ev.eventDate)) }}d overdue</Badge>
              </div>
              <div class="flex items-center gap-3 text-xs text-danger-500/70">
                <span>{{ categoryConfig[ev.category]?.icon }} {{ categoryConfig[ev.category]?.label }}</span>
                <span v-if="ev.amount" class="font-medium text-danger-600 dark:text-danger-400">{{ fmtCur(ev.amount, ev.currency) }}</span>
              </div>
            </div>
            <button @click.stop="handleComplete(ev.id)" class="p-1.5 rounded-lg hover:bg-green-50 dark:hover:bg-green-500/10 text-green-500 transition-colors shrink-0" title="Mark complete">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/></svg>
            </button>
          </div>
        </div>
      </div>

      <!-- Completed Events -->
      <div v-if="activeTab === 'all' && store.completedEvents.length > 0">
        <h3 class="text-sm font-semibold text-surface-500 dark:text-surface-400 mb-3">Completed ({{ store.completedEvents.length }})</h3>
        <div class="space-y-2">
          <div v-for="ev in store.completedEvents.slice(0, 5)" :key="ev.id"
            class="p-4 rounded-xl opacity-50 cursor-pointer flex items-center gap-4"
            @click="openDetail(ev)"
          >
            <div class="w-12 h-12 rounded-lg flex flex-col items-center justify-center shrink-0 bg-surface-100 dark:bg-surface-700">
              <span class="text-xs text-surface-400 leading-none">{{ new Date(ev.eventDate).toLocaleDateString('en-US', { month: 'short' }) }}</span>
              <span class="text-lg font-bold leading-tight text-surface-400">{{ new Date(ev.eventDate).getDate() }}</span>
            </div>
            <div class="flex-1 min-w-0">
              <h4 class="font-medium text-surface-500 dark:text-surface-400 text-sm truncate line-through">{{ ev.title }}</h4>
              <span class="text-xs text-surface-400">{{ categoryConfig[ev.category]?.icon }} {{ categoryConfig[ev.category]?.label }}</span>
            </div>
            <svg class="w-4 h-4 text-green-500 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/></svg>
          </div>
        </div>
      </div>

      <!-- Empty State -->
      <div v-if="filteredUpcoming.length === 0 && filteredOverdue.length === 0">
        <EmptyState icon="📅" title="No events found" description="Add your first financial event or change the filter.">
          <template #action>
            <button class="btn-primary" @click="openAddModal()">Add Event</button>
          </template>
        </EmptyState>
      </div>
    </div>

    <!-- ======================== DETAIL MODAL ======================== -->
    <Modal v-if="selectedEvent" :is-open="showDetailModal" title="Event Details" size="lg" @close="showDetailModal = false">
      <div class="space-y-5" v-if="selectedEvent">
        <!-- Header -->
        <div class="flex items-center gap-4 pb-4 border-b border-surface-200 dark:border-surface-700">
          <div class="w-14 h-14 rounded-xl flex items-center justify-center text-2xl" :style="{ backgroundColor: selectedEvent.color + '20' }">
            {{ categoryConfig[selectedEvent.category]?.icon }}
          </div>
          <div class="flex-1">
            <h3 class="text-lg font-bold text-surface-900 dark:text-white">{{ selectedEvent.title }}</h3>
            <p class="text-sm text-surface-500">
              {{ categoryConfig[selectedEvent.category]?.label }}
              <span class="mx-1">&middot;</span>
              <span :class="priorityConfig[selectedEvent.priority]?.color">{{ priorityConfig[selectedEvent.priority]?.label }}</span>
            </p>
          </div>
          <Badge :variant="statusConfig[selectedEvent.status]?.variant || 'neutral'">
            {{ statusConfig[selectedEvent.status]?.label }}
          </Badge>
        </div>

        <!-- Key Info -->
        <div class="grid grid-cols-2 md:grid-cols-3 gap-3">
          <div class="bg-surface-50 dark:bg-surface-700/50 rounded-lg p-3">
            <p class="text-xs text-surface-400 mb-1">Event Date</p>
            <p class="font-semibold text-surface-900 dark:text-white">{{ formatDate(selectedEvent.eventDate, 'long') }}</p>
            <p v-if="isToday(selectedEvent.eventDate)" class="text-xs text-primary-500 font-medium mt-0.5">Today!</p>
          </div>
          <div v-if="selectedEvent.amount" class="bg-surface-50 dark:bg-surface-700/50 rounded-lg p-3">
            <p class="text-xs text-surface-400 mb-1">Amount</p>
            <p class="font-semibold text-sm" :class="isIncomeCategory(selectedEvent.category) ? 'text-green-600' : 'text-surface-900 dark:text-white'">
              {{ fmtCur(selectedEvent.amount, selectedEvent.currency) }}
            </p>
          </div>
          <div class="bg-surface-50 dark:bg-surface-700/50 rounded-lg p-3">
            <p class="text-xs text-surface-400 mb-1">Recurrence</p>
            <p class="font-semibold text-surface-900 dark:text-white text-sm">{{ recurrenceLabels[selectedEvent.recurrence] }}</p>
            <p v-if="selectedEvent.recurrenceDayOfMonth" class="text-xs text-surface-400">Day {{ selectedEvent.recurrenceDayOfMonth }} of month</p>
          </div>
          <div v-if="selectedEvent.endDate" class="bg-surface-50 dark:bg-surface-700/50 rounded-lg p-3">
            <p class="text-xs text-surface-400 mb-1">End Date</p>
            <p class="font-semibold text-surface-900 dark:text-white text-sm">{{ formatDate(selectedEvent.endDate, 'long') }}</p>
          </div>
          <div class="bg-surface-50 dark:bg-surface-700/50 rounded-lg p-3">
            <p class="text-xs text-surface-400 mb-1">Reminder</p>
            <p class="font-semibold text-surface-900 dark:text-white text-sm">{{ selectedEvent.reminderEnabled ? selectedEvent.reminderDaysBefore + ' days before' : 'Disabled' }}</p>
            <p v-if="selectedEvent.secondReminderDaysBefore" class="text-xs text-surface-400">Also {{ selectedEvent.secondReminderDaysBefore }}d before</p>
          </div>
          <div v-if="selectedEvent.linkedEntityId" class="bg-surface-50 dark:bg-surface-700/50 rounded-lg p-3">
            <p class="text-xs text-surface-400 mb-1">Linked To</p>
            <p class="font-semibold text-surface-900 dark:text-white text-sm">🔗 {{ linkedEntityLabels[selectedEvent.linkedEntityType || 'other'] }}</p>
            <p class="text-xs text-surface-400 truncate">{{ selectedEvent.linkedEntityId }}</p>
          </div>
        </div>

        <!-- Description -->
        <div v-if="selectedEvent.description" class="bg-surface-50 dark:bg-surface-900 rounded-lg p-4">
          <p class="text-sm text-surface-600 dark:text-surface-400">{{ selectedEvent.description }}</p>
        </div>

        <!-- Notes -->
        <div v-if="selectedEvent.notes">
          <h4 class="text-sm font-semibold text-surface-700 dark:text-surface-300 mb-1">Notes</h4>
          <p class="text-sm text-surface-600 dark:text-surface-400">{{ selectedEvent.notes }}</p>
        </div>

        <!-- Tags -->
        <div v-if="selectedEvent.tags && selectedEvent.tags.length > 0">
          <div class="flex flex-wrap gap-2">
            <span v-for="tag in selectedEvent.tags" :key="tag" class="text-sm px-2.5 py-1 rounded-lg bg-primary-50 dark:bg-primary-500/10 text-primary-600 dark:text-primary-400">{{ tag }}</span>
          </div>
        </div>

        <!-- Actions -->
        <div class="flex flex-wrap gap-3 pt-2 border-t border-surface-200 dark:border-surface-700">
          <button v-if="selectedEvent.status === 'upcoming'" class="btn-primary" @click="handleComplete(selectedEvent.id); showDetailModal = false;">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/></svg>
            Mark Complete
          </button>
          <button v-if="selectedEvent.status === 'completed' || selectedEvent.status === 'overdue'" class="btn-secondary" @click="handleRestore(selectedEvent.id); showDetailModal = false;">
            Restore
          </button>
          <button v-if="selectedEvent.status === 'upcoming'" class="btn-secondary" @click="handleCancel(selectedEvent.id); showDetailModal = false;">
            Cancel
          </button>
          <button class="btn-danger" @click="showDeleteConfirm = true">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/></svg>
            Delete
          </button>
        </div>
      </div>
    </Modal>

    <!-- ======================== ADD EVENT MODAL ======================== -->
    <Modal :is-open="showAddModal" title="Add Calendar Event" size="lg" @close="showAddModal = false">
      <div class="space-y-5">
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div class="md:col-span-2">
            <label class="field-label">Event Title *</label>
            <input v-model="addForm.title" type="text" class="input-field" placeholder="e.g., DBBL Home Loan EMI" />
          </div>
          <div>
            <label class="field-label">Category</label>
            <select v-model="addForm.category" class="input-field">
              <option value="emi_payment">💰 EMI Payment</option>
              <option value="insurance_premium">🛡️ Insurance Premium</option>
              <option value="bill_payment">📄 Bill Payment</option>
              <option value="investment_maturity">🎯 Investment Maturity</option>
              <option value="investment_deposit">🏦 Investment Deposit</option>
              <option value="dividend">📈 Dividend / Interest</option>
              <option value="tax_deadline">🧾 Tax Deadline</option>
              <option value="salary">💵 Salary</option>
              <option value="rental_income">🏠 Rental Income</option>
              <option value="rental_payment">🏠 Rental Payment</option>
              <option value="lending_payment">🤝 Lending Payment</option>
              <option value="subscription">📺 Subscription</option>
              <option value="maintenance">🔧 Maintenance</option>
              <option value="document_renewal">📝 Document Renewal</option>
              <option value="milestone">⭐ Milestone</option>
              <option value="other">📎 Other</option>
            </select>
          </div>
          <div>
            <label class="field-label">Priority</label>
            <select v-model="addForm.priority" class="input-field">
              <option value="high">🔴 High</option>
              <option value="medium">🟡 Medium</option>
              <option value="low">⚪ Low</option>
            </select>
          </div>
          <div>
            <label class="field-label">Amount (BDT)</label>
            <input v-model.number="addForm.amount" type="number" class="input-field" placeholder="0" min="0" />
          </div>
          <div>
            <label class="field-label">Event Date *</label>
            <input v-model="addForm.eventDate" type="date" class="input-field" />
          </div>
          <div>
            <label class="field-label">Recurrence</label>
            <select v-model="addForm.recurrence" class="input-field">
              <option value="none">One-time</option>
              <option value="monthly">Monthly</option>
              <option value="quarterly">Quarterly</option>
              <option value="semiannually">Semi-annually</option>
              <option value="annually">Annually</option>
              <option value="weekly">Weekly</option>
              <option value="biweekly">Bi-weekly</option>
            </select>
          </div>
          <div v-if="addForm.recurrence !== 'none'">
            <label class="field-label">Day of Month</label>
            <input v-model.number="addForm.recurrenceDayOfMonth" type="number" class="input-field" min="1" max="31" placeholder="1" />
          </div>
          <div v-if="addForm.recurrence !== 'none'">
            <label class="field-label">End Date (optional)</label>
            <input v-model="addForm.endDate" type="date" class="input-field" />
          </div>
          <div>
            <label class="field-label">Reminder (days before)</label>
            <input v-model.number="addForm.reminderDaysBefore" type="number" class="input-field" min="0" />
          </div>
        </div>
        <div>
          <label class="field-label">Description</label>
          <textarea v-model="addForm.description" class="input-field" rows="2" placeholder="Brief description..."></textarea>
        </div>
        <div>
          <label class="field-label">Notes</label>
          <textarea v-model="addForm.notes" class="input-field" rows="2" placeholder="Additional notes..."></textarea>
        </div>
        <div class="flex justify-end gap-3 pt-2 border-t border-surface-200 dark:border-surface-700">
          <button class="btn-secondary" @click="showAddModal = false">Cancel</button>
          <button class="btn-primary" @click="submitAddEvent" :disabled="!addForm.title">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/></svg>
            Add Event
          </button>
        </div>
      </div>
    </Modal>

    <!-- ======================== DELETE CONFIRM ======================== -->
    <Modal :is-open="showDeleteConfirm" title="Delete Event" size="sm" @close="showDeleteConfirm = false">
      <div class="space-y-4">
        <div class="flex items-center gap-3 p-4 bg-danger-50 dark:bg-danger-500/10 rounded-lg">
          <svg class="w-6 h-6 text-danger-500 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z"/></svg>
          <p class="text-sm text-danger-700 dark:text-danger-300">
            Are you sure you want to delete <strong>"{{ selectedEvent?.title }}"</strong>?
          </p>
        </div>
        <div class="flex justify-end gap-3">
          <button class="btn-secondary" @click="showDeleteConfirm = false">Cancel</button>
          <button class="btn-danger" @click="confirmDelete">Delete</button>
        </div>
      </div>
    </Modal>
  </div>
</template>
