# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    if not version:
        return
    openupgrade.logged_query(
        env.cr, """DELETE FROM ir_model_fields WHERE model = 'tbai.invoice.customer';"""
    )
    openupgrade.logged_query(
        env.cr,
        """DELETE FROM ir_model_constraint
        WHERE model =
        (SELECT id FROM ir_model WHERE model = 'tbai.invoice.customer');""",
    )
    openupgrade.logged_query(
        env.cr,
        """DELETE FROM ir_model_relation
         WHERE model = (SELECT id FROM ir_model WHERE model = 'tbai.invoice.customer');""",
    )
    openupgrade.logged_query(
        env.cr, """DELETE FROM ir_model WHERE model = 'tbai.invoice.customer';"""
    )
