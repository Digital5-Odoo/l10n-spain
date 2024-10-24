# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import odoo


def migrate(cr, version):
    """Trasladamos valor de cancelled_invoice_id a invoice_id en tbai_invoice.
    Despues recalculamos tbai_invoice_id de account_move para establecer
     la última tbai_invoice generada por esa factura"""
    if not version:
        return
    env = odoo.api.Environment(cr, odoo.SUPERUSER_ID, {})
    env.cr.execute(
        """
        UPDATE tbai_invoice
        SET invoice_id = cancelled_invoice_id
        WHERE cancelled_invoice_id IS NOT NULL;"""
    )
    env.cr.execute(
        """
        WITH last_tbai_invoice AS (
            SELECT DISTINCT ON (invoice_id) invoice_id, id, schema
            FROM tbai_invoice
            WHERE invoice_id IS NOT NULL
            ORDER BY invoice_id, create_date DESC
        )
        UPDATE account_move am
        SET tbai_invoice_id = lti.id
        FROM last_tbai_invoice lti
        WHERE (am.tbai_invoice_id IS NOT NULL OR am.tbai_cancellation_id IS NOT NULL);"""
    )
