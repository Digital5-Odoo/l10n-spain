# Copyright 2020 Binovo IT Human Project SL
# Copyright 2021 Landoo Sistemas de Informacion SL
# Copyright 2021 Digital5, S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import _, exceptions, models


class AccountTax(models.Model):
    _inherit = "account.tax"

    def tbai_is_subject_to_tax(self):
        s_iva_ns_tbai_maps = self.env["tbai.tax.map"].search(
            [("code", "in", ("SNS", "BNS"))]
        )
        s_iva_ns_taxes = self.company_id.get_taxes_from_templates(
            s_iva_ns_tbai_maps.mapped("tax_template_ids")
        )
        return self not in s_iva_ns_taxes

    def tbai_is_tax_exempted(self):
        map_ids = self.env["tbai.tax.map"].search([("code", "in", ["IEE", "SER"])])
        tax_ids = self.company_id.get_taxes_from_templates(
            map_ids.mapped("tax_template_ids")
        )
        return self in tax_ids

    def tbai_get_exemption_cause(self, invoice_id):
        return (
            self.env["account.fp.tbai.tax"]
            .search(
                [
                    ("tax_id", "=", self.id),
                    ("position_id", "=", invoice_id.fiscal_position_id.id),
                ],
                limit=1,
            )
            .tbai_vat_exemption_key.code
        )

    def tbai_get_amount_total_company(self, invoice_id):
        if invoice_id.currency_id.id != invoice_id.company_id.currency_id.id:
            currency = invoice_id.currency_id
            amount = self.tbai_get_invoice_amount_for_tax_group(invoice_id)
            amount_total = currency._convert(
                amount,
                invoice_id.company_id.currency_id,
                invoice_id.company_id,
                invoice_id.date or invoice_id.invoice_date,
            )
        else:
            amount_total = self.tbai_get_invoice_amount_for_tax_group(invoice_id)
        return amount_total

    def tbai_get_associated_re_tax(self, invoice_id):
        re_invoice_tax = None
        tbai_maps = self.env["tbai.tax.map"].search([("code", "=", "RE")])
        s_iva_re_taxes = self.company_id.get_taxes_from_templates(
            tbai_maps.mapped("tax_template_ids")
        )
        lines = invoice_id.invoice_line_ids.filtered(lambda l: self in l.tax_ids)
        re_taxes = lines.mapped("tax_ids").filtered(lambda tax: tax in s_iva_re_taxes)
        if 1 < len(re_taxes):
            raise exceptions.ValidationError(
                _(
                    "TicketBAI Invoice %(name)s Error: Tax %(tax)s contains "
                    "multiple Equivalence Surcharge Taxes"
                )
                % {"name": invoice_id.name, "tax": self.name}
            )
        elif 1 == len(re_taxes):
            re_invoice_taxes = (
                invoice_id.invoice_line_ids.filtered(
                    lambda x: any([tax.id == re_taxes.id for tax in x.tax_ids])
                )
                .mapped("tax_ids")
                .filtered(lambda t: t in s_iva_re_taxes)
            )
            if 1 == len(re_invoice_taxes):
                re_invoice_tax = re_invoice_taxes
            else:
                raise exceptions.ValidationError(
                    _(
                        "TicketBAI Invoice %(name)s Error: the Invoice should "
                        "have one tax line for Tax %(tax)s"
                    )
                    % {"name": invoice_id.name, "tax": re_taxes.name}
                )
        return re_invoice_tax

    def tbai_get_value_tax_type(self):
        if self.tbai_es_prestacion_servicios():
            res = "service"
        elif self.tbai_es_entrega():
            res = "goods"
        else:
            res = None
        return res

    def tbai_es_prestacion_servicios(self):
        # No sujeto Repercutido (Servicios)
        # Prestación de servicios intracomunitario y extracomunitario
        # Servicios
        # Servicios Exento Repercutido
        tbai_maps = self.env["tbai.tax.map"].search(
            [("code", "in", ("SNS", "SIE", "S", "SER"))]
        )
        taxes = self.company_id.get_taxes_from_templates(
            tbai_maps.mapped("tax_template_ids")
        )
        return self in taxes

    def tbai_es_entrega(self):
        # Bienes
        # No sujeto Repercutido (Bienes)
        # Entregas Intracomunitarias y Exportaciones exentas
        # Servicios Exento Repercutido
        tbai_maps = self.env["tbai.tax.map"].search(
            [("code", "in", ("B", "BNS", "IEE", "SER"))]
        )
        taxes = self.company_id.get_taxes_from_templates(
            tbai_maps.mapped("tax_template_ids")
        )
        return self in taxes

    def tbai_get_value_causa(self, invoice_id):
        country_code = invoice_id.partner_id._parse_aeat_vat_info()[0]
        if country_code and self.env.ref("base.es").code.upper() == country_code:
            fp_not_subject_tai = invoice_id.company_id.get_fps_from_templates(
                self.env.ref("l10n_es.fp_not_subject_tai")
            )
            if (
                fp_not_subject_tai
                and fp_not_subject_tai == invoice_id.fiscal_position_id
            ):
                res = "RL"
            else:
                res = "OT"
        elif country_code:
            res = "RL"
        else:
            raise exceptions.ValidationError(
                _("Country code for partner %s not found!") % invoice_id.partner_id.name
            )
        return res

    def tbai_get_value_base_imponible(self, invoice_id):
        if invoice_id.tbai_refund_type == "I":
            sign = -1
        else:
            sign = 1
        if invoice_id.currency_id.id != invoice_id.company_id.currency_id.id:
            currency = invoice_id.currency_id
            base_balance = self.tbai_get_invoice_base_balace_for_tax_group(invoice_id)
            base = currency._convert(
                base_balance,
                invoice_id.company_id.currency_id,
                invoice_id.company_id,
                invoice_id.date or invoice_id.invoice_date,
            )
        else:
            base = self.tbai_get_invoice_base_balace_for_tax_group(invoice_id)
        return "%.2f" % (sign * base)

    def tbai_get_value_tipo_no_exenta(self):
        tbai_maps = self.env["tbai.tax.map"].search([("code", "=", "ISP")])
        isp_taxes = self.company_id.get_taxes_from_templates(
            tbai_maps.mapped("tax_template_ids")
        )
        if self in isp_taxes:
            res = "S2"
        else:
            res = "S1"
        return res

    def tbai_get_value_cuota_impuesto(self, invoice_id):
        if invoice_id.tbai_refund_type == "I":
            sign = -1
        else:
            sign = 1
        amount_total = self.tbai_get_amount_total_company(invoice_id)
        return "%.2f" % (sign * amount_total)

    def tbai_get_value_tipo_recargo_equiv(self, invoice_id):
        re_invoice_tax = self.tbai_get_associated_re_tax(invoice_id)
        if re_invoice_tax:
            res = "%.2f" % abs(re_invoice_tax.amount)
        else:
            res = None
        return res

    def tbai_get_value_cuota_recargo_equiv(self, invoice_id):
        if invoice_id.tbai_refund_type == "I":
            sign = -1
        else:
            sign = 1
        re_invoice_tax = self.tbai_get_associated_re_tax(invoice_id)
        if re_invoice_tax:
            amount_total = re_invoice_tax.tbai_get_amount_total_company(invoice_id)
            res = "%.2f" % (sign * amount_total)
        else:
            res = None
        return res

    def tbai_get_value_op_recargo_equiv_o_reg_simpl(self, invoice_id):
        re_invoice_tax = self.tbai_get_associated_re_tax(invoice_id)
        if re_invoice_tax or invoice_id.company_id.tbai_vat_regime_simplified:
            res = "S"
        else:
            res = "N"
        return res

    def tbai_get_invoice_base_balace_for_tax_group(self, invoice_id):
        base = 0
        for line in invoice_id.line_ids:
            if self.id in line.tax_ids.ids:
                base += line.price_subtotal
        return base

    def tbai_get_invoice_amount_for_tax_group(self, invoice_id):
        amount = 0
        for line in invoice_id.line_ids:
            if self.id in line.tax_ids.ids:
                amount += line.price_subtotal * self.amount / 100
        return amount
