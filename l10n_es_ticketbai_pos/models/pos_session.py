# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class PosSession(models.Model):
    _inherit = "pos.session"

    def _loader_params_res_company(self):
        res = super()._loader_params_res_company()
        res["search_params"]["fields"] += ["tbai_enabled"]
        return res

    def _loader_params_res_partner(self):
        res = super()._loader_params_res_partner()
        res["search_params"]["fields"] += [
            "country_code",
            "aeat_anonymous_cash_customer",
        ]
        return res
