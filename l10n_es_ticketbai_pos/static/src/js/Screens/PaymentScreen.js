/* Copyright 2021 Binovo IT Human Project SL
   Copyright 2022 Landoo Sistemas de Informacion SL
   Copyright 2022 Advanced Programming Solutions SL (APSL)
   License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
*/

odoo.define("l10n_es_ticketbai_pos.PaymentScreen", function (require) {
    "use strict";

    const PaymentScreen = require("point_of_sale.PaymentScreen");
    const Registries = require("point_of_sale.Registries");
    const session = require("web.session");

    // eslint-disable-next-line no-shadow
    const L10nEsTicketBaiPaymentScreen = (PaymentScreen) =>
        // eslint-disable-next-line no-shadow
        class L10nEsTicketBaiPaymentScreen extends PaymentScreen {
            async _isOrderValid() {
                var res = await super._isOrderValid(...arguments);
                if (this.env.pos.company.tbai_enabled && res === true) {
                    var order = this.currentOrder;
                    var partner = this.currentOrder.get_partner();
                    // Checks customer
                    if (!order.is_customer_anonymous(partner)) {
                        res = order.check_customer_tbai(partner);
                    }
                    // Checks productos
                    if (!order.check_products_have_taxes()) {
                        res = false;
                        this.showPopup("ErrorPopup", {
                            title: this.env._t("TicketBAI"),
                            body: this.env._t(
                                "At least one product does not have a tax."
                            ),
                        });
                    }
                }
                return res;
            }
            async _postPushOrderResolve(order, order_server_ids) {
                try {
                    if (this.env.pos.company.tbai_enabled) {
                        var result = await this.rpc({
                            model: "pos.order",
                            method: "search_read",
                            domain: [["id", "in", order_server_ids]],
                            fields: ["tbai_identifier", "tbai_qr_src"],
                            context: session.user_context,
                        });
                        order.set_l10n_es_ticketbai_identifier(
                            result[0].tbai_identifier || false
                        );
                        order.set_l10n_es_ticketbai_qr(result[0].tbai_qr_src || false);
                    }
                } finally {
                    // eslint-disable-next-line no-unsafe-finally
                    return super._postPushOrderResolve(...arguments);
                }
            }
        };

    Registries.Component.extend(PaymentScreen, L10nEsTicketBaiPaymentScreen);

    return PaymentScreen;
});
