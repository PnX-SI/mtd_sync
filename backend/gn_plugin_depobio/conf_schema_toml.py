from marshmallow import Schema, fields


class DemarchesSimplifiees(Schema):
    URL = fields.String(load_default="https://www.demarches-simplifiees.fr/api/v2/graphql")
    TOKEN = fields.String()
    LIBELLE_ID = fields.String(load_default="Q2hhbXAtMTE0NzQ4")
    DESCRIPTION_ID = fields.String(load_default="Q2hhbXAtMTE0NzQ5")
    DATE_FIN_ID = fields.String(load_default="Q2hhbXAtMTE0Nzgy")


class GnModuleSchemaConf(Schema):
    MAIL_SUBJECT_AF_CLOSED_BASE = fields.String(load_default="")
    MAIL_CONTENT_AF_CLOSED_ADDITION = fields.String(load_default="")
    MAIL_CONTENT_AF_CLOSED_PDF = fields.String(load_default="")
    MAIL_CONTENT_AF_CLOSED_GREETINGS = fields.String(load_default="")
    DEMARCHES_SIMPLIFIEES = fields.Nested(
        DemarchesSimplifiees, load_default=DemarchesSimplifiees().load({})
    )
