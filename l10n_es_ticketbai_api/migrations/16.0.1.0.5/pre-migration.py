# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

# flake8: noqa: B950

import odoo


def migrate(cr, version):
    if not version:
        return
    env = odoo.api.Environment(cr, odoo.SUPERUSER_ID, {})
    tax_agency_map = {
        "l10n_es_ticketbai_api.tbai_tax_agency_gipuzkoa": "l10n_es_aeat.aeat_tax_agency_gipuzkoa",
        "l10n_es_ticketbai_api.tbai_tax_agency_araba": "l10n_es_aeat.aeat_tax_agency_araba",
        "l10n_es_ticketbai_api_batuz.tbai_tax_agency_bizkaia": "l10n_es_aeat.aeat_tax_agency_bizkaia",
    }
    env.cr.execute(
        """
        SELECT
            rc.id,
            imd.module || '.' || imd.name
        FROM res_company AS rc
        INNER JOIN ir_model_data AS imd ON imd.model = 'tbai.tax.agency' AND res_id = rc.tbai_tax_agency_id
        WHERE rc.tbai_tax_agency_id IS NOT NULL;
    """
    )
    for company_id, tbai_tax_agency_xmlid in env.cr.fetchall():
        aeat_tax_agency_xmlid = tax_agency_map.get(tbai_tax_agency_xmlid, "")
        if not aeat_tax_agency_xmlid:
            continue
        tax_agency = env.ref(aeat_tax_agency_xmlid, raise_if_not_found=False)
        if tax_agency:
            env.cr.execute(
                """
                UPDATE res_company
                SET tax_agency_id = %s
                WHERE id = %s;""",
                (
                    tax_agency.id,
                    company_id,
                ),
            )
