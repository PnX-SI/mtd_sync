from flask import Blueprint

from geonature.core.gn_meta.models import TAcquisitionFramework
from geonature.utils.env import db
from geonature.utils.errors import GeoNatureError
from geonature.core.gn_permissions import decorators as permissions
from utils_flask_sqla.response import json_resp
from gql.transport.exceptions import TransportQueryError
from werkzeug.exceptions import Forbidden, NotFound
from .demarches_simplifiees import DemarchesSimplifieesConnection, ErrorCode
from .mail_builder import MailBuilder

blueprint = Blueprint("plugin_depobio", __name__)


@blueprint.route("/extended_af_publish/<int:af_id>", endpoint="extended_af_publish")
@permissions.check_cruved_scope("E", module_code="METADATA")
@json_resp
def publish_acquisition_framework_mail(af_id):
    """
    Method for sending a mail during the publication process
    Parameters
    ----------
    af_id Identifiant of acquisition framework

    Returns Mail sent
    -------

    """
    acquisition_framework = db.session.get(TAcquisitionFramework, af_id)
    mail_builder = MailBuilder(acquisition_framework)
    try:
        mail_builder.send_mail()
    except GeoNatureError as error:
        log.error(str(error))
        raise GeoNatureError(error)
    return mail_builder.mail


def convert_error_to_exception(error: TransportQueryError, file_number: int) -> Exception:
    error_code = error.errors[0]["extensions"]["code"]
    if error_code == ErrorCode.NOT_FOUND:
        result = NotFound(f"Le dossier numéro {file_number} n'existe pas")
    elif error_code == ErrorCode.FORBIDDEN:
        result = Forbidden(
            f"Le dossier numéro {file_number} ne peut pas être récupéré. Vérifiez que votre numéro de "
            "dossier appartient à la bonne démarche"
        )
    else:
        result = error
    return result


@blueprint.route("/validate_file_number/<int:file_number>", endpoint="validate_file_number")
@permissions.check_cruved_scope("R", module_code="METADATA")
@json_resp
def validate_file_number(file_number: int):
    """
    Validate a file number against Demarches Simplifiées
    """
    ds_api = DemarchesSimplifieesConnection()
    try:
        result = ds_api.is_valid_file_number(file_number)
    except TransportQueryError as error:
        raise convert_error_to_exception(error, file_number)
    return result


@blueprint.route("/get_file/<int:file_number>", endpoint="get_file")
@permissions.check_cruved_scope("R", module_code="METADATA")
@json_resp
def get_file(file_number: int):
    """
    Get file informations from Demarches Simplifiées
    """
    ds_api = DemarchesSimplifieesConnection()
    try:
        result = ds_api.get_file(file_number)
    except TransportQueryError as error:
        raise convert_error_to_exception(error, file_number)
    return result


@blueprint.route("/get_af_from_file_number/<int:file_number>", endpoint="get_af_from_file_number")
@permissions.check_cruved_scope("R", module_code="METADATA")
@json_resp
def get_af_from_file_number(file_number: int):
    """
    Get acquisition framework IDs from file number
    """
    afs = (
        db.session.query(TAcquisitionFramework.id_acquisition_framework)
        .filter(TAcquisitionFramework.additional_data["file_id"].astext == str(file_number))
        .all()
    )

    if not afs:
        raise NotFound(f"Aucun cadre d'acquisition trouvé pour le dossier n°{file_number}")

    return [af.id_acquisition_framework for af in afs]
