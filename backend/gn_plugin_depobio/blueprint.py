from time import sleep

from flask import Blueprint, abort

import logging
from geonature.core.gn_meta.models import TAcquisitionFramework
from geonature.utils.env import db
from geonature.utils.errors import GeoNatureError
from geonature.core.gn_permissions import decorators as permissions
from utils_flask_sqla.response import json_resp
from gql.transport.exceptions import TransportQueryError
from werkzeug.exceptions import Forbidden, NotFound
from .demarches_simplifiees import DemarchesSimplifieesConnexion, ErrorCode
from .mail_builder import MailBuilder

log = logging.getLogger()
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

def convert_error_to_exception(error: TransportQueryError, folder_number: int) -> Exception:
    error_code = error.errors[0]["extensions"]["code"]
    if error_code == ErrorCode.NOT_FOUND:
        result = NotFound(f"Le dossier numéro {folder_number} n'existe pas")
        result.printable = True
    elif error_code == ErrorCode.FORBIDDEN:
        result = Forbidden(f"Le dossier numéro {folder_number} ne peux pas être visualisé. Vérifiez que votre numéro de "
                           f"dossier appartient à la bonne démarche")
        result.printable = True
    else:
        result = error
    return result

@blueprint.route("/validate_folder_number/<int:folder_number>", endpoint="validate_folder_number")
@permissions.check_cruved_scope("R", module_code="METADATA")
@json_resp
def validate_folder_number(folder_number: int):
    """
    Method for validating a folder number against Demarches Simplifiées
    ----------
    folder_number

    -------

    """
    ds_api = DemarchesSimplifieesConnexion()
    try:
        result = ds_api.is_valid_folder_number(folder_number)
    except TransportQueryError as error:
        raise convert_error_to_exception(error, folder_number)
    return result

@blueprint.route("/get_folder/<int:folder_number>", endpoint="get_folder")
@permissions.check_cruved_scope("R", module_code="METADATA")
@json_resp
def get_folder(folder_number: int):
    """
    Method for getting folder informations from Demarches Simplifiées
    ----------
    folder_number

    -------

    """
    ds_api = DemarchesSimplifieesConnexion()
    try:
        result = ds_api.get_folder(folder_number)
    except TransportQueryError as error:
        raise convert_error_to_exception(error, folder_number)
    return result
