# backend/config/urls.py

from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings
from ninja import NinjaAPI


api = NinjaAPI(
    title="SattaFinance API",
    description="Personal Accounting & Dashboard API",
    version="1.0.0",
    docs_url="/docs",
    openapi_url="/openapi.json",
)

admin.site.site_header = "SattaFinance admin"
admin.site.site_title = "SattaFinance admin"
# admin.site.site_url = ''
admin.site.index_title = "SattaFinanace administration"
# admin.empty_value_display = '**Empty**'

admin.autodiscover()
# admin.site.login = secure_admin_login(admin.site.login)  # type: ignore


@api.get("/hello")
def hello(request):
    return {"message": "Welcome to SattaFinanace API"}


# ==================== Auth ====================
from users.api import router as users_router  # noqa: E402

api.add_router("/auth/", users_router)


# ==================== Domain Apps ====================
from bank.api import router as bank_router  # noqa: E402
from income.api import router as income_router  # noqa: E402
from expense.api import router as expense_router  # noqa: E402
from card.api import router as card_router  # noqa: E402
from loan.api import router as loan_router  # noqa: E402
from budget.api import router as budget_router  # noqa: E402
from investment.api import router as investment_router  # noqa: E402
from insurance.api import router as insurance_router  # noqa: E402
from mortgage.api import router as mortgage_router  # noqa: E402
from savings_goal.api import router as savings_goal_router  # noqa: E402
from asset.api import router as asset_router  # noqa: E402
from lending.api import router as lending_router  # noqa: E402
from invoice.api import router as invoice_router  # noqa: E402
from bill.api import router as bill_router  # noqa: E402
from fcalender.api import router as calendar_router  # noqa: E402
from document.api import router as document_router  # noqa: E402

api.add_router("/bank/", bank_router)
api.add_router("/income/", income_router)
api.add_router("/expense/", expense_router)
api.add_router("/card/", card_router)
api.add_router("/loan/", loan_router)
api.add_router("/budget/", budget_router)
api.add_router("/investment/", investment_router)
api.add_router("/insurance/", insurance_router)
api.add_router("/mortgage/", mortgage_router)
api.add_router("/savings-goal/", savings_goal_router)
api.add_router("/asset/", asset_router)
api.add_router("/lending/", lending_router)
api.add_router("/invoice/", invoice_router)
api.add_router("/bill/", bill_router)
api.add_router("/calendar/", calendar_router)
api.add_router("/document/", document_router)


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", api.urls),
    path("", include("common.urls")),
    path("account/", include("users.urls")),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
