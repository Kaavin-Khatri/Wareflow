"""Logistics Document Export Service for generating print-ready Pick Lists and Packing Slips."""

import io
from collections import defaultdict
from datetime import UTC, datetime
from typing import Any

from fastapi import HTTPException, status
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import (
    HRFlowable,
    KeepTogether,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from app.models.retailer import SalesOrder
from app.repositories.interfaces.business_settings_repository import (
    BusinessSettingsRepositoryInterface,
)
from app.repositories.interfaces.delivery_repository import DeliveryRepositoryInterface
from app.repositories.interfaces.sales_order_repository import SalesOrderRepositoryInterface


class ExportService:
    """Document export service generating print-ready PDF pick lists and customer packing slips."""

    def __init__(
        self,
        sales_order_repo: SalesOrderRepositoryInterface,
        business_settings_repo: BusinessSettingsRepositoryInterface | None = None,
        delivery_repo: DeliveryRepositoryInterface | None = None,
        stock_repo: Any | None = None,
    ) -> None:
        self.sales_order_repo = sales_order_repo
        self.business_settings_repo = business_settings_repo
        self.delivery_repo = delivery_repo
        self.stock_repo = stock_repo

    def _get_buyer_details(self, order: SalesOrder) -> dict[str, str]:
        """Extract buyer name, contact, phone, and destination address."""
        if order.retailer:
            return {
                "name": order.retailer.name or "Wholesale Retailer",
                "contact": order.retailer.contact_person or "—",
                "phone": order.retailer.phone or "—",
                "address": order.retailer.address or "Registered Retailer Location",
                "type": "B2B Retailer",
            }
        if order.customer:
            return {
                "name": order.customer.name or "Direct Buyer",
                "contact": order.customer.name or "—",
                "phone": order.customer.phone or "—",
                "address": order.customer.address or "Direct Delivery Address",
                "type": "Direct Customer",
            }
        return {
            "name": getattr(order, "retailer_name", None) or "Direct Buyer",
            "contact": "—",
            "phone": "—",
            "address": "Warehouse Pickup / Delivery Destination",
            "type": "Buyer",
        }

    def generate_pick_list(self, sales_order_id: str) -> bytes:
        """
        Generate staff-facing Warehouse Pick List PDF.

        Strict constraints:
        - Large print with checkbox per line for warehouse floor tick-off.
        - Grouped by warehouse if items originate from multiple warehouses.
        - ZERO pricing information (staff packing orders must not see prices).
        """
        order = self.sales_order_repo.get_by_id(sales_order_id)
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Sales order '{sales_order_id}' not found",
            )

        buyer = self._get_buyer_details(order)
        delivery = (
            self.delivery_repo.get_by_sales_order_id(sales_order_id)
            if self.delivery_repo
            else None
        )

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            leftMargin=24,
            rightMargin=24,
            topMargin=24,
            bottomMargin=24,
            pageCompression=0,
        )

        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            "PickTitle",
            parent=styles["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=16,
            leading=18,
            textColor=colors.HexColor("#0F172A"),
        )
        subtitle_style = ParagraphStyle(
            "PickSubTitle",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=8,
            leading=10,
            textColor=colors.HexColor("#64748B"),
        )
        cell_bold = ParagraphStyle(
            "CellBold",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=9,
            leading=11,
            textColor=colors.HexColor("#0F172A"),
        )
        cell_normal = ParagraphStyle(
            "CellNormal",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=8,
            leading=10,
            textColor=colors.HexColor("#334155"),
        )
        header_cell = ParagraphStyle(
            "HeaderCell",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8,
            leading=10,
            textColor=colors.HexColor("#FFFFFF"),
        )

        elements: list[Any] = []

        # Document Header
        header_table = Table(
            [
                [
                    Paragraph("WAREHOUSE PICK LIST", title_style),
                    Paragraph(
                        f"<b>SO: {order.so_number}</b><br/>"
                        f"<font size='8' color='#64748B'>Status: {order.status.value.upper()}</font>",
                        ParagraphStyle("RightHead", parent=cell_bold, alignment=TA_RIGHT),
                    ),
                ],
                [
                    Paragraph(
                        "Staff-facing picking & carton staging document • Keep in warehouse",
                        subtitle_style,
                    ),
                    Paragraph(
                        f"Order Date: {order.order_date.strftime('%d %b %Y') if order.order_date else datetime.now(UTC).strftime('%d %b %Y')}",
                        ParagraphStyle("RightDate", parent=cell_normal, alignment=TA_RIGHT),
                    ),
                ],
            ],
            colWidths=[345, 200],
        )
        header_table.setStyle(
            TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                ("TOPPADDING", (0, 0), (-1, -1), 2),
            ])
        )
        elements.append(header_table)
        elements.append(Spacer(1, 8))
        elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#CBD5E1")))
        elements.append(Spacer(1, 8))

        # Order Meta Box
        dest_addr = getattr(delivery, "destination_address", None) or buyer["address"]
        meta_table = Table(
            [
                [
                    Paragraph(f"<b>Buyer:</b> {buyer['name']}", cell_normal),
                    Paragraph(f"<b>Contact:</b> {buyer['contact']} ({buyer['phone']})", cell_normal),
                ],
                [
                    Paragraph(f"<b>Destination:</b> {dest_addr}", cell_normal),
                    Paragraph(
                        f"<b>Driver/Vehicle:</b> {delivery.driver_name or 'Unassigned'} / {delivery.vehicle_no or '—'}"
                        if delivery
                        else "<b>Driver/Vehicle:</b> Unassigned",
                        cell_normal,
                    ),
                ],
            ],
            colWidths=[270, 275],
        )
        meta_table.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#F1F5F9")),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ])
        )
        elements.append(meta_table)
        elements.append(Spacer(1, 12))

        # Group items by Warehouse
        # If order items have explicit warehouse or stock movements exist, group them; otherwise default to primary
        warehouse_groups: dict[str, list[Any]] = defaultdict(list)
        for item in order.items:
            wh_name = "Main Warehouse (Primary Storage)"
            if hasattr(item, "warehouse_name") and item.warehouse_name:
                wh_name = item.warehouse_name
            elif hasattr(item.product, "warehouse") and item.product.warehouse:
                wh_name = item.product.warehouse.name
            warehouse_groups[wh_name].append(item)

        # Build Table for each Warehouse Group
        for wh_name, items in warehouse_groups.items():
            wh_header = Paragraph(
                f"<b>Warehouse Location: {wh_name}</b>",
                ParagraphStyle("WHHead", parent=cell_bold, fontSize=10, textColor=colors.HexColor("#1E293B")),
            )
            elements.append(wh_header)
            elements.append(Spacer(1, 4))

            table_data = [
                [
                    Paragraph("Pick", header_cell),
                    Paragraph("SKU", header_cell),
                    Paragraph("Product Description", header_cell),
                    Paragraph("Pick Qty", header_cell),
                    Paragraph("UoM", header_cell),
                    Paragraph("Storage Bin / Loc", header_cell),
                ]
            ]

            for item in items:
                sku = item.product.sku if item.product else "—"
                name = item.product.name if item.product else "Product"
                qty = f"{item.qty:g}"
                uom = item.uom.symbol if item.uom else (item.product.unit if item.product else "PCS")
                location = getattr(item.product, "storage_location", None) or "Aisle / Bin Staging"

                table_data.append([
                    Paragraph("<b>[ &nbsp; ]</b>", ParagraphStyle("Chk", parent=cell_bold, alignment=TA_CENTER, fontSize=11)),
                    Paragraph(f"<b>{sku}</b>", cell_normal),
                    Paragraph(name, cell_normal),
                    Paragraph(f"<b>{qty}</b>", ParagraphStyle("QtyP", parent=cell_bold, fontSize=10, alignment=TA_CENTER)),
                    Paragraph(uom or "PCS", ParagraphStyle("UomP", parent=cell_normal, alignment=TA_CENTER)),
                    Paragraph(location, cell_normal),
                ])

            pick_table = Table(table_data, colWidths=[40, 85, 200, 65, 55, 100])
            pick_table.setStyle(
                TableStyle([
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1E293B")),
                    ("ALIGN", (0, 0), (-1, 0), "LEFT"),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
                    ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ])
            )
            elements.append(pick_table)
            elements.append(Spacer(1, 10))

        # Sign-off and Verification Footer Block
        elements.append(Spacer(1, 6))
        sign_table = Table(
            [
                [
                    Paragraph("<b>Picking Verification:</b>", cell_bold),
                    Paragraph("<b>Packing & Staging Check:</b>", cell_bold),
                ],
                [
                    Paragraph(
                        "Picked by (Name): _______________________<br/>"
                        "Date & Time: ___________________________<br/>"
                        "All Items Verified: [ &nbsp; ] &nbsp; Shortage Flagged: [ &nbsp; ]",
                        cell_normal,
                    ),
                    Paragraph(
                        "Packer / QA (Name): ______________________<br/>"
                        "Number of Cartons / Crates: ______________<br/>"
                        "Packing Slip Placed in Box: [ &nbsp; ]",
                        cell_normal,
                    ),
                ],
            ],
            colWidths=[270, 275],
        )
        sign_table.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#94A3B8")),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ])
        )
        elements.append(KeepTogether(sign_table))

        doc.build(elements)
        buffer.seek(0)
        return buffer.getvalue()

    def generate_packing_slip(self, sales_order_id: str) -> bytes:
        """
        Generate customer-facing Packing Slip / Delivery Manifest PDF.

        Strict constraints:
        - Professional document placed inside or affixed to the shipping box.
        - Contains distributor identity, destination, line items, and receiver acknowledgment.
        - ZERO pricing information (invoices handle money/taxes; packing slips handle physical verification).
        """
        order = self.sales_order_repo.get_by_id(sales_order_id)
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Sales order '{sales_order_id}' not found",
            )

        buyer = self._get_buyer_details(order)
        delivery = (
            self.delivery_repo.get_by_sales_order_id(sales_order_id)
            if self.delivery_repo
            else None
        )

        settings = (
            self.business_settings_repo.get_settings()
            if self.business_settings_repo
            else None
        )

        legal_name = (
            getattr(settings, "business_name", None)
            or getattr(settings, "legal_name", None)
            or "WAREFLOW DISTRIBUTION LTD"
        )
        address = getattr(settings, "address", None) or "Central Logistics Park, Sector 4, Mumbai"
        gstin = getattr(settings, "gstin", None) or "27AAAAA0000A1Z5"
        fssai = getattr(settings, "fssai_license_no", None) or "10020011000123"
        phone = getattr(settings, "phone", None) or "+91 22 2847 0000"
        email = getattr(settings, "email", None) or "dispatch@wareflow.io"

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            leftMargin=24,
            rightMargin=24,
            topMargin=24,
            bottomMargin=24,
            pageCompression=0,
        )

        styles = getSampleStyleSheet()
        company_style = ParagraphStyle(
            "CompanyTitle",
            parent=styles["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=14,
            leading=16,
            textColor=colors.HexColor("#0F172A"),
        )
        doc_title_style = ParagraphStyle(
            "DocTitle",
            parent=styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=13,
            leading=15,
            textColor=colors.HexColor("#4338CA"),
            alignment=TA_RIGHT,
        )
        normal_text = ParagraphStyle(
            "NormalText",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=8,
            leading=10,
            textColor=colors.HexColor("#334155"),
        )
        bold_text = ParagraphStyle(
            "BoldText",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8.5,
            leading=11,
            textColor=colors.HexColor("#0F172A"),
        )
        header_cell = ParagraphStyle(
            "HeaderCell",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8.5,
            leading=10,
            textColor=colors.HexColor("#FFFFFF"),
        )

        elements: list[Any] = []

        # Top Header: Distributor Identity + Document Title
        top_table = Table(
            [
                [
                    Paragraph(f"<b>{legal_name}</b>", company_style),
                    Paragraph("PACKING SLIP", doc_title_style),
                ],
                [
                    Paragraph(
                        f"{address}<br/>"
                        f"GSTIN: {gstin} &nbsp;|&nbsp; FSSAI Lic: {fssai}<br/>"
                        f"Phone: {phone} &nbsp;|&nbsp; Email: {email}",
                        normal_text,
                    ),
                    Paragraph(
                        f"<b>SO No: {order.so_number}</b><br/>"
                        f"<font size='7.5' color='#64748B'>Delivery Manifest / Consignee Copy</font><br/>"
                        f"Date: {order.order_date.strftime('%d %b %Y') if order.order_date else datetime.now(UTC).strftime('%d %b %Y')}",
                        ParagraphStyle("RightMeta", parent=normal_text, alignment=TA_RIGHT),
                    ),
                ],
            ],
            colWidths=[335, 210],
        )
        top_table.setStyle(
            TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                ("TOPPADDING", (0, 0), (-1, -1), 1),
            ])
        )
        elements.append(top_table)
        elements.append(Spacer(1, 8))
        elements.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#4338CA")))
        elements.append(Spacer(1, 8))

        # Ship-To & Logistics Grid
        dest_addr = getattr(delivery, "destination_address", None) or buyer["address"]
        logistics_info = (
            f"<b>Driver Name:</b> {delivery.driver_name or 'Standard Dispatch'}<br/>"
            f"<b>Vehicle No:</b> {delivery.vehicle_no or '—'}<br/>"
            f"<b>Dispatch Status:</b> {order.status.value.upper()}"
            if delivery
            else f"<b>Dispatch Mode:</b> Standard Logistics<br/><b>Status:</b> {order.status.value.upper()}"
        )

        dispatch_grid = Table(
            [
                [
                    Paragraph("<b>SHIP TO / CONSIGNEE:</b>", bold_text),
                    Paragraph("<b>LOGISTICS & TRANSPORT:</b>", bold_text),
                ],
                [
                    Paragraph(
                        f"<b>{buyer['name']}</b> ({buyer['type']})<br/>"
                        f"Contact Person: {buyer['contact']}<br/>"
                        f"Phone: {buyer['phone']}<br/>"
                        f"Delivery Address: {dest_addr}",
                        normal_text,
                    ),
                    Paragraph(logistics_info, normal_text),
                ],
            ],
            colWidths=[300, 245],
        )
        dispatch_grid.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#F1F5F9")),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ])
        )
        elements.append(dispatch_grid)
        elements.append(Spacer(1, 10))

        # Shipped Items Table
        items_header = Paragraph("<b>SHIPPED ITEMS MANIFEST:</b>", bold_text)
        elements.append(items_header)
        elements.append(Spacer(1, 4))

        table_data = [
            [
                Paragraph("#", header_cell),
                Paragraph("SKU", header_cell),
                Paragraph("Item Description", header_cell),
                Paragraph("Qty Shipped", header_cell),
                Paragraph("Packaging / UoM", header_cell),
                Paragraph("Verified", header_cell),
            ]
        ]

        total_units = 0.0
        for idx, item in enumerate(order.items, start=1):
            sku = item.product.sku if item.product else "—"
            name = item.product.name if item.product else "Product"
            qty = float(item.qty)
            total_units += qty
            uom = item.uom.symbol if item.uom else (item.product.unit if item.product else "PCS")

            table_data.append([
                Paragraph(str(idx), ParagraphStyle("IdxP", parent=normal_text, alignment=TA_CENTER)),
                Paragraph(f"<b>{sku}</b>", normal_text),
                Paragraph(name, normal_text),
                Paragraph(f"<b>{qty:g}</b>", ParagraphStyle("QtyP", parent=bold_text, alignment=TA_CENTER)),
                Paragraph(uom or "PCS", ParagraphStyle("UomP", parent=normal_text, alignment=TA_CENTER)),
                Paragraph("[ &nbsp;✓&nbsp; ]", ParagraphStyle("VrfP", parent=bold_text, alignment=TA_CENTER)),
            ])

        # Summary Row (Quantity count only, zero currency)
        table_data.append([
            Paragraph("", normal_text),
            Paragraph("<b>TOTAL ITEMS</b>", bold_text),
            Paragraph(f"<b>{len(order.items)} Line Items</b>", normal_text),
            Paragraph(f"<b>{total_units:g}</b>", ParagraphStyle("TotQty", parent=bold_text, alignment=TA_CENTER)),
            Paragraph("Units", ParagraphStyle("TotUom", parent=normal_text, alignment=TA_CENTER)),
            Paragraph("", normal_text),
        ])

        items_table = Table(table_data, colWidths=[25, 90, 230, 75, 75, 50])
        items_table.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#4338CA")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
                ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#F1F5F9")),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
            ])
        )
        elements.append(items_table)
        elements.append(Spacer(1, 10))

        # Receiver Acknowledgment Block
        ack_table = Table(
            [
                [
                    Paragraph("<b>CONSIGNEE / RECEIVER ACKNOWLEDGMENT:</b>", bold_text),
                    Paragraph("<b>DISPATCH VERIFICATION:</b>", bold_text),
                ],
                [
                    Paragraph(
                        "Received the above goods in good order and complete condition.<br/><br/>"
                        "Receiver Full Name: _________________________________<br/>"
                        "Signature & Stamp: __________________________________<br/>"
                        "Date & Time Received: _______________________________",
                        normal_text,
                    ),
                    Paragraph(
                        "Dispatched By: ____________________________________<br/>"
                        "Warehouse Dispatch Stamp:<br/><br/>"
                        "Security Gate Pass Verified: [ &nbsp; ]",
                        normal_text,
                    ),
                ],
            ],
            colWidths=[310, 235],
        )
        ack_table.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#94A3B8")),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ])
        )
        elements.append(KeepTogether(ack_table))
        elements.append(Spacer(1, 6))

        # Bottom Legal Notice
        elements.append(
            Paragraph(
                "<i>Notice: This document is a physical Packing Slip & Delivery Manifest. It is NOT a Tax Invoice. "
                "The official GST Tax Invoice is issued separately as per statutory accounting rules.</i>",
                ParagraphStyle("Disclaimer", parent=normal_text, fontSize=7, textColor=colors.HexColor("#64748B"), alignment=TA_CENTER),
            )
        )

        doc.build(elements)
        buffer.seek(0)
        return buffer.getvalue()
