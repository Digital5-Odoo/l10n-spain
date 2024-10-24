# Copyright 2021 Binovo IT Human Project SL
# Copyright 2021 Landoo Sistemas de Informacion SL
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.tests.common import tagged

from odoo.addons.l10n_es_ticketbai_api.ticketbai.xml_schema import XMLSchema

from .common import TestL10nEsTicketBAI


@tagged("post_install", "-at_install")
class TestL10nEsTicketBAICustomerCancellation(TestL10nEsTicketBAI):
    def setUp(self):
        super().setUp()

    def test_out_invoice_cancel(self):
        invoice = self.create_draft_invoice(
            self.account_billing.id, self.fiscal_position_national, self.partner.id
        )
        invoice.onchange_fiscal_position_id_tbai_vat_regime_key()
        invoice.action_post()
        self.assertEqual(invoice.state, "posted")
        self.assertEqual(1, len(invoice.tbai_invoice_ids))
        (
            root,
            signature_value,
        ) = invoice.sudo().tbai_invoice_ids.get_tbai_xml_signed_and_signature_value()
        res = XMLSchema.xml_is_valid(self.test_xml_invoice_schema_doc, root)
        self.assertTrue(res)
        invoice.sudo().tbai_invoice_ids.state = "sent"
        invoice.button_cancel()
        self.assertEqual(invoice.state, "cancel")
        tbai_cancel_invs = invoice.sudo().tbai_invoice_ids.filtered(
            lambda tbai: tbai.schema == "AnulaTicketBai"
        )
        self.assertEqual(1, len(tbai_cancel_invs))
        (
            root,
            signature_value,
        ) = tbai_cancel_invs.get_tbai_xml_signed_and_signature_value()
        res = XMLSchema.xml_is_valid(self.test_xml_cancellation_schema_doc, root)
        self.assertTrue(res)

    def test_out_invoice_cancel_not_sent_invoice(self):
        self.main_company.tbai_enabled = False
        invoice = self.create_draft_invoice(
            self.account_billing.id, self.fiscal_position_national, self.partner.id
        )
        invoice.onchange_fiscal_position_id_tbai_vat_regime_key()
        invoice.action_post()
        self.assertEqual(invoice.state, "posted")
        self.assertEqual(0, len(invoice.tbai_invoice_ids))
        self.main_company.tbai_enabled = True
        invoice.button_cancel()
        self.assertEqual(invoice.state, "cancel")
        tbai_cancel_invs = invoice.sudo().tbai_invoice_ids.filtered(
            lambda tbai: tbai.schema == "AnulaTicketBai"
        )
        self.assertEqual(0, len(tbai_cancel_invs))
