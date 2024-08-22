# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import odoo


def migrate(cr, version):
    """Actualizamos aeat_simplified_invoice por el valor de lroe_simplified_invoice porque
    si se está actualizando ticketbai/batuz tiene prioridad frente a otros modulos que
    usan este campo, como por ejemplo el SII"""
    if not version:
        return
    env = odoo.api.Environment(cr, odoo.SUPERUSER_ID, {})
    env.cr.execute(
        """
        UPDATE res_partner
        SET aeat_simplified_invoice = lroe_simplified_invoice;"""
    )
