# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openupgradelib import openupgrade


def migrate(cr, version):
    """Actualizamos aeat_identification_type y aeat_identification porque si se está
    actualizando ticketbai tiene prioridad frente a otros modulos que usan estos campos,
    como por ejemplo el SII"""
    if not version:
        return
    if openupgrade.column_exists(
        cr, "res_partner", "tbai_partner_idtype"
    ) and openupgrade.column_exists(
        cr, "res_partner", "tbai_partner_identification_number"
    ):
        cr.execute(
            """
            UPDATE res_partner
            SET
                aeat_identification_type = tbai_partner_idtype,
                aeat_identification = tbai_partner_identification_number
            WHERE tbai_partner_idtype IN ('03', '05', '06')
                AND tbai_partner_identification_number IS NOT NULL;"""
        )
