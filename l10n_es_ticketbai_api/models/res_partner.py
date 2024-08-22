# Copyright 2021 Binovo IT Human Project SL
# Copyright 2021 Landoo Sistemas de Informacion SL
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from collections import OrderedDict

from odoo import _, exceptions, models

from ..utils import utils as tbai_utils


class ResPartner(models.Model):
    _inherit = "res.partner"

    def tbai_get_partner_country_code(self):
        country_code = self.commercial_partner_id._parse_aeat_vat_info()[0]
        if not country_code:
            raise exceptions.ValidationError(
                _("The invoice customer %s does not have a valid country assigned.")
                % self.name
            )
        return country_code.upper()

    def tbai_get_value_apellidos_nombre_razon_social(self):
        """V 1.2
        <element name="ApellidosNombreRazonSocial" type="T:TextMax120Type"/>
            <maxLength value="120"/>
        :return: Name and surname, or business name
        """
        name = self.commercial_partner_id.name
        return name.strip()[:120]  # Remove leading and trailing whitespace

    def tbai_build_id_otro(self):
        """V 1.2
        <complexType name="IDOtro">
            <sequence>
                <element name="CodigoPais" type="T:CountryType2" minOccurs="0"/>
                <element name="IDType" type="T:IDTypeType"/>
                <element name="ID" type="T:TextMax20Type"/>
            </sequence>
        </complexType>
        """
        self.ensure_one()
        partner = self.commercial_partner_id
        res = OrderedDict()
        (
            country_code,
            identifier_type,
            identifier,
        ) = partner._parse_aeat_vat_info()
        res = OrderedDict(
            [
                ("CodigoPais", country_code),
                ("IDType", identifier_type or "02"),
                (
                    "ID",
                    country_code + identifier
                    if partner._map_aeat_country_code(country_code)
                    in partner._get_aeat_europe_codes()
                    else identifier,
                ),
            ]
        )
        return res

    def tbai_get_value_nif(self):
        """V 1.2
        <element name="NIF" type="T:NIFType"/>
            <length value="9" />
            <pattern value="(([a-z|A-Z]{1}\\d{7}[a-z|A-Z]{1})|(\\d{8}[a-z|A-Z]{1})|
            ([a-z|A-Z]{1}\\d{8}))" />
        :return: VAT Number for Customers from Spain or the Company associated partner.
        """
        (
            country_code,
            identifier_type,
            vat_number,
        ) = self.commercial_partner_id._parse_aeat_vat_info()
        if (
            vat_number
            and country_code
            and self.env.ref("base.es").code.upper() == country_code
            and identifier_type in ("02", "")
        ):
            tbai_utils.check_spanish_vat_number(
                _("%s VAT Number") % self.name, vat_number
            )
            res = vat_number
        else:
            res = ""
        return res

    def tbai_get_value_direccion(self):
        """V 1.2
        <element name="Direccion" type="T:TextMax250Type" minOccurs="0"/>
            <maxLength value="250"/>
        """
        address_fields = [
            "%s" % (self.street or ""),
            "%s" % (self.street2 or ""),
            ("{} {}".format(self.zip or "", self.city or "")).strip(),
            "%s" % (self.state_id.name or ""),
            "%s" % (self.country_id.name or ""),
        ]
        return ", ".join([x for x in address_fields if x])
