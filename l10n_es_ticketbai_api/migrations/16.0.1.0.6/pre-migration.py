# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import odoo


def migrate(cr, version):
    """Actualizamos aeat_identification_type y aeat_identification porque si se está
    actualizando ticketbai tiene prioridad frente a otros modulos que usan estos campos,
    como por ejemplo el SII"""
    if not version:
        return
    env = odoo.api.Environment(cr, odoo.SUPERUSER_ID, {})
    env.cr.execute(
        """
        UPDATE res_partner
        SET
            aeat_identification_type = tbai_partner_idtype,
            aeat_identification = tbai_partner_identification_number
        WHERE tbai_partner_idtype IN ('03', '05', '06')
            AND tbai_partner_identification_number IS NOT NULL;"""
    )
