#  Copyright 2021 Landoo Sistemas de Informacion SL
#  License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class AccountJournal(models.Model):
    _inherit = 'account.journal'

    tbai_enabled = fields.Boolean(
        related='company_id.tbai_enabled', readonly=True)

    tbai_send_invoice = fields.Boolean(
        string='Send TicketBAI invoices to tax agency', default=True)

    tbai_active_date = fields.Date(
        string="TicketBAI active date",
        help="Start date for sending invoices to the tax authorities",
        default=fields.Date.from_string("2022-01-01"))
    tbai_invoice_issuer = fields.Selection(
        selection=[
            ("N", "Invoice issued by the issuer itself"),
            # Factura emitida por el propio emisor
            ("T", "Invoice issued by a third party"),
            # Factura emitida por tercero
            ("D", "Invoice issued by recipient"),
            # Factura emitida por destinatario
        ],
        default="N",
        string="TicketBai: Invoice issuer",
        # TicketBai: Emisor de la factura
        copy=False,
        required=True,
    )

    @api.onchange('refund_sequence')
    def onchange_refund_sequence(self):
        if not self.refund_sequence and self.type == 'sale':
            self.refund_sequence = True

    @api.onchange('type')
    def onchange_type(self):
        if self.type == 'sale':
            self.refund_sequence = True

    @api.onchange('tbai_send_invoice')
    def onchange_tbai_send_invoice(self):
        if not self.tbai_send_invoice:
            tbai_invoices = self.env["account.invoice"].search(
                [('journal_id', '=', self._origin.id),
                 ('tbai_invoice_id', '!=', False)]
            )
            if len(tbai_invoices) > 0:
                raise UserError(_('You cannot stop sending invoices from this'
                                  ' journal, an invoice has already been sent.'))
