# Copyright 2021 Binovo IT Human Project SL
# Copyright 2021 Landoo Sistemas de Informacion SL
# Copyright 2024 Digital5, S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models


class AeatTaxAgency(models.Model):
    _inherit = "aeat.tax.agency"

    tbai_version = fields.Char(
        string="TicketBAI version",
    )
    tbai_qr_base_url = fields.Char(
        string="QR Base URL",
    )
    tbai_test_qr_base_url = fields.Char(
        string="Test QR Base URL",
    )
    tbai_rest_url_invoice = fields.Char(
        string="REST API URL for Invoices",
    )
    tbai_test_rest_url_invoice = fields.Char(
        string="Test - REST API URL for Invoices",
    )
    tbai_rest_url_cancellation = fields.Char(
        string="REST API URL for Invoice Cancellations",
    )
    tbai_test_rest_url_cancellation = fields.Char(
        string="Test - REST API URL for Invoice Cancellations",
    )
    tbai_sign_file_url = fields.Char(string="Sign File URL")
    tbai_sign_file_hash = fields.Char(string="Sign File HASH")
