# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import odoo


def migrate(cr, version):
    if not version:
        return
    env = odoo.api.Environment(cr, odoo.SUPERUSER_ID, {})
    for lroe in env["lroe.operation"].search([]):
        lroe._compute_api_url()
