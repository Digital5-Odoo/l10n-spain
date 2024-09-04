# Copyright 2021 Binovo IT Human Project SL
# Copyright 2022 Landoo Sistemas de Informacion SL
# Copyright 2022 Advanced Programming Solutions SL
# Copyright 2024 Digital5 SL
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import models


class AccountMove(models.Model):
    _inherit = "account.move"

    def tbai_prepare_invoice_values(self):
        res = super().tbai_prepare_invoice_values()
        if not res.get("vat_regime_key", False):
            res["vat_regime_key"] = (
                self.env["tbai.vat.regime.key"]
                .search([("code", "=", "01")], limit=1)
                .code
            )
        # Refund original simplified invoices
        if res.get("substitutes_simplified_invoice", "N") == "S":
            tbai_invoice_refund_ids = []
            po_to_refund = self.tbai_get_factura_emitida_simplificada_sustituida()
            for refunded_pos_order in po_to_refund:
                tbai_invoice_refund_ids.append(
                    (
                        0,
                        0,
                        {
                            "number_prefix": (
                                refunded_pos_order.tbai_get_value_serie_factura()
                            ),
                            "number": (refunded_pos_order.tbai_get_value_num_factura()),
                            "expedition_date": (
                                refunded_pos_order.tbai_get_value_fecha_exp_factura()
                            ),
                        },
                    )
                )
            if tbai_invoice_refund_ids:
                res.update(
                    {
                        "is_invoice_refund": False,
                        "tbai_invoice_refund_ids": tbai_invoice_refund_ids,
                    }
                )
        return res

    def tbai_get_factura_emitida_simplificada_sustituida(self):
        return self.pos_order_ids.filtered(
            lambda po: po.tbai_invoice_id
            and po.tbai_invoice_id.state not in ("cancel", "error")
        )

    def tbai_get_value_factura_emitida_sustitucion_simplificada(self):
        po_to_refund = self.tbai_get_factura_emitida_simplificada_sustituida()
        if po_to_refund:
            return "S"
        return super().tbai_get_value_factura_emitida_sustitucion_simplificada()

    def _post(self, soft=True):
        # For Ticketbai is mandatory to specify origin invoice in refunds
        def set_reverse_entries(self):
            for invoice in self:
                pos_order_ids = invoice.sudo().pos_order_ids
                for pos_order in pos_order_ids:
                    pos_refunded_orders = pos_order.refunded_order_ids
                    for refunded_order_id in pos_refunded_orders:
                        refunded_invoice_id = refunded_order_id.account_move
                        invoice.reversed_entry_id = refunded_invoice_id.id

        set_reverse_entries(self)
        res = super()._post(soft)
        return res
