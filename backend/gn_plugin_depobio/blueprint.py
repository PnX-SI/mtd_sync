from flask import Blueprint, abort

import logging
from geonature.core.gn_meta.models import TAcquisitionFramework
from geonature.utils.env import db
from geonature.utils.errors import GeoNatureError
from geonature.core.gn_permissions import decorators as permissions
from utils_flask_sqla.response import json_resp
from .demarches_simplifiee import DemarcheSimplifieConnexion
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


@blueprint.route("/validate_folder_number/<int:folder_number>", endpoint="validate_folder_number")
@permissions.check_cruved_scope("R", module_code="METADATA")
@json_resp
def validate_folder_number(folder_number: int):
    """
    Method for validating a folder number against Demarche Simplifiée
    ----------
    folder_number

    -------

    """
    ds_api = DemarcheSimplifieConnexion()
    result = ds_api.is_valid_folder_number(folder_number)
    if not result:
        abort(404, description=f"Le dossier numéro {folder_number} n'existe pas")
    return result

