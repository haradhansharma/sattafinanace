/**
 * FinLife InvoiceService
 * =====================
 * Invoice-specific service that wraps the centralized DataService.
 * Provides typed methods for full CRUD, status transitions, filtering,
 * and aggregate statistics.
 *
 * Components and stores should import `invoiceService` from here
 * rather than calling `dataService.getInvoices()` directly, so that
 * business logic (stats computation, status guards, etc.) stays
 * encapsulated.
 */

import { dataService } from './data-service';
import type {
  Invoice,
  InvoiceItem,
  InvoiceStatus,
  InvoiceFilter,
  Currency,
} from '../types';

// ==================== Helpers ====================

const delay = (ms: number): Promise<void> =>
  new Promise(resolve => setTimeout(resolve, ms));

/** Mutable in-memory store for mock write operations. */
let localInvoices: Invoice[] = [];

/** Lazy-initialise the local copy from the DataService once. */
async function ensureLoaded(): Promise<Invoice[]> {
  if (localInvoices.length === 0) {
    localInvoices = await dataService.getInvoices();
  }
  return localInvoices;
}

function generateInvoiceNumber(): string {
  const now = new Date();
  const y = now.getFullYear();
  const seq = String(localInvoices.length + 1).padStart(3, '0');
  return `INV-${y}-${seq}`;
}

function generateItemId(): string {
  return `ii_${Date.now()}_${Math.random().toString(36).slice(2, 6)}`;
}

// ==================== Stats Types ====================

export interface InvoiceStats {
  totalCount: number;
  paidCount: number;
  sentCount: number;
  draftCount: number;
  viewedCount: number;
  overdueCount: number;
  cancelledCount: number;
  totalAmount: number;
  paidAmount: number;
  pendingAmount: number;     // sent + viewed + draft (still expected)
  overdueAmount: number;
}

// ==================== InvoiceService ====================

export const invoiceService = {
  // ==================== CRUD ====================

  /** Get all invoices, sorted by issue date (newest first). */
  async getInvoices(): Promise<Invoice[]> {
    await delay(50);
    const invoices = await ensureLoaded();
    return [...invoices].sort(
      (a, b) => new Date(b.issueDate).getTime() - new Date(a.issueDate).getTime(),
    );
  },

  /** Get a single invoice by id. */
  async getInvoiceById(id: string): Promise<Invoice | null> {
    await delay(30);
    const invoices = await ensureLoaded();
    return invoices.find(inv => inv.id === id) ?? null;
  },

  /**
   * Create a new invoice.
   * Automatically computes subtotal, tax, and total from line items.
   */
  async createInvoice(
    data: Omit<Invoice, 'id' | 'createdAt' | 'updatedAt' | 'invoiceNumber' | 'subtotal' | 'taxAmount' | 'totalAmount'>,
  ): Promise<Invoice> {
    await delay(50);
    const invoices = await ensureLoaded();
    const now = new Date().toISOString();

    const subtotal = data.items.reduce((sum, item) => sum + item.total, 0);
    const taxAmount = Math.round(subtotal * (data.taxRate / 100));
    const totalAmount = subtotal + taxAmount - data.discountAmount;

    const newInvoice: Invoice = {
      ...data,
      id: `inv_${Date.now()}`,
      invoiceNumber: generateInvoiceNumber(),
      subtotal,
      taxAmount,
      totalAmount,
      createdAt: now,
      updatedAt: now,
    };

    invoices.unshift(newInvoice);
    localInvoices = invoices;
    return { ...newInvoice };
  },

  /**
   * Update an existing invoice.
   * Accepts partial fields; subtotal/tax/total are recomputed if items or rates change.
   */
  async updateInvoice(
    id: string,
    data: Partial<Omit<Invoice, 'id' | 'createdAt'>>,
  ): Promise<Invoice> {
    await delay(50);
    const invoices = await ensureLoaded();
    const idx = invoices.findIndex(inv => inv.id === id);
    if (idx === -1) throw new Error(`Invoice "${id}" not found`);

    const existing = invoices[idx];
    const merged = { ...existing, ...data, updatedAt: new Date().toISOString() };

    // Recompute derived money fields when relevant inputs change
    if (data.items !== undefined || data.taxRate !== undefined || data.discountAmount !== undefined) {
      const items = data.items ?? existing.items;
      const taxRate = data.taxRate !== undefined ? data.taxRate : existing.taxRate;
      const discountAmount = data.discountAmount !== undefined ? data.discountAmount : existing.discountAmount;
      merged.subtotal = items.reduce((sum, item) => sum + item.total, 0);
      merged.taxAmount = Math.round(merged.subtotal * (taxRate / 100));
      merged.totalAmount = merged.subtotal + merged.taxAmount - discountAmount;
    }

    invoices[idx] = merged;
    localInvoices = invoices;
    return { ...merged };
  },

  /** Delete an invoice by id. */
  async deleteInvoice(id: string): Promise<void> {
    await delay(50);
    const invoices = await ensureLoaded();
    const idx = invoices.findIndex(inv => inv.id === id);
    if (idx === -1) throw new Error(`Invoice "${id}" not found`);
    invoices.splice(idx, 1);
    localInvoices = invoices;
  },

  // ==================== Status Transitions ====================

  /**
   * Transition an invoice to a new status.
   * Enforces basic guards (e.g. paid/cancelled invoices cannot be re-opened).
   */
  async updateInvoiceStatus(id: string, newStatus: InvoiceStatus): Promise<Invoice> {
    await delay(50);
    const invoices = await ensureLoaded();
    const invoice = invoices.find(inv => inv.id === id);
    if (!invoice) throw new Error(`Invoice "${id}" not found`);

    const disallowed: Record<InvoiceStatus, InvoiceStatus[]> = {
      paid: ['cancelled'],
      cancelled: ['paid', 'sent', 'viewed'],
      draft: ['overdue'],
      sent: ['overdue'],
      viewed: ['overdue'],
      overdue: ['draft'],
    };

    const blocked = disallowed[invoice.status] ?? [];
    if (blocked.includes(newStatus)) {
      throw new Error(
        `Cannot transition invoice "${id}" from "${invoice.status}" to "${newStatus}".`,
      );
    }

    const now = new Date().toISOString();
    const updated: Invoice = {
      ...invoice,
      status: newStatus,
      updatedAt: now,
      paidDate: newStatus === 'paid' ? now : invoice.paidDate,
    };

    const idx = invoices.findIndex(inv => inv.id === id);
    invoices[idx] = updated;
    localInvoices = invoices;
    return { ...updated };
  },

  /** Mark an invoice as cancelled. */
  async cancelInvoice(id: string): Promise<Invoice> {
    return this.updateInvoiceStatus(id, 'cancelled');
  },

  /**
   * "Send" a draft invoice — transitions it to 'sent'.
   * Returns the updated invoice.
   */
  async sendInvoice(id: string): Promise<Invoice> {
    return this.updateInvoiceStatus(id, 'sent');
  },

  // ==================== Filtering & Query ====================

  /**
   * Get invoices matching an optional filter.
   * Supported filter fields: status, startDate, endDate, clientId (mapped to clientName),
   * search (matched against invoiceNumber, clientName, notes).
   */
  async getFilteredInvoices(filter: InvoiceFilter = {}): Promise<Invoice[]> {
    await delay(50);
    let invoices = await ensureLoaded();

    // Sort newest first
    invoices = [...invoices].sort(
      (a, b) => new Date(b.issueDate).getTime() - new Date(a.issueDate).getTime(),
    );

    if (filter.status) {
      const statuses = Array.isArray(filter.status) ? filter.status : [filter.status];
      invoices = invoices.filter(inv => statuses.includes(inv.status));
    }

    if (filter.startDate) {
      const start = new Date(filter.startDate);
      invoices = invoices.filter(inv => new Date(inv.issueDate) >= start);
    }

    if (filter.endDate) {
      const end = new Date(filter.endDate);
      invoices = invoices.filter(inv => new Date(inv.issueDate) <= end);
    }

    if (filter.search) {
      const q = filter.search.toLowerCase();
      invoices = invoices.filter(
        inv =>
          inv.invoiceNumber.toLowerCase().includes(q) ||
          inv.clientName.toLowerCase().includes(q) ||
          (inv.notes?.toLowerCase().includes(q) ?? false),
      );
    }

    return invoices;
  },

  // ==================== Statistics ====================

  /**
   * Compute aggregate stats across all invoices.
   * Categorises amounts by status for dashboard widgets.
   */
  async getInvoiceStats(): Promise<InvoiceStats> {
    await delay(50);
    const invoices = await ensureLoaded();

    const stats: InvoiceStats = {
      totalCount: invoices.length,
      paidCount: 0,
      sentCount: 0,
      draftCount: 0,
      viewedCount: 0,
      overdueCount: 0,
      cancelledCount: 0,
      totalAmount: 0,
      paidAmount: 0,
      pendingAmount: 0,
      overdueAmount: 0,
    };

    for (const inv of invoices) {
      stats.totalAmount += inv.totalAmount;

      switch (inv.status) {
        case 'paid':
          stats.paidCount++;
          stats.paidAmount += inv.totalAmount;
          break;
        case 'sent':
          stats.sentCount++;
          stats.pendingAmount += inv.totalAmount;
          break;
        case 'draft':
          stats.draftCount++;
          stats.pendingAmount += inv.totalAmount;
          break;
        case 'viewed':
          stats.viewedCount++;
          stats.pendingAmount += inv.totalAmount;
          break;
        case 'overdue':
          stats.overdueCount++;
          stats.overdueAmount += inv.totalAmount;
          break;
        case 'cancelled':
          stats.cancelledCount++;
          break;
      }
    }

    return stats;
  },
};
