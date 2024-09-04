odoo.define("l10n_es_ticketbai_pos.PartnerDetailsEdit", function (require) {
    "use strict";

    const PartnerDetailsEdit = require("point_of_sale.PartnerDetailsEdit");
    const Registries = require("point_of_sale.Registries");
    const {useState} = owl;

    // eslint-disable-next-line no-shadow
    const L10nEsTicketBaiPartnerDetailsEdit = (PartnerDetailsEdit) =>
        class extends PartnerDetailsEdit {
            setup() {
                super.setup();
                this.changes = useState({
                    ...this.changes,
                    aeat_anonymous_cash_customer:
                        this.props.partner.aeat_anonymous_cash_customer || null,
                });
            }
        };
    Registries.Component.extend(PartnerDetailsEdit, L10nEsTicketBaiPartnerDetailsEdit);
    return PartnerDetailsEdit;
});
