odoo.define("l10n_es_ticketbai_pos.models", function (require) {
    "use strict";

    const {Order} = require("point_of_sale.models");
    var {Gui} = require("point_of_sale.Gui");
    const Registries = require("point_of_sale.Registries");
    var core = require("web.core");
    var _t = core._t;

    // eslint-disable-next-line no-shadow
    const OverloadOrder = (Order) =>
        // eslint-disable-next-line no-shadow
        class OverloadOrder extends Order {
            export_for_printing() {
                const result = super.export_for_printing(...arguments);
                result.company.tbai_enabled = this.pos.company.tbai_enabled;
                result.tbai_identifier = this.get_l10n_es_ticketbai_identifier();
                result.tbai_qr_src = this.get_l10n_es_ticketbai_qr();
                return result;
            }
            init_from_JSON(json) {
                super.init_from_JSON(...arguments);
                this.tbai_identifier = json.tbai_identifier;
                this.tbai_qr_src = json.tbai_qr_src;
            }
            export_as_JSON() {
                const result = super.export_as_JSON(...arguments);
                result.tbai_identifier = this.get_l10n_es_ticketbai_identifier();
                result.tbai_qr_src = this.get_l10n_es_ticketbai_qr();
                return result;
            }
            // Customer-partner checks
            is_customer_anonymous(client) {
                var customer = client || this.get_partner();
                return (customer && customer.aeat_anonymous_cash_customer) || true;
            }
            check_customer_tbai(client) {
                var partner = client || this.get_partner();
                var res = true;
                if (!this.check_customer_country(partner)) {
                    res = false;
                    Gui.showPopup("ErrorPopup", {
                        title: _t("TicketBAI"),
                        body: _.str.sprintf(
                            _t(
                                "Please set Country for customer %s or mark as anonymous cash customer."
                            ),
                            partner.name
                        ),
                    });
                } else if (!this.check_customer_simplified_invoice_spanish(partner)) {
                    res = false;
                    Gui.showPopup("ErrorPopup", {
                        title: _t("TicketBAI"),
                        body: _t(
                            "Non spanish customers are not supported for Simplified Invoice."
                        ),
                    });
                } else if (!this.check_customer_vat(partner)) {
                    res = false;
                    Gui.showPopup("ErrorPopup", {
                        title: _t("TicketBAI"),
                        body: _.str.sprintf(
                            _t(
                                "Please set VAT or TicketBAI Partner Identification Number for customer %s."
                            ),
                            partner.name
                        ),
                    });
                }
                return res;
            }
            check_customer_country(customer) {
                return !(!customer || (customer && !customer.country_id));
            }
            check_customer_simplified_invoice_spanish(customer) {
                var ok = true;
                if (customer !== null) {
                    ok = this.check_customer_country(customer);
                    if (ok) {
                        var country_code = customer.country_code;
                        if (country_code !== "ES" && !this.to_invoice) {
                            ok = false;
                        }
                    }
                }
                return ok;
            }
            check_customer_vat(customer) {
                var ok = true;
                if (customer !== null) {
                    ok = this.check_customer_country(customer);
                    if (ok) {
                        if (customer.country_code === "ES") {
                            if (!customer.vat) {
                                ok = false;
                            }
                        }
                    }
                }
                return ok;
            }
            // Product checks
            check_products_have_taxes() {
                var orderLines = this.get_orderlines();
                var line = null;
                var taxes = null;
                var all_products_have_one_tax = true;
                var i = 0;
                while (all_products_have_one_tax && i < orderLines.length) {
                    line = orderLines[i];
                    taxes = line.get_taxes();
                    if (taxes.length !== 1) {
                        all_products_have_one_tax = false;
                    }
                    i++;
                }
                return all_products_have_one_tax;
            }
            // Misc
            get_l10n_es_ticketbai_identifier() {
                return this.tbai_identifier;
            }
            set_l10n_es_ticketbai_identifier(identifier) {
                this.tbai_identifier = identifier;
            }
            get_l10n_es_ticketbai_qr() {
                return this.tbai_qr_src;
            }
            set_l10n_es_ticketbai_qr(qr) {
                this.tbai_qr_src = qr;
            }
            wait_for_push_order() {
                var result = super.wait_for_push_order(...arguments);
                result = Boolean(result || this.pos.company.tbai_enabled);
                return result;
            }
            _get_qr_code_data() {
                if (this.pos.company.tbai_enabled) {
                    return false;
                }
                return super._get_qr_code_data(...arguments);
            }
        };

    Registries.Model.extend(Order, OverloadOrder);
});
