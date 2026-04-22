import uuid
from datetime import date
from typing import Optional

from django.db import transaction as db_transaction
from django.shortcuts import get_object_or_404
from ninja import Router, Query

from common.permissions import BearerAuth
from common.pagination import PaginatedResponse, PaginationSchema
from common.pagination import paginate_queryset

from .models import Invoice, InvoiceItem
from .schemas import (
    InvoiceOut,
    InvoiceCreate,
    InvoiceUpdate,
    InvoiceItemCreate,
    NextInvoiceNumberOut,
    MessageOut,
)

router = Router(tags=["Invoice"])
auth = BearerAuth()

# ==================== Field Mapping: camelCase → snake_case ====================

INVOICE_FIELD_MAP = {
    "clientName": "client_name",
    "clientEmail": "client_email",
    "clientPhone": "client_phone",
    "clientAddress": "client_address",
    "subtotal": "subtotal",
    "taxRate": "tax_rate",
    "taxAmount": "tax_amount",
    "discountAmount": "discount_amount",
    "totalAmount": "total_amount",
    "issueDate": "issue_date",
    "dueDate": "due_date",
    "paidDate": "paid_date",
    "bankAccountId": "bank_account_id",
}

DATE_FIELDS = {"issueDate", "dueDate", "paidDate"}


def _parse_date(d):
    """Parse a date from ISO string or date object."""
    if isinstance(d, date):
        return d
    return date.fromisoformat(d)


def _generate_invoice_number():
    """
    Auto-generate invoice number: INV-{year}-{sequential_number}.
    Sequential number resets per year, zero-padded to 3 digits.
    """
    year = date.today().year
    last = (
        Invoice.objects.filter(invoice_number__startswith=f"INV-{year}-")
        .order_by("-invoice_number")
        .first()
    )

    if last:
        try:
            num = int(last.invoice_number.split("-")[-1]) + 1
        except (ValueError, IndexError):
            num = 1
    else:
        num = 1

    return f"INV-{year}-{num:03d}"


def _map_invoice_payload(payload: dict) -> dict:
    """Convert camelCase invoice payload to snake_case model fields."""
    result = {}
    for key, value in payload.items():
        mapped = INVOICE_FIELD_MAP.get(key, key)
        if key in DATE_FIELDS and value is not None:
            result[mapped] = _parse_date(value)
        else:
            result[mapped] = value
    return result


# ==================== Invoice CRUD ====================


@router.get("/", auth=auth, response=PaginatedResponse[InvoiceOut])
async def list_invoices(
    request,
    pagination: PaginationSchema = Query(...),
    type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
):
    """
    List all invoices for the authenticated user (paginated).
    Supports filtering by type and status.
    """
    qs = Invoice.objects.filter(owner=request.user)

    if type:
        qs = qs.filter(type=type)
    if status:
        qs = qs.filter(status=status)

    items, total, total_pages = paginate_queryset(
        qs, pagination.page, pagination.per_page
    )

    return {
        "items": items,
        "total": total,
        "page": pagination.page,
        "per_page": pagination.per_page,
        "total_pages": total_pages,
    }


@router.post("/", auth=auth, response={201: InvoiceOut, 400: MessageOut})
async def create_invoice(request, payload: InvoiceCreate):
    """
    Create a new invoice with auto-generated invoice number.
    Items are created inline if provided.
    """
    raw = payload.model_dump()
    items_data = raw.pop("items", None) or []

    try:
        invoice_fields = _map_invoice_payload(raw)
        invoice_fields["invoice_number"] = _generate_invoice_number()
        if "tags" not in invoice_fields or invoice_fields["tags"] is None:
            invoice_fields["tags"] = []

        with db_transaction.atomic():
            invoice = Invoice.objects.create(owner=request.user, **invoice_fields)
            for item in items_data:
                InvoiceItem.objects.create(
                    invoice=invoice,
                    description=item["description"],
                    quantity=item["quantity"],
                    unit_price=item["unitPrice"],
                    total=item["total"],
                )
    except Exception as e:
        return 400, {"message": str(e)}

    return 201, invoice


@router.get("/next-number/", auth=auth, response=NextInvoiceNumberOut)
async def get_next_invoice_number(request):
    """Preview the next auto-generated invoice number."""
    return NextInvoiceNumberOut(nextInvoiceNumber=_generate_invoice_number())


@router.get("/{invoice_id}/", auth=auth, response={200: InvoiceOut, 404: MessageOut})
async def get_invoice(request, invoice_id: uuid.UUID):
    """Get a single invoice by ID with embedded items."""
    invoice = get_object_or_404(Invoice, id=invoice_id, owner=request.user)
    return invoice


@router.put(
    "/{invoice_id}/",
    auth=auth,
    response={200: InvoiceOut, 404: MessageOut, 400: MessageOut},
)
async def update_invoice(request, invoice_id: uuid.UUID, payload: InvoiceUpdate):
    """
    Update an invoice. If items are provided, all existing items
    are replaced atomically.
    """
    invoice = get_object_or_404(Invoice, id=invoice_id, owner=request.user)
    raw = payload.model_dump(exclude_unset=True)
    items_data = raw.pop("items", None)

    try:
        invoice_fields = _map_invoice_payload(raw)

        with db_transaction.atomic():
            for field, value in invoice_fields.items():
                setattr(invoice, field, value)
            invoice.save()

            if items_data is not None:
                invoice.items.all().delete()
                for item in items_data:
                    InvoiceItem.objects.create(
                        invoice=invoice,
                        description=item["description"],
                        quantity=item["quantity"],
                        unit_price=item["unitPrice"],
                        total=item["total"],
                    )
    except Exception as e:
        return 400, {"message": str(e)}

    invoice.refresh_from_db()
    return invoice


@router.delete("/{invoice_id}/", auth=auth, response={200: MessageOut, 404: MessageOut})
async def delete_invoice(request, invoice_id: uuid.UUID):
    """Delete an invoice and all its items."""
    invoice = get_object_or_404(Invoice, id=invoice_id, owner=request.user)
    invoice.delete()
    return {"message": "Invoice deleted successfully"}


# ==================== Invoice Actions ====================


@router.post(
    "/{invoice_id}/send/", auth=auth, response={200: InvoiceOut, 404: MessageOut}
)
async def send_invoice(request, invoice_id: uuid.UUID):
    """Mark an invoice as sent."""
    invoice = get_object_or_404(Invoice, id=invoice_id, owner=request.user)
    invoice.status = "sent"
    invoice.save()
    invoice.refresh_from_db()
    return invoice


@router.post(
    "/{invoice_id}/mark-paid/", auth=auth, response={200: InvoiceOut, 404: MessageOut}
)
async def mark_paid(request, invoice_id: uuid.UUID):
    """Mark an invoice as paid with today's date."""
    invoice = get_object_or_404(Invoice, id=invoice_id, owner=request.user)
    invoice.status = "paid"
    invoice.paid_date = date.today()
    invoice.save()
    invoice.refresh_from_db()
    return invoice


@router.post(
    "/{invoice_id}/cancel/", auth=auth, response={200: InvoiceOut, 404: MessageOut}
)
async def cancel_invoice(request, invoice_id: uuid.UUID):
    """Cancel an invoice."""
    invoice = get_object_or_404(Invoice, id=invoice_id, owner=request.user)
    invoice.status = "cancelled"
    invoice.save()
    invoice.refresh_from_db()
    return invoice
