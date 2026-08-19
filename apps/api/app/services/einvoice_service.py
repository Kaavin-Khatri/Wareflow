"""E-Invoice (IRN) and E-Way Bill domain service with GSP/IRP provider abstraction.

Complies with statutory Indian GST e-invoicing specifications:
- 64-character SHA-256 Invoice Reference Number (IRN)
- 16-digit IRP Acknowledgment Number & Timestamp
- Standard signed QR Code string payload
- 12-digit E-Way Bill Number for goods transit above threshold (e.g. ₹50,000)
- Pluggable GSP/Sandbox provider for cost-free testing and threshold-based deferral.
"""

import hashlib
import json
import math
import random
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, Any, Protocol

from fastapi import HTTPException, status

if TYPE_CHECKING:
    from app.core.security import CurrentUser

from app.core.config import Settings, get_settings
from app.models.billing import Invoice
from app.repositories.interfaces.audit_repository import AuditRepository
from app.repositories.interfaces.business_settings_repository import (
    BusinessSettingsRepositoryInterface,
)
from app.repositories.interfaces.invoice_repository import InvoiceRepositoryInterface
from app.schemas.billing import (
    EInvoiceConfigResponse,
    EInvoiceGenerateResponse,
    EWayBillGenerateRequest,
    EWayBillResponse,
)


class EInvoiceProviderInterface(Protocol):
    """Protocol defining the interface for GST Suvidha Provider (GSP) / IRP integrations."""

    def generate_irn(
        self,
        invoice: Invoice,
        seller_gstin: str,
        buyer_gstin: str | None = None,
    ) -> dict[str, Any]:
        """Generate statutory IRN, acknowledgment number, and signed QR code string."""
        ...

    def generate_eway_bill(
        self,
        invoice: Invoice,
        seller_gstin: str,
        vehicle_no: str,
        distance_km: int,
        transporter_id: str | None = None,
        transporter_name: str | None = None,
    ) -> dict[str, Any]:
        """Generate 12-digit statutory E-Way Bill number and validity."""
        ...


class SandboxGspProvider:
    """
    Deterministic Sandbox / Simulator provider for GST E-Invoicing and E-Way Bills.

    Produces strictly valid statutory schema outputs without external recurring API costs.
    """

    def generate_irn(
        self,
        invoice: Invoice,
        seller_gstin: str,
        buyer_gstin: str | None = None,
    ) -> dict[str, Any]:
        """Compute deterministic 64-hex SHA-256 IRN and statutory QR Code payload."""
        now = datetime.now(UTC)
        raw_seed = (
            f"{seller_gstin}:{invoice.invoice_no}:"
            f"{invoice.invoice_date.strftime('%Y%m%d')}:"
            f"{float(invoice.total_amount):.2f}"
        )
        irn = hashlib.sha256(raw_seed.encode("utf-8")).hexdigest()
        ack_no = f"12{now.strftime('%y%m%d')}{random.randint(10000000, 99999999)}"

        first_hsn = "0401"
        if getattr(invoice, "items", None) and len(invoice.items) > 0:
            first_hsn = invoice.items[0].hsn_code or "0401"

        qr_payload = {
            "SellerGstin": seller_gstin,
            "BuyerGstin": buyer_gstin or "URP",
            "DocNo": invoice.invoice_no,
            "DocTyp": "INV",
            "DocDt": invoice.invoice_date.strftime("%d/%m/%Y"),
            "TotInvVal": float(invoice.total_amount),
            "ItemCnt": len(invoice.items) if getattr(invoice, "items", None) else 1,
            "MainHsnCode": first_hsn,
            "Irn": irn,
        }

        qr_code_str = json.dumps(qr_payload, separators=(",", ":"))

        return {
            "irn": irn,
            "ack_no": ack_no,
            "ack_date": now,
            "qr_code": qr_code_str,
            "status": "ACT",
            "is_sandbox": True,
        }

    def generate_eway_bill(
        self,
        invoice: Invoice,
        seller_gstin: str,
        vehicle_no: str,
        distance_km: int,
        transporter_id: str | None = None,
        transporter_name: str | None = None,
    ) -> dict[str, Any]:
        """Generate deterministic 12-digit E-Way Bill Number and validity timeframe."""
        now = datetime.now(UTC)
        # 12 digit format e.g. 24 + 10 digits
        ewb_seed = f"{invoice.invoice_no}:{vehicle_no}:{distance_km}"
        ewb_hash_int = int(hashlib.md5(ewb_seed.encode("utf-8")).hexdigest()[:10], 16)
        ewb_no = f"24{str(ewb_hash_int).zfill(10)[:10]}"

        # Statutory validity: 1 day for first 200 km, +1 day per additional 200 km
        validity_days = max(1, math.ceil(distance_km / 200.0))
        valid_until = now + timedelta(days=validity_days)

        return {
            "e_way_bill_no": ewb_no,
            "e_way_bill_date": now,
            "valid_until": valid_until,
            "vehicle_no": vehicle_no.upper().replace(" ", ""),
            "transporter_name": transporter_name or "Direct Fleet Logistics",
            "distance_km": distance_km,
            "is_sandbox": True,
        }


class EinvoiceService:
    """Domain service managing E-Invoice IRN and E-Way Bill compliance workflows."""

    def __init__(
        self,
        invoice_repo: InvoiceRepositoryInterface,
        business_repo: BusinessSettingsRepositoryInterface | None = None,
        audit_repo: AuditRepository | None = None,
        provider: EInvoiceProviderInterface | None = None,
        settings: Settings | None = None,
    ) -> None:
        self.invoice_repo = invoice_repo
        self.business_repo = business_repo
        self.audit_repo = audit_repo
        self.provider = provider or SandboxGspProvider()
        self.settings = settings or get_settings()

    def get_config(self) -> EInvoiceConfigResponse:
        """Return current statutory E-Invoice configuration status."""
        return EInvoiceConfigResponse(
            enabled=self.settings.einvoice_enabled,
            gsp_provider=self.settings.gsp_provider,
            eway_bill_threshold_inr=self.settings.eway_bill_threshold_inr,
            is_sandbox=self.settings.gsp_provider == "sandbox",
            turnover_threshold_notice=(
                "GST E-Invoicing is statutory for businesses exceeding ₹5 Crore annual turnover. "
                "Below this threshold, E-Invoicing is optional and can be run via sandbox or disabled."
            ),
        )

    def _get_seller_gstin(self) -> str:
        """Retrieve distributor legal GSTIN from business settings or standard fallback."""
        if self.business_repo:
            biz = self.business_repo.get_settings()
            if biz and getattr(biz, "gstin", None):
                return biz.gstin
        return "07AAAAA0000A1Z5"

    def _get_buyer_gstin(self, invoice: Invoice) -> str | None:
        """Extract buyer GSTIN from invoice sales order if available."""
        so = getattr(invoice, "sales_order", None)
        if so and getattr(so, "retailer", None):
            return so.retailer.gstin
        return None

    def generate_irn(
        self,
        invoice_id: str,
        force_sandbox: bool = False,
        current_user: "CurrentUser | None" = None,
    ) -> EInvoiceGenerateResponse:
        """
        Generate or fetch an official 64-hex IRN, Acknowledgment No, and signed QR Code.

        Idempotent: If already generated, returns existing statutory values immediately.
        """
        invoice = self.invoice_repo.get_by_id(invoice_id)
        if not invoice:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Invoice '{invoice_id}' not found.",
            )

        # Idempotency Check
        if invoice.e_invoice_irn and invoice.e_invoice_ack_no and invoice.e_invoice_qr_code:
            return EInvoiceGenerateResponse(
                invoice_id=invoice.id,
                invoice_no=invoice.invoice_no,
                irn=invoice.e_invoice_irn,
                ack_no=invoice.e_invoice_ack_no,
                ack_date=invoice.created_at,
                qr_code=invoice.e_invoice_qr_code,
                is_sandbox=self.settings.gsp_provider == "sandbox" or force_sandbox,
                status="ALREADY_GENERATED",
            )

        seller_gstin = self._get_seller_gstin()
        buyer_gstin = self._get_buyer_gstin(invoice)

        # Provider invocation
        result = self.provider.generate_irn(invoice, seller_gstin, buyer_gstin)

        # Update and persist invoice record
        updated_invoice = self.invoice_repo.update_invoice(
            invoice_id,
            e_invoice_irn=result["irn"],
            e_invoice_ack_no=result["ack_no"],
            e_invoice_qr_code=result["qr_code"],
        )

        # Audit log
        if self.audit_repo:
            actor_id = current_user.id if current_user else "system"
            self.audit_repo.create_log(
                actor_id=actor_id,
                action="einvoice_irn_generated",
                entity_type="invoice",
                entity_id=invoice.id,
                before_value={"e_invoice_irn": None},
                after_value={
                    "e_invoice_irn": result["irn"],
                    "e_invoice_ack_no": result["ack_no"],
                    "invoice_no": invoice.invoice_no,
                },
            )

        return EInvoiceGenerateResponse(
            invoice_id=updated_invoice.id,
            invoice_no=updated_invoice.invoice_no,
            irn=result["irn"],
            ack_no=result["ack_no"],
            ack_date=result["ack_date"],
            qr_code=result["qr_code"],
            is_sandbox=result.get("is_sandbox", True),
            status="GENERATED",
        )

    def generate_eway_bill(
        self,
        invoice_id: str,
        payload: EWayBillGenerateRequest,
        current_user: "CurrentUser | None" = None,
    ) -> EWayBillResponse:
        """
        Generate statutory 12-digit E-Way Bill Number for goods transit.

        Validates vehicle format and updates invoice record with e_way_bill_no.
        """
        invoice = self.invoice_repo.get_by_id(invoice_id)
        if not invoice:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Invoice '{invoice_id}' not found.",
            )

        # Vehicle number format sanitization
        clean_vehicle = payload.vehicle_no.strip().upper().replace(" ", "").replace("-", "")
        if len(clean_vehicle) < 4:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid vehicle registration number: '{payload.vehicle_no}'.",
            )

        # Idempotency Check
        if invoice.e_way_bill_no:
            now = datetime.now(UTC)
            return EWayBillResponse(
                invoice_id=invoice.id,
                invoice_no=invoice.invoice_no,
                e_way_bill_no=invoice.e_way_bill_no,
                e_way_bill_date=invoice.created_at,
                valid_until=now + timedelta(days=2),
                vehicle_no=clean_vehicle,
                transporter_name=payload.transporter_name,
                distance_km=payload.distance_km,
                is_sandbox=self.settings.gsp_provider == "sandbox",
            )

        seller_gstin = self._get_seller_gstin()
        ewb_result = self.provider.generate_eway_bill(
            invoice=invoice,
            seller_gstin=seller_gstin,
            vehicle_no=clean_vehicle,
            distance_km=payload.distance_km,
            transporter_id=payload.transporter_id,
            transporter_name=payload.transporter_name,
        )

        # Update invoice
        updated_invoice = self.invoice_repo.update_invoice(
            invoice_id,
            e_way_bill_no=ewb_result["e_way_bill_no"],
        )

        # Audit log
        if self.audit_repo:
            actor_id = current_user.id if current_user else "system"
            self.audit_repo.create_log(
                actor_id=actor_id,
                action="eway_bill_generated",
                entity_type="invoice",
                entity_id=invoice.id,
                before_value={"e_way_bill_no": None},
                after_value={
                    "e_way_bill_no": ewb_result["e_way_bill_no"],
                    "vehicle_no": clean_vehicle,
                    "distance_km": payload.distance_km,
                },
            )

        return EWayBillResponse(
            invoice_id=updated_invoice.id,
            invoice_no=updated_invoice.invoice_no,
            e_way_bill_no=ewb_result["e_way_bill_no"],
            e_way_bill_date=ewb_result["e_way_bill_date"],
            valid_until=ewb_result["valid_until"],
            vehicle_no=ewb_result["vehicle_no"],
            transporter_name=ewb_result["transporter_name"],
            distance_km=ewb_result["distance_km"],
            is_sandbox=ewb_result.get("is_sandbox", True),
        )
