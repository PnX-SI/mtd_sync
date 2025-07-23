from flask import request, current_app, Blueprint
import click
import logging
from geonature.core.gn_meta.models import TAcquisitionFramework
from geonature.utils.env import db
from geonature.utils.errors import GeoNatureError
from geonature.core.gn_permissions import decorators as permissions
from utils_flask_sqla.response import json_resp
from .mail_builder import MailBuilder

log = logging.getLogger()
blueprint = Blueprint("mtd_sync", __name__)

from .mtd_sync import (
    sync_af_and_ds as mtd_sync_af_and_ds,
    sync_af_and_ds_by_user,
)


@current_app.before_request
def synchronize_mtd():
    if request.method != "OPTIONS" and request.endpoint in [
        "gn_meta.get_datasets",
        "gn_meta.get_acquisition_frameworks_list",
    ]:
        from flask_login import current_user

        if current_user.is_authenticated:
            params = request.json if request.is_json else request.args
            try:
                list_id_af = params.get("id_acquisition_frameworks", [])
                for id_af in list_id_af:
                    sync_af_and_ds_by_user(id_role=current_user.id_role, id_af=id_af)
                if not list_id_af:
                    sync_af_and_ds_by_user(id_role=current_user.id_role)
            except Exception as e:
                log.exception(f"Error while get JDD via MTD: {e}")


@blueprint.cli.command()
@click.option("--id-role", nargs=1, required=False, default=None, help="ID of an user")
@click.option(
    "--id-af",
    nargs=1,
    required=False,
    default=None,
    help="ID of an acquisition framework",
)
def sync(id_role, id_af):
    """
    \b
    Triggers :
    - global sync for instance
    - a sync for a given user only (if id_role is provided)
    - a sync for a given AF (Acquisition Framework) only (if id_af is provided). NOTE: the AF should in this case already exist in the database, and only datasets associated to this AF will be retrieved

    NOTE: if both id_role and id_af are provided, only the datasets possibly associated to both the AF and the user will be retrieved.
    """
    if id_role:
        return sync_af_and_ds_by_user(id_role, id_af)
    else:
        return mtd_sync_af_and_ds()


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
        return {"error": error}, 500
    return mail_builder.mail
