from datetime import date
from typing import List, Optional

from ninja import Schema


# ==================== Message ====================


class MessageOut(Schema):
    """Generic message response."""

    message: str


# ==================== InvoiceItem Schemas ====================


class InvoiceItemOut(Schema):
    """Invoice line item response matching frontend InvoiceItem type."""

    id: str
    description: str
    quantity: int
    unitPrice: int
    total: int

    @staticmethod
    def resolve_id(obj):
        return str(obj.id)

    @staticmethod
    def resolve_unitPrice(obj):
        return obj.unit_price


class InvoiceItemCreate(Schema):
    """Create an invoice line item."""

    description: str
    quantity: int
    unitPrice: int
    total: int


# ==================== Invoice Schemas ====================


class InvoiceOut(Schema):
    """Full invoice response matching frontend Invoice type."""

    id: str
    invoiceNumber: str
    type: str
    clientName: str
    clientEmail: Optional[str] = None
    clientPhone: Optional[str] = None
    clientAddress: Optional[str] = None
    items: List[InvoiceItemOut] = []
    subtotal: int
    taxRate: float
    taxAmount: int
    discountAmount: int
    totalAmount: int
    currency: str = "BDT"
    status: str
    issueDate: str
    dueDate: str
    paidDate: Optional[str] = None
    notes: Optional[str] = None
    bankAccountId: Optional[str] = None
    tags: List[str] = []
    createdAt: str
    updatedAt: str

    @staticmethod
    def resolve_id(obj):
        return str(obj.id)

    @staticmethod
    def resolve_invoiceNumber(obj):
        return obj.invoice_number

    @staticmethod
    def resolve_clientName(obj):
        return obj.client_name

    @staticmethod
    def resolve_clientEmail(obj):
        return obj.client_email or None

    @staticmethod
    def resolve_clientPhone(obj):
        return obj.client_phone or None

    @staticmethod
    def resolve_clientAddress(obj):
        return obj.client_address or None

    @staticmethod
    def resolve_taxRate(obj):
        return float(obj.tax_rate)

    @staticmethod
    def resolve_issueDate(obj):
        return obj.issue_date.isoformat()

    @staticmethod
    def resolve_dueDate(obj):
        return obj.due_date.isoformat()

    @staticmethod
    def resolve_paidDate(obj):
        return obj.paid_date.isoformat() if obj.paid_date else None

    @staticmethod
    def resolve_notes(obj):
        return obj.notes or None

    @staticmethod
    def resolve_bankAccountId(obj):
        return str(obj.bank_account_id) if obj.bank_account_id else None

    @staticmethod
    def resolve_createdAt(obj):
        return obj.created_at.isoformat()

    @staticmethod
    def resolve_updatedAt(obj):
        return obj.updated_at.isoformat()


class InvoiceCreate(Schema):
    """Create a new invoice."""

    type: str
    clientName: str
    clientEmail: Optional[str] = None
    clientPhone: Optional[str] = None
    clientAddress: Optional[str] = None
    subtotal: int = 0
    taxRate: float = 0.0
    taxAmount: int = 0
    discountAmount: int = 0
    totalAmount: int = 0
    currency: str = "BDT"
    issueDate: date
    dueDate: date
    notes: Optional[str] = None
    bankAccountId: Optional[str] = None
    tags: Optional[List[str]] = None
    items: Optional[List[InvoiceItemCreate]] = None


class InvoiceUpdate(Schema):
    """Update an invoice — all fields optional."""

    type: Optional[str] = None
    clientName: Optional[str] = None
    clientEmail: Optional[str] = None
    clientPhone: Optional[str] = None
    clientAddress: Optional[str] = None
    subtotal: Optional[int] = None
    taxRate: Optional[float] = None
    taxAmount: Optional[int] = None
    discountAmount: Optional[int] = None
    totalAmount: Optional[int] = None
    currency: Optional[str] = None
    status: Optional[str] = None
    issueDate: Optional[date] = None
    dueDate: Optional[date] = None
    paidDate: Optional[date] = None
    notes: Optional[str] = None
    bankAccountId: Optional[str] = None
    tags: Optional[List[str]] = None
    items: Optional[List[InvoiceItemCreate]] = None


class NextInvoiceNumberOut(Schema):
    """Preview of the next auto-generated invoice number."""

    nextInvoiceNumber: str
