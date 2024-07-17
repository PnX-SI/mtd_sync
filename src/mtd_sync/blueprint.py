from flask import request, g, current_app, Blueprint
import click
import logging
from flask_login import login_required, login_manager
from geonature.core.gn_meta.routes import routes

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

        try:
            sync_af_and_ds_by_user(id_role=current_user.id_role)
        except Exception as e:
            log.exception("Error while get JDD via MTD")


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
