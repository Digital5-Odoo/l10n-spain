# Copyright 2024 Digital5, S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models


class TbaiMixin(models.AbstractModel):
    _name = "tbai.mixin"
    _description = "TicketBAI Mixin"

    company_id = fields.Many2one(comodel_name="res.company", string="Company")
    tbai_enabled = fields.Boolean(related="company_id.tbai_enabled", readonly=True)
    tbai_invoice_id = fields.Many2one(
        comodel_name="tbai.invoice", string="Last TicketBAI Invoice", copy=False
    )
    tbai_response_ids = fields.Many2many(
        comodel_name="tbai.response",
        compute="_compute_tbai_response_ids",
        string="Responses",
    )
    tbai_datetime_invoice = fields.Datetime(
        compute="_compute_tbai_datetime_invoice", store=True, copy=False
    )
    tbai_date_operation = fields.Datetime("Operation Date", copy=False)
    tbai_description_operation = fields.Text(
        "Operation Description",
        default="/",
        copy=False,
        compute="_compute_tbai_description",
        store=True,
    )
    tbai_refund_key = fields.Selection(
        selection=[
            ("R1", "Art. 80.1, 80.2, 80.6 and rights founded error"),
            ("R2", "Art. 80.3"),
            ("R3", "Art. 80.4"),
            ("R4", "Art. 80 - other"),
            ("R5", "Simplified Invoice"),
        ],
        help="BOE-A-1992-28740. Ley 37/1992, de 28 de diciembre, del Impuesto sobre el "
        "Valor Añadido. Artículo 80. Modificación de la base imponible.",
        copy=False,
    )
    tbai_refund_type = fields.Selection(
        selection=[("I", "By differences")],
        copy=False,
    )
    tbai_vat_regime_key = fields.Many2one(
        comodel_name="tbai.vat.regime.key",
        string="VAT Regime Key",
        copy=True,
        compute="_compute_tbai_vat_regime_key",
    )
    tbai_vat_regime_key2 = fields.Many2one(
        comodel_name="tbai.vat.regime.key", string="VAT Regime 2nd Key", copy=True
    )
    tbai_vat_regime_key3 = fields.Many2one(
        comodel_name="tbai.vat.regime.key", string="VAT Regime 3rd Key", copy=True
    )
    tbai_refund_origin_ids = fields.One2many(
        comodel_name="tbai.invoice.refund.origin",
        inverse_name="account_refund_invoice_id",
        string="TicketBAI Refund Origin References",
    )

    def _compute_tbai_response_ids(self):
        for record in self:
            response_ids = record.tbai_invoice_id.mapped("tbai_response_ids").ids
            record.tbai_response_ids = [(6, 0, response_ids)]

    def _compute_tbai_datetime_invoice(self):
        raise NotImplementedError

    @api.depends("fiscal_position_id")
    def _compute_tbai_vat_regime_key(self):
        default_tbai_vat_regime_key = self.env["tbai.vat.regime.key"].search(
            [("code", "=", "01")], limit=1
        )
        for document in self:
            if document.fiscal_position_id:
                document.tbai_vat_regime_key = (
                    document.fiscal_position_id.tbai_vat_regime_key
                )
                document.tbai_vat_regime_key2 = (
                    document.fiscal_position_id.tbai_vat_regime_key2
                )
                document.tbai_vat_regime_key3 = (
                    document.fiscal_position_id.tbai_vat_regime_key3
                )
            else:
                document.tbai_vat_regime_key = default_tbai_vat_regime_key

    def tbai_prepare_invoice_values(self):
        def tbai_prepare_refund_values():
            refunded_inv = self.reversed_entry_id
            if refunded_inv:
                vals.update(
                    {
                        "is_invoice_refund": True,
                        "refund_code": self.tbai_refund_key,
                        "refund_type": self.tbai_refund_type,
                        "tbai_invoice_refund_ids": [
                            (
                                0,
                                0,
                                {
                                    "number_prefix": (
                                        refunded_inv.tbai_get_value_serie_factura()
                                    ),
                                    "number": (
                                        refunded_inv.tbai_get_value_num_factura()
                                    ),
                                    "expedition_date": (
                                        refunded_inv.tbai_get_value_fecha_exp_factura()
                                    ),
                                },
                            )
                        ],
                    }
                )
            else:
                if self.tbai_refund_origin_ids:
                    refund_id_dicts = []
                    for refund_origin_id in self.tbai_refund_origin_ids:
                        expedition_date = fields.Date.from_string(
                            refund_origin_id.expedition_date
                        ).strftime("%d-%m-%Y")
                        refund_id_dicts.append(
                            (
                                0,
                                0,
                                {
                                    "number_prefix": refund_origin_id.number_prefix,
                                    "number": refund_origin_id.number,
                                    "expedition_date": expedition_date,
                                },
                            )
                        )
                    vals.update(
                        {
                            "is_invoice_refund": True,
                            "refund_code": self.tbai_refund_key,
                            "refund_type": self.tbai_refund_type,
                            "tbai_invoice_refund_ids": refund_id_dicts,
                        }
                    )

        self.ensure_one()
        vals = {
            "schema": "TicketBai",
            "partner_id": self.partner_id.commercial_partner_id.id,
            "company_id": self.company_id.id,
            "number_prefix": self.tbai_get_value_serie_factura(),
            "number": self.tbai_get_value_num_factura(),
            "expedition_date": self.tbai_get_value_fecha_exp_factura(),
            "expedition_hour": self.tbai_get_value_hora_exp_factura(),
            "simplified_invoice": self.tbai_get_value_simplified_invoice(),
            "substitutes_simplified_invoice": (
                self.tbai_get_value_factura_emitida_sustitucion_simplificada()
            ),
            "description": self.tbai_description_operation[:250],
            "vat_regime_key": self.tbai_vat_regime_key.code,
            "vat_regime_key2": self.tbai_vat_regime_key2.code,
            "vat_regime_key3": self.tbai_vat_regime_key3.code,
        }
        retencion_soportada = self.tbai_get_value_retencion_soportada()
        if retencion_soportada:
            vals["tax_retention_amount_total"] = retencion_soportada
        if self.tbai_is_invoice_refund() and self.tbai_refund_type == "I":
            tbai_prepare_refund_values()
        operation_date = self.tbai_get_value_fecha_operacion()
        if operation_date:
            vals["operation_date"] = operation_date
        gipuzkoa_tax_agency = self.env.ref("l10n_es_aeat.aeat_tax_agency_gipuzkoa")
        araba_tax_agency = self.env.ref("l10n_es_aeat.aeat_tax_agency_araba")
        tax_agency = self.company_id.tax_agency_id
        if tax_agency in (gipuzkoa_tax_agency, araba_tax_agency):
            lines = self.tbai_prepare_invoice_lines_values()
            vals["tbai_invoice_line_ids"] = lines
        taxes = self.tbai_prepare_invoice_tax_values()
        vals["tbai_tax_ids"] = taxes
        return vals

    def _tbai_build_invoice(self):
        tbai_inv_obj = self.env["tbai.invoice"]
        for record in self:
            vals = record.tbai_prepare_invoice_values()
            tbai_invoice = tbai_inv_obj.create(vals)
            tbai_invoice.build_tbai_invoice()
            record.tbai_invoice_id = tbai_invoice.id

    def tbai_prepare_cancellation_values(self):
        self.ensure_one()
        vals = {
            "schema": "AnulaTicketBai",
            "partner_id": self.partner_id.commercial_partner_id.id,
            "name": "{} - {}".format(_("Cancellation"), self.name),
            "company_id": self.company_id.id,
            "number_prefix": self.tbai_get_value_serie_factura(),
            "number": self.tbai_get_value_num_factura(),
            "expedition_date": self.tbai_get_value_fecha_exp_factura(),
        }
        return vals

    def _tbai_invoice_cancel(self):
        tbai_inv_obj = self.env["tbai.invoice"]
        for record in self:
            vals = record.tbai_prepare_cancellation_values()
            tbai_invoice = tbai_inv_obj.create(vals)
            tbai_invoice.build_tbai_invoice()
            record.tbai_invoice_id = tbai_invoice.id

    def tbai_prepare_invoice_lines_values(self):
        """
        Returns:
            dict: {
                'description': '',
                'quantity': tbai_get_value_cantidad(),
                'price_unit': tbai_get_price_unit(),
                'discount_amount': tbai_get_value_descuento(),
                'amount_total': tbai_get_value_importe_total(),
            }
        """
        raise NotImplementedError()

    def tbai_prepare_invoice_tax_values(self):
        raise NotImplementedError()

    def tbai_is_invoice_refund(self):
        raise NotImplementedError()

    def tbai_get_value_serie_factura(self):
        raise NotImplementedError()

    def tbai_get_value_num_factura(self):
        raise NotImplementedError()

    def tbai_get_value_fecha_exp_factura(self):
        raise NotImplementedError()

    def tbai_get_value_hora_exp_factura(self):
        raise NotImplementedError()

    def tbai_get_value_simplified_invoice(self):
        if self.partner_id.aeat_simplified_invoice or not self.partner_id:
            res = "S"
        else:
            res = "N"
        return res

    def tbai_get_value_factura_emitida_sustitucion_simplificada(self):
        return "N"

    def tbai_get_value_base_rectificada(self):
        raise NotImplementedError()

    def tbai_get_value_cuota_rectificada(self):
        raise NotImplementedError()

    def tbai_get_value_fecha_operacion(self):
        raise NotImplementedError()

    def tbai_get_value_retencion_soportada(self):
        raise NotImplementedError()

    def _compute_tbai_description(self):
        self.tbai_description_operation = "/"


class TbaiMixinLine(models.AbstractModel):
    _name = "tbai.mixin.line"
    _description = "TicketBAI Line Mixin"

    def tbai_get_value_cantidad(self):
        raise NotImplementedError()

    def tbai_get_value_descuento(self, price_unit):
        raise NotImplementedError()

    def tbai_get_value_importe_total(self):
        raise NotImplementedError()

    def tbai_get_price_unit(self):
        raise NotImplementedError()
