import '../lib/pinia-init';
import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import type { CalendarEvent, CalendarEventCategory, CalendarEventStatus, RecurrencePattern } from '../types';
import { mockCalendarEvents } from '../mock-data';
import { generateId } from '../utils/formatters';

export const useCalendarStore = defineStore('calendar', () => {
  const events = ref<CalendarEvent[]>(mockCalendarEvents.map(e => ({
    ...e,
    tags: e.tags || [],
  })));

  // ==================== Computed ====================

  const totalEvents = computed(() => events.value.length);
  const recurringEvents = computed(() => events.value.filter(e => e.recurrence !== 'none'));

  const upcomingEvents = computed(() => {
    const now = new Date();
    now.setHours(0, 0, 0, 0);
    return events.value
      .filter(e => {
        const date = new Date(e.eventDate);
        date.setHours(0, 0, 0, 0);
        return date >= now && (e.status === 'upcoming' || e.status === 'overdue');
      })
      .sort((a, b) => new Date(a.eventDate).getTime() - new Date(b.eventDate).getTime());
  });

  const overdueEvents = computed(() => {
    const now = new Date();
    now.setHours(0, 0, 0, 0);
    return events.value
      .filter(e => {
        const date = new Date(e.eventDate);
        date.setHours(0, 0, 0, 0);
        return date < now && e.status !== 'completed' && e.status !== 'cancelled';
      })
      .sort((a, b) => new Date(a.eventDate).getTime() - new Date(b.eventDate).getTime());
  });

  const completedEvents = computed(() =>
    events.value.filter(e => e.status === 'completed')
  );

  // Events this month
  const eventsThisMonth = computed(() => {
    const now = new Date();
    const year = now.getFullYear();
    const month = now.getMonth();
    return events.value.filter(e => {
      const d = new Date(e.eventDate);
      return d.getFullYear() === year && d.getMonth() === month;
    });
  });

  // Events in a specific month (for calendar grid)
  function getEventsForMonth(year: number, month: number): CalendarEvent[] {
    return events.value.filter(e => {
      const d = new Date(e.eventDate);
      return d.getFullYear() === year && d.getMonth() === month;
    });
  }

  // Events on a specific date
  function getEventsForDate(dateStr: string): CalendarEvent[] {
    const target = new Date(dateStr);
    target.setHours(0, 0, 0, 0);
    return events.value.filter(e => {
      const d = new Date(e.eventDate);
      d.setHours(0, 0, 0, 0);
      return d.getTime() === target.getTime();
    });
  }

  // Events upcoming within N days
  function getEventsWithinDays(days: number): CalendarEvent[] {
    const now = new Date();
    now.setHours(0, 0, 0, 0);
    const future = new Date(now.getTime() + days * 24 * 60 * 60 * 1000);
    return events.value
      .filter(e => {
        const d = new Date(e.eventDate);
        d.setHours(0, 0, 0, 0);
        return d >= now && d <= future && e.status !== 'completed' && e.status !== 'cancelled';
      })
      .sort((a, b) => new Date(a.eventDate).getTime() - new Date(b.eventDate).getTime());
  }

  // Reminders due (events within reminder window)
  const activeReminders = computed(() => {
    const now = new Date();
    now.setHours(0, 0, 0, 0);
    return events.value.filter(e => {
      if (!e.reminderEnabled || e.status === 'completed' || e.status === 'cancelled') return false;
      const eventDate = new Date(e.eventDate);
      eventDate.setHours(0, 0, 0, 0);
      const reminderDate = new Date(eventDate.getTime() - (e.reminderDaysBefore) * 24 * 60 * 60 * 1000);
      return reminderDate <= now && eventDate >= now;
    });
  });

  // Category breakdown
  const eventsByCategory = computed(() => {
    const map: Record<string, CalendarEvent[]> = {};
    events.value.forEach(e => {
      if (!map[e.category]) map[e.category] = [];
      map[e.category].push(e);
    });
    return map;
  });

  const categoryCounts = computed(() => {
    const map = {} as Record<string, number>;
    events.value.forEach(e => {
      map[e.category] = (map[e.category] || 0) + 1;
    });
    return map;
  });

  // Total outflow this month (bills, EMI, insurance, etc.)
  const outflowThisMonth = computed(() => {
    return eventsThisMonth.value
      .filter(e => {
        const incomeCategories = ['salary', 'rental_income', 'dividend'];
        return !incomeCategories.includes(e.category) && e.amount && e.status !== 'cancelled';
      })
      .reduce((sum, e) => sum + (e.amount || 0), 0);
  });

  // Total inflow this month
  const inflowThisMonth = computed(() => {
    return eventsThisMonth.value
      .filter(e => {
        const incomeCategories = ['salary', 'rental_income', 'dividend'];
        return incomeCategories.includes(e.category) && e.amount && e.status !== 'cancelled';
      })
      .reduce((sum, e) => sum + (e.amount || 0), 0);
  });

  // High priority upcoming
  const highPriorityUpcoming = computed(() =>
    upcomingEvents.value.filter(e => e.priority === 'high')
  );

  // Search
  function searchEvents(query: string): CalendarEvent[] {
    const q = query.toLowerCase().trim();
    if (!q) return events.value;
    return events.value.filter(e =>
      e.title.toLowerCase().includes(q) ||
      e.description?.toLowerCase().includes(q) ||
      e.tags?.some(t => t.toLowerCase().includes(q)) ||
      e.notes?.toLowerCase().includes(q)
    );
  }

  // Filter by category
  function getByCategory(category: CalendarEventCategory): CalendarEvent[] {
    return events.value.filter(e => e.category === category);
  }

  // ==================== CRUD ====================

  function addEvent(data: Omit<CalendarEvent, 'id' | 'createdAt' | 'updatedAt'>) {
    const now = new Date().toISOString();
    const event: CalendarEvent = {
      ...data,
      tags: data.tags || [],
      id: generateId('cal'),
      createdAt: now,
      updatedAt: now,
    };
    events.value.push(event);
    return event;
  }

  function updateEvent(id: string, data: Partial<CalendarEvent>) {
    const index = events.value.findIndex(e => e.id === id);
    if (index === -1) return null;
    events.value[index] = {
      ...events.value[index],
      ...data,
      id: events.value[index].id,
      createdAt: events.value[index].createdAt,
      tags: data.tags ?? events.value[index].tags,
      updatedAt: new Date().toISOString(),
    };
    return events.value[index];
  }

  function deleteEvent(id: string) {
    const index = events.value.findIndex(e => e.id === id);
    if (index !== -1) events.value.splice(index, 1);
  }

  function completeEvent(id: string) {
    const ev = events.value.find(e => e.id === id);
    if (ev) {
      ev.status = 'completed';
      ev.updatedAt = new Date().toISOString();
    }
  }

  function cancelEvent(id: string) {
    const ev = events.value.find(e => e.id === id);
    if (ev) {
      ev.status = 'cancelled';
      ev.updatedAt = new Date().toISOString();
    }
  }

  function markAsUpcoming(id: string) {
    const ev = events.value.find(e => e.id === id);
    if (ev) {
      ev.status = 'upcoming';
      ev.updatedAt = new Date().toISOString();
    }
  }

  function getEventById(id: string): CalendarEvent | undefined {
    return events.value.find(e => e.id === id);
  }

  return {
    events,
    totalEvents,
    recurringEvents,
    upcomingEvents,
    overdueEvents,
    completedEvents,
    eventsThisMonth,
    activeReminders,
    eventsByCategory,
    categoryCounts,
    outflowThisMonth,
    inflowThisMonth,
    highPriorityUpcoming,
    getEventsForMonth,
    getEventsForDate,
    getEventsWithinDays,
    searchEvents,
    getByCategory,
    addEvent,
    updateEvent,
    deleteEvent,
    completeEvent,
    cancelEvent,
    markAsUpcoming,
    getEventById,
  };
});
