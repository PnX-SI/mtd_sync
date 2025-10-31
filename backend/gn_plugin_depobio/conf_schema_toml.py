from marshmallow import Schema, fields


class GnModuleSchemaConf(Schema):
    MAIL_SUBJECT_AF_CLOSED_BASE = fields.String(load_default="")
    MAIL_CONTENT_AF_CLOSED_ADDITION = fields.String(load_default="")
    MAIL_CONTENT_AF_CLOSED_PDF = fields.String(load_default="")
    MAIL_CONTENT_AF_CLOSED_GREETINGS = fields.String(load_default="")

    DEMARCHE_SIMPLIFIEES_URL = fields.String(required=True)
    DEMARCHE_SIMPLIFIEES_TOKEN = fields.String(required=True)
