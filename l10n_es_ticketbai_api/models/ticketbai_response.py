# Copyright 2020 Binovo IT Human Project SL
# Copyright 2021 Landoo Sistemas de Informacion SL
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import base64

from odoo import _, api, fields, models

from ..ticketbai.xml_schema import XMLSchema


class TicketBaiResponse(models.Model):
    _name = "tbai.response"
    _order = "id desc"
    _description = "TicketBAI Tax Agency Invoice response"

    tbai_invoice_id = fields.Many2one(
        comodel_name="tbai.invoice", required=True, ondelete="cascade"
    )
    xml = fields.Binary(string="XML Response", attachment=True)
    xml_fname = fields.Char("File Name")
    state = fields.Selection(
        string="Status",
        selection=[
            ("00", "Received"),
            ("01", "Rejected"),
            ("-1", "Request error"),
            ("-2", "Build error"),
        ],
        required=True,
    )
    tbai_response_message_ids = fields.One2many(
        comodel_name="tbai.response.message", inverse_name="tbai_response_id"
    )

    @api.model
    def prepare_tbai_api_error_values(self, msg):
        values = {}
        values.update(
            {
                "state": "-2",
                "tbai_response_message_ids": [
                    (
                        0,
                        0,
                        {
                            "code": _("TicketBAI API required fields missing."),
                            "description": msg,
                        },
                    )
                ],
            }
        )
        return values

    @api.model
    def prepare_tbai_response_values(self, response):
        values = {}
        if response.error:
            errno = response.errno
            strerror = response.strerror
            values.update(
                {
                    "state": "-1",
                    "tbai_response_message_ids": [
                        (0, 0, {"code": errno, "description": strerror})
                    ],
                }
            )
        else:
            xml_dict = (
                XMLSchema("TicketBaiResponse").parse_xml(response.data)[
                    "TicketBaiResponse"
                ]
                or {}
            )
            state = xml_dict["Salida"]["Estado"]
            values.update(
                {
                    "xml": base64.encodebytes(response.data.encode("utf-8")),
                    "state": state,
                }
            )
            tbai_response_message_ids = []
            if state == "00":
                if xml_dict.get("Salida").get("CSV"):
                    tbai_response_message_ids = [
                        (
                            0,
                            0,
                            {
                                "code": xml_dict["Salida"]["CSV"],
                                "description": {
                                    "es_ES": xml_dict["Salida"]["Descripcion"],
                                    "eu_ES": xml_dict["Salida"]["Azalpena"],
                                },
                            },
                        )
                    ]
                messages = xml_dict.get("Salida").get("ResultadosValidacion", False)
                if messages:
                    if isinstance(messages, dict):
                        messages = [messages]
                    for msg in messages:
                        tbai_response_message_ids.append(
                            (
                                0,
                                0,
                                {
                                    "code": msg["Codigo"],
                                    "description": {
                                        "es_ES": msg["Descripcion"],
                                        "eu_ES": msg["Azalpena"],
                                    },
                                },
                            )
                        )
            elif state == "01":
                messages = xml_dict["Salida"]["ResultadosValidacion"]
                if isinstance(messages, dict):
                    messages = [messages]
                for msg in messages:
                    tbai_response_message_ids.append(
                        (
                            0,
                            0,
                            {
                                "code": msg["Codigo"],
                                "description": {
                                    "es_ES": msg["Descripcion"],
                                    "eu_ES": msg["Azalpena"],
                                },
                            },
                        )
                    )
            else:
                tbai_response_message_ids.append(
                    (
                        0,
                        0,
                        {
                            "code": state,
                            "description": _("Unknown TicketBAI response code."),
                        },
                    )
                )
            values.update(tbai_response_message_ids=tbai_response_message_ids)
        return values


class TicketBaiResponseMessage(models.Model):
    _name = "tbai.response.message"
    _description = "TicketBAI Tax Agency Invoice response messages"

    tbai_response_id = fields.Many2one(
        comodel_name="tbai.response", required=True, ondelete="cascade"
    )
    code = fields.Char(required=True)
    description = fields.Char(required=True, translate=True)

    @api.depends("code", "description")
    def name_get(self):
        result = []
        for msg in self:
            name = "{} - {}".format(msg.code, msg.description)
            result.append((msg.id, name))
        return result

    @api.model_create_multi
    def create(self, vals_list):
        description_basque_translation_list = []
        for vals in vals_list:
            if "description" in vals and isinstance(vals["description"], dict):
                description = vals["description"]["es_ES"]
                description_basque_translation_list.append(vals["description"]["eu_ES"])
                vals["description"] = description
            else:
                description_basque_translation_list.append("")
        records = super().create(vals_list)
        lang = self.env["res.lang"].search([("code", "=", "eu_ES")], limit=1)
        if lang:
            for record, descrip_basque_translation in zip(
                records, description_basque_translation_list
            ):
                if not descrip_basque_translation:
                    continue
                record.with_context(
                    lang="eu_ES"
                ).description = descrip_basque_translation
        return records
