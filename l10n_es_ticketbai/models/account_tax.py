# Copyright 2020 Binovo IT Human Project SL
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import models


class AccountTax(models.Model):
    _inherit = 'account.tax'

    def tbai_is_subject_to_tax(self):
        s_iva_ns_tbai_maps = self.env["tbai.tax.map"].search(
            [('code', 'in', ("SNS", "BNS"))]
        )
        s_iva_ns_taxes = self.env["l10n.es.aeat.report"].get_taxes_from_templates(
            s_iva_ns_tbai_maps.mapped("tax_template_ids")
        )
        return self not in s_iva_ns_taxes

    def tbai_is_tax_exempted(self):
        map_ids = self.env["tbai.tax.map"].search([("code", "in", ["IEE", "SER"])])
        tax_ids = self.env["l10n.es.aeat.report"].new(
            {'company_id': self.company_id.id}
        ).get_taxes_from_templates(map_ids.mapped("tax_template_ids"))
        return self in tax_ids

    def tbai_is_not_tax_exempted(self):
        map_ids = self.env["tbai.tax.map"].search([("code", "in", ["IEE", "SER"])])
        tax_ids = self.env["l10n.es.aeat.report"].new(
            {'company_id': self.company_id.id}
        ).get_taxes_from_templates(map_ids.mapped("tax_template_ids"))
        return self not in tax_ids
