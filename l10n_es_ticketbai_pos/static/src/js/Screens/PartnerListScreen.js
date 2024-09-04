/* Copyright 2021 Binovo IT Human Project SL
   Copyright 2022 Landoo Sistemas de Informacion SL
   Copyright 2022 Advanced Programming Solutions SL (APSL)
   License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
*/

odoo.define("l10n_es_ticketbai_pos.PartnerListScreen", function (require) {
    "use strict";

    const PartnerListScreen = require("point_of_sale.PartnerListScreen");
    const Registries = require("point_of_sale.Registries");

    // eslint-disable-next-line no-shadow
    const L10nEsTicketBaiPartnerListScreen = (PartnerListScreen) =>
        class extends PartnerListScreen {
            confirm() {
                var res = true;
                if (this.env.pos.company.tbai_enabled && this.state.selectedPartner) {
                    var order = this.env.pos.get_order();
                    var partner = this.state.selectedPartner;
                    if (!order.is_customer_anonymous(partner)) {
                        res = order.check_customer_tbai(partner);
                    }
                }
                if (res) {
                    super.confirm();
                }
            }
        };

    Registries.Component.extend(PartnerListScreen, L10nEsTicketBaiPartnerListScreen);
    return PartnerListScreen;
});
