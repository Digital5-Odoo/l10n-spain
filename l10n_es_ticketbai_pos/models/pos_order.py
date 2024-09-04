# Copyright 2021 Binovo IT Human Project SL
# Copyright 2022 Landoo Sistemas de Informacion SL
# Copyright 2024 Digital5, S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, exceptions, fields, models
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT


class PosOrder(models.Model):
    _name = "pos.order"
    _inherit = ["pos.order", "tbai.mixin"]

    tbai_identifier = fields.Char(
        string="TBAI Identifier",
        related="tbai_invoice_id.tbai_identifier",
        store=True,
        copy=False,
    )
    tbai_qr_src = fields.Char(
        string="QR source", compute="_compute_tbai_qr_src", store=True, copy=False
    )
    tbai_invoice_ids = fields.One2many(
        comodel_name="tbai.invoice",
        inverse_name="pos_order_id",
        string="TicketBAI Invoices",
    )

    @api.depends("tbai_invoice_ids", "tbai_invoice_ids.state")
    def _compute_tbai_response_ids(self):
        for record in self:
            record.tbai_response_ids = [
                (6, 0, record.tbai_invoice_ids.mapped("tbai_response_ids").ids)
            ]

    @api.depends("date_order")
    def _compute_tbai_datetime_invoice(self):
        for record in self:
            record.tbai_datetime_invoice = fields.Datetime.now()

    @api.depends("tbai_invoice_id", "tbai_invoice_id.qr")
    def _compute_tbai_qr_src(self):
        for po in self:
            tbai_qr_src = ""
            if po.tbai_invoice_id:
                tbai_qr_src = "data:image/png;base64," + str(
                    po.tbai_invoice_id.qr.decode("UTF-8")
                )
            po.tbai_qr_src = tbai_qr_src

    @api.model
    def _order_fields(self, ui_order):
        res = super()._order_fields(ui_order)
        session = self.env["pos.session"].browse(ui_order["pos_session_id"])
        if session.config_id.tbai_enabled and not ui_order.get("to_invoice", False):
            res["tbai_vat_regime_key"] = ui_order.get("tbai_vat_regime_key", False)
        return res

    @api.model
    def _process_order(self, pos_order, draft, existing_order):
        if draft:
            return super()._process_order(pos_order, draft, existing_order)
        if pos_order["data"].get("tbai_vat_regime_key", False) and isinstance(
            pos_order["data"]["tbai_vat_regime_key"], str
        ):
            regime_key = pos_order["data"]["tbai_vat_regime_key"]
            pos_order["data"]["tbai_vat_regime_key"] = (
                self.env["tbai.vat.regime.key"]
                .search([("code", "=", regime_key)], limit=1)
                .id
            )
        order_id = super()._process_order(pos_order, draft, existing_order)
        order = self.env["pos.order"].browse(order_id)
        if order.config_id.tbai_enabled and not pos_order["data"].get(
            "to_invoice", False
        ):
            order._tbai_build_invoice()
            order.config_id.tbai_last_invoice_id = order.tbai_invoice_id
        return order.id

    def _export_for_ui(self, order):
        res = super()._export_for_ui(order)
        res["tbai_identifier"] = order.tbai_identifier
        res["tbai_qr_src"] = order.tbai_qr_src
        return res

    def _prepare_invoice_vals(self):
        res = super(PosOrder, self)._prepare_invoice_vals()
        if self.tbai_enabled:
            vat_regime_key_id = self.tbai_vat_regime_key
            if not vat_regime_key_id and self.partner_id:
                fp = self.env["account.fiscal.position"].get_fiscal_position(
                    self.partner_id.id
                )
                vat_regime_key_id = fp.tbai_vat_regime_key.id
            if not vat_regime_key_id:
                vat_regime_key_id = self.env.ref(
                    "l10n_es_ticketbai.tbai_vat_regime_01"
                ).id
            res.update({"tbai_vat_regime_key": vat_regime_key_id})
        return res

    def tbai_prepare_invoice_values(self):
        vals = super().tbai_prepare_invoice_values()
        vals.update(
            {
                "name": self.l10n_es_unique_id,
                "pos_order_id": self.id,
                "amount_total": "%.2f" % self.amount_total,
                "previous_tbai_invoice_id": self.config_id.tbai_last_invoice_id.id,
                "state": "pending",
            }
        )
        return vals

    def _tbai_build_invoice(self):
        tbai_inv_obj = self.env["tbai.invoice"]
        for record in self:
            vals = record.tbai_prepare_invoice_values()
            tbai_invoice = tbai_inv_obj.create(vals)
            tbai_invoice.sudo().build_tbai_simplified_invoice()
            record.tbai_invoice_id = tbai_invoice.id

    def tbai_prepare_cancellation_values(self):
        vals = super().tbai_prepare_cancellation_values()
        vals.update(
            {
                "pos_order_id": self.id,
            }
        )
        return vals

    def tbai_prepare_invoice_lines_values(self):
        self.ensure_one()
        lines = []
        for line in self.lines:
            description_line = line.name[:250] if line.name else ""
            if (
                self.company_id.tbai_protected_data
                and self.company_id.tbai_protected_data_txt
            ):
                description_line = self.company_id.tbai_protected_data_txt[:250]
            price_unit = line.tbai_get_price_unit()
            lines.append(
                (
                    0,
                    0,
                    {
                        "description": description_line,
                        "quantity": line.tbai_get_value_cantidad(),
                        "price_unit": "%.8f" % price_unit,
                        "discount_amount": line.tbai_get_value_descuento(price_unit),
                        "amount_total": line.tbai_get_value_importe_total(),
                    },
                )
            )
        return lines

    def tbai_prepare_invoice_tax_values(self):
        self.ensure_one()
        partner = self.partner_id.commercial_partner_id
        taxes_list = []
        taxes = {}
        for line in self.lines:
            for tax in line.tax_ids_after_fiscal_position:
                taxes.setdefault(
                    tax.id,
                    {
                        "is_subject_to": True,
                        "is_exempted": False,
                        "not_exempted_type": "S1",
                        "base": 0.0,
                        "amount": tax.amount,
                        "amount_total": 0.0,
                    },
                )
                price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
                computed_tax = tax.compute_all(
                    price,
                    self.pricelist_id.currency_id,
                    line.qty,
                    product=line.product_id,
                    partner=partner,
                )
                amount_total = (
                    computed_tax["total_included"] - computed_tax["total_excluded"]
                )
                taxes[tax.id]["base"] += computed_tax["total_excluded"]
                taxes[tax.id]["amount_total"] += amount_total
        for _tax_id, tax_values in taxes.items():
            tax_values["base"] = "%.2f" % tax_values["base"]
            tax_values["amount"] = "%.2f" % tax_values["amount"]
            tax_values["amount_total"] = "%.2f" % tax_values["amount_total"]
            taxes_list.append((0, 0, tax_values))
        return taxes_list

    def tbai_is_invoice_refund(self):
        return False

    def tbai_get_value_serie_factura(self):
        if hasattr(self.config_id, "pos_sequence_by_device") and self.pos_device_id:
            sequence = self.pos_device_id.sequence
        else:
            sequence = self.config_id.l10n_es_simplified_invoice_sequence_id
        date = fields.Datetime.context_timestamp(
            self, fields.Datetime.from_string(self.date_order)
        ).strftime(DEFAULT_SERVER_DATE_FORMAT)
        prefix, suffix = sequence.with_context(
            ir_sequence_date=date, ir_sequence_date_range=date
        )._get_prefix_suffix()
        return prefix

    def tbai_get_value_num_factura(self):
        invoice_number_prefix = self.tbai_get_value_serie_factura()
        if invoice_number_prefix and not self.l10n_es_unique_id.startswith(
            invoice_number_prefix
        ):
            raise exceptions.ValidationError(
                _("Simplified Invoice Number Prefix %s is not part of Number %%!")
                % (invoice_number_prefix, self.l10n_es_unique_id)
            )
        return self.l10n_es_unique_id[len(invoice_number_prefix) :]

    def tbai_get_value_fecha_exp_factura(self):
        date = fields.Datetime.context_timestamp(
            self, fields.Datetime.from_string(self.date_order)
        )
        return date.strftime("%d-%m-%Y")

    def tbai_get_value_hora_exp_factura(self):
        date = fields.Datetime.context_timestamp(
            self, fields.Datetime.from_string(self.date_order)
        )
        return date.strftime("%H:%M:%S")

    def tbai_get_value_simplified_invoice(self):
        return "S"

    def tbai_get_value_base_rectificada(self):
        return 0.0

    def tbai_get_value_cuota_rectificada(self):
        return 0.0

    def tbai_get_value_fecha_operacion(self):
        return self.tbai_get_value_fecha_exp_factura()

    def tbai_get_value_retencion_soportada(self):
        return None

    def _compute_tbai_description(self):
        self.tbai_description_operation = "/"


class PosOrderLine(models.Model):
    _name = "pos.order.line"
    _inherit = ["pos.order.line", "tbai.mixin.line"]

    def tbai_get_value_cantidad(self):
        return "%.2f" % self.qty

    def tbai_get_value_descuento(self, price_unit):
        return "%.2f" % (self.qty * price_unit * self.discount / 100.0)

    def tbai_get_value_importe_total(self):
        return "%.2f" % self.price_subtotal_incl

    def tbai_get_price_unit(self):
        return "%.8f" % self.price_unit
