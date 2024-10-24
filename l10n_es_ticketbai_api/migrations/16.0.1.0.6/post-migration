# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    if not version:
        return
    openupgrade.logged_query(
        env.cr, """
        UPDATE tbai_invoice AS ti
        SET partner_id = am.commercial_partner_id
        FROM account_move AS am
        WHERE ti.invoice_id IS NOT NULL AND ti.invoice_id = am.id;
        """)
