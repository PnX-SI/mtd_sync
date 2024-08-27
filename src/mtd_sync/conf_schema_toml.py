from marshmallow import Schema, fields, post_load


class GnModuleSchemaConf(Schema):
    BASE_URL = fields.String(load_default="")
    XML_NAMESPACE = fields.String(load_default="{http://inpn.mnhn.fr/mtd}")
    USER = fields.String(load_default="")
    PASSWORD = fields.String(load_default="")
    ID_INSTANCE_FILTER = fields.Integer(load_default=None)
    MTD_API_ENDPOINT = fields.Url(load_default="https://preprod-inpn.mnhn.fr/mtd")
    SYNC_LOG_LEVEL = fields.String(load_default="INFO")
    USERS_CAN_SEE_ORGANISM_DATA = fields.Boolean(load_default=False)
    JDD_MODULE_CODE_ASSOCIATION = fields.List(fields.String, load_default=["OCCTAX", "OCCHAB"])
    ID_PROVIDER_INPN = fields.String(load_default="cas_inpn")
    ID_USER_SOCLE_1 = fields.Integer(load_default=1)
    ID_USER_SOCLE_2 = fields.Integer(load_default=2)
