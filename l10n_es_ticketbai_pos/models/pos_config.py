# Copyright 2021 Binovo IT Human Project SL
# Copyright 2022 Landoo Sistemas de Informacion SL
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, exceptions, fields, models


class PosConfig(models.Model):
    _inherit = "pos.config"

    tbai_enabled = fields.Boolean(related="company_id.tbai_enabled", readonly=True)
    tbai_last_invoice_id = fields.Many2one(
        string="Last TicketBAI Invoice sent", comodel_name="tbai.invoice", copy=False
    )
    iface_l10n_es_simplified_invoice = fields.Boolean(default=True)

    def open_ui(self):
        self.ensure_one()
        if self.tbai_enabled:
            if not self.is_simplified_config:
                raise exceptions.ValidationError(
                    _("Simplified Invoice IDs Sequence is required")
                )
        return super().open_ui()

    def _open_session(self, session_id):
        self.ensure_one()
        if self.tbai_enabled and not self.is_simplified_config:
            raise exceptions.ValidationError(
                _("Simplified Invoice IDs Sequence is required")
            )
        return super()._open_session(session_id)
