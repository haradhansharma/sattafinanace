import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import type { CalendarEvent, CalendarEventCategory } from '../types';
import { api, fetchAllPages } from '../services/api-bridge';
import { ApiError } from '../services/api-bridge';

export const useCalendarStore = defineStore('calendar', () => {
  // ==================== State ====================
  const events = ref<CalendarEvent[]>([]);
  const loading = ref(false);
  const error = ref<string | null>(null);

  // ==================== Fetchers ====================

  async function fetchEvents(params?: {
    category?: string;
    status?: string;
    priority?: string;
  }): Promise<void> {
    loading.value = true;
    error.value = null;
    try {
      events.value = await fetchAllPages<CalendarEvent>('/calendar/', { params });
    } catch (err) {
      error.value = err instanceof ApiError ? err.message : 'Failed to fetch events';
      throw err;
    } finally {
      loading.value = false;
    }
  }

  async function fetchEventById(id: string): Promise<CalendarEvent> {
    loading.value = true;
    error.value = null;
    try {
      const event = await api.get<CalendarEvent>(`/calendar/${id}/`);
      const index = events.value.findIndex(e => e.id === id);
      if (index !== -1) {
        events.value[index] = event;
      } else {
        events.value.push(event);
      }
      return event;
    } catch (err) {
      error.value = err instanceof ApiError ? err.message : 'Failed to fetch event';
      throw err;
    } finally {
      loading.value = false;
    }
  }

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

  const eventsThisMonth = computed(() => {
    const now = new Date();
    const year = now.getFullYear();
    const month = now.getMonth();
    return events.value.filter(e => {
      const d = new Date(e.eventDate);
      return d.getFullYear() === year && d.getMonth() === month;
    });
  });

  // ==================== CRUD ====================

  async function addEvent(data: Omit<CalendarEvent, 'id' | 'createdAt' | 'updatedAt'>): Promise<CalendarEvent> {
    error.value = null;
    try {
      const event = await api.post<CalendarEvent>('/calendar/', data);
      events.value.push(event);
      return event;
    } catch (err) {
      error.value = err instanceof ApiError ? err.message : 'Failed to create event';
      throw err;
    }
  }

  async function updateCalendarEvent(id: string, data: Partial<CalendarEvent>): Promise<CalendarEvent | null> {
    error.value = null;
    try {
      const updated = await api.put<CalendarEvent>(`/calendar/${id}/`, data);
      const index = events.value.findIndex(e => e.id === id);
      if (index !== -1) {
        events.value[index] = updated;
      }
      return updated;
    } catch (err) {
      error.value = err instanceof ApiError ? err.message : 'Failed to update event';
      throw err;
    }
  }

  async function deleteEvent(id: string): Promise<void> {
    error.value = null;
    try {
      await api.delete(`/calendar/${id}/`);
      const index = events.value.findIndex(e => e.id === id);
      if (index !== -1) {
        events.value.splice(index, 1);
      }
    } catch (err) {
      error.value = err instanceof ApiError ? err.message : 'Failed to delete event';
      throw err;
    }
  }

  // ==================== Status Helpers ====================

  async function completeEvent(id: string): Promise<CalendarEvent | null> {
    return updateCalendarEvent(id, { status: 'completed' });
  }

  async function cancelEvent(id: string): Promise<CalendarEvent | null> {
    return updateCalendarEvent(id, { status: 'cancelled' });
  }

  async function markAsUpcoming(id: string): Promise<CalendarEvent | null> {
    return updateCalendarEvent(id, { status: 'upcoming' });
  }

  // ==================== Local Filters ====================

  function getEventsForMonth(year: number, month: number): CalendarEvent[] {
    return events.value.filter(e => {
      const d = new Date(e.eventDate);
      return d.getFullYear() === year && d.getMonth() === month;
    });
  }

  function getEventsForDate(dateStr: string): CalendarEvent[] {
    const target = new Date(dateStr);
    target.setHours(0, 0, 0, 0);
    return events.value.filter(e => {
      const d = new Date(e.eventDate);
      d.setHours(0, 0, 0, 0);
      return d.getTime() === target.getTime();
    });
  }

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

  // ==================== Helpers ====================

  function getEventById(id: string): CalendarEvent | undefined {
    return events.value.find(e => e.id === id);
  }

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

  function getByCategory(category: CalendarEventCategory): CalendarEvent[] {
    return events.value.filter(e => e.category === category);
  }

  function clearError() {
    error.value = null;
  }

  return {
    // State
    events,
    loading,
    error,
    // Fetchers
    fetchEvents,
    fetchEventById,
    // Computed
    totalEvents,
    recurringEvents,
    upcomingEvents,
    overdueEvents,
    completedEvents,
    eventsThisMonth,
    // CRUD
    addEvent,
    updateCalendarEvent,
    deleteEvent,
    // Status helpers
    completeEvent,
    cancelEvent,
    markAsUpcoming,
    // Local filters
    getEventsForMonth,
    getEventsForDate,
    getEventsWithinDays,
    // Helpers
    getEventById,
    searchEvents,
    getByCategory,
    clearError,
  };
});
