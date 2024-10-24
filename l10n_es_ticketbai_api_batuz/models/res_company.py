# Copyright 2021 Binovo IT Human Project SL
# Copyright 2021 Digital5, S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    lroe_model = fields.Selection(
        [
            ("240", "LROE PJ 240"),
            ("140", "LROE PF 140"),
        ],
        string="LROE Model",
        required=True,
        default="240",
    )
    main_activity_iae = fields.Char(
        string="Epígrafe I.A.E. actividad principal",
        size=7,
    )
