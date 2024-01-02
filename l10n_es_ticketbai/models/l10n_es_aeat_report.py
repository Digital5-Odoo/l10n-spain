# -*- coding: utf-8 -*-

from odoo import _, api, fields, models


class L10nEsAeatReport(models.AbstractModel):
    _inherit = "l10n.es.aeat.report"

    def get_taxes_from_templates(self, tax_templates, **kwargs):
        """Propagamos la company que nos venga en kwargs porque con sudo()
        especialmente en ticketbai, se coge la company del usuario admin y no se mapean
        los impuestos correctamente."""
        if not kwargs.get('invoice_company_id', False):
            return super().get_taxes_from_templates(tax_templates, **kwargs)
        company_id = kwargs.get('invoice_company_id')
        tax_ids = [self._get_tax_id_from_tax_template(tmpl, company_id)
                   for tmpl in tax_templates]
        return self.env['account.tax'].browse(tax_ids)
