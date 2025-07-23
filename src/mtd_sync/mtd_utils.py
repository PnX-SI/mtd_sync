import logging
import json
from copy import copy
import pprint
from typing import Literal, Union
import uuid
from flask import current_app

from sqlalchemy import select, exists
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from sqlalchemy.sql import func, update

from sqlalchemy.dialects.postgresql import insert as pg_insert

from geonature.utils.env import DB, db
from geonature.core.gn_meta.models import (
    TDatasets,
    CorDatasetActor,
    TAcquisitionFramework,
    CorAcquisitionFrameworkActor,
)
from geonature.core.gn_commons.models import TModules
from pypnusershub.db.models import Organisme as BibOrganismes, User
from geonature.utils.errors import GeonatureApiError
from pypnusershub.routes import insert_or_update_organism
from pypnusershub.auth.providers.cas_inpn_provider import AuthenficationCASINPN
from pypnusershub.auth.auth_manager import auth_manager

# /!\ DO NOT REMOVE FOLLOWING LINE OF IMPORT
#   The following import is actually used,
#    but from outside of the current file : https://github.com/PnX-SI/GeoNature/blob/c557d1d275c406805d44da1a6880006d5d452eef/backend/geonature/core/gn_meta/routes.py#L933
from .mtd_webservice import get_acquisition_framework

NOMENCLATURE_MAPPING = {
    "cd_nomenclature_data_type": "DATA_TYP",
    "cd_nomenclature_dataset_objectif": "JDD_OBJECTIFS",
    "cd_nomenclature_data_origin": "DS_PUBLIQUE",
    "cd_nomenclature_source_status": "STATUT_SOURCE",
}

# Get the logger instance "MTD_SYNC"
logger = logging.getLogger("MTD_SYNC")


def sync_ds(ds, cd_nomenclatures):
    """
    Will create or update a given DS according to UUID.
    Only process DS if dataset's cd_nomenclatures exists in ref_normenclatures.t_nomenclatures.

    :param ds: <dict> DS infos
    :param cd_nomenclatures: <array> cd_nomenclature from ref_normenclatures.t_nomenclatures
    """

    uuid_ds = ds["unique_dataset_id"]
    name_ds = ds["dataset_name"]

    logger.debug("MTD - PROCESSING DS WITH UUID '%s' AND NAME '%s'" % (uuid_ds, name_ds))

    if not ds["cd_nomenclature_data_origin"]:
        ds["cd_nomenclature_data_origin"] = "NSP"

    # FIXME: the following temporary fix was added due to possible differences in referential of nomenclatures values between INPN and GeoNature
    #     should be fixed by ensuring that the two referentials are identical, at least for instances that integrates with INPN and thus rely on MTD synchronization from INPN Métadonnées: GINCO and DEPOBIO instances.
    ds_cd_nomenclature_data_origin = ds["cd_nomenclature_data_origin"]
    if ds_cd_nomenclature_data_origin not in cd_nomenclatures:
        logger.warning(
            f"MTD - Nomenclature with code '{ds_cd_nomenclature_data_origin}' not found in database - SKIPPING SYNCHRONIZATION OF DATASET WITH UUID '{uuid_ds}' AND NAME '{name_ds}'"
        )
        return

    # CONTROL AF
    af_uuid = ds.pop("uuid_acquisition_framework")
    af = (
        DB.session.execute(
            select(TAcquisitionFramework).filter_by(unique_acquisition_framework_id=af_uuid)
        )
        .unique()
        .scalar_one_or_none()
    )

    if af is None:
        logger.warning(
            f"MTD - AF with UUID '{af_uuid}' not found in database - SKIPPING SYNCHRONIZATION OF DATASET WITH UUID '{uuid_ds}' AND NAME '{name_ds}'"
        )
        return

    ds["id_acquisition_framework"] = af.id_acquisition_framework
    ds = {
        field.replace("cd_nomenclature", "id_nomenclature"): (
            func.ref_nomenclatures.get_id_nomenclature(NOMENCLATURE_MAPPING[field], value)
            if field.startswith("cd_nomenclature")
            else value
        )
        for field, value in ds.items()
        if value is not None
    }

    ds_exists = DB.session.scalar(
        exists()
        .where(
            TDatasets.unique_dataset_id == ds["unique_dataset_id"],
        )
        .select()
    )

    statement = (
        pg_insert(TDatasets)
        .values(**ds)
        .on_conflict_do_nothing(index_elements=["unique_dataset_id"])
    )
    if ds_exists:
        statement = (
            update(TDatasets)
            .where(TDatasets.unique_dataset_id == ds["unique_dataset_id"])
            .values(**ds)
        )
    DB.session.execute(statement)

    dataset = DB.session.scalars(
        select(TDatasets).filter_by(unique_dataset_id=ds["unique_dataset_id"])
    ).first()

    # Associate dataset to the modules if new dataset
    if not ds_exists:
        associate_dataset_modules(dataset)

    return dataset


def sync_af(af):
    """
    Will update a given AF (Acquisition Framework) if already exists in database according to UUID, else update the AF.

    Parameters
    ----------
    af : dict
        AF infos.

    Returns
    -------
    TAcquisitionFramework
        The updated or inserted acquisition framework.
    """
    # TODO: handle case where af_uuid is None ; as will raise an error at database level when executing the statement below ;
    #   af_uuid being None, i.e. af UUID is missing, could be due to no UUID specified in `<ca:identifiantCadre/>` tag in the XML file
    #   Solutions - if UUID is missing:
    #       - Just pass the sync of the AF
    #       - Generate a UUID for the AF
    af_uuid = af["unique_acquisition_framework_id"]
    name_af = af["acquisition_framework_name"]

    logger.debug("MTD - PROCESSING AF WITH UUID '%s' AND NAME '%s'" % (af_uuid, name_af))

    # Handle case where af_uuid is None, as it would raise an error at database level when executing the statement below.
    #   None value for `af_uuid`, i.e. af UUID is missing, could be due to no UUID specified in `<ca:identifiantCadre/>` tag in the XML file.
    #   If so, we skip the retrieval of the AF.
    if not af_uuid:
        logger.warning(
            f"No UUID provided for the AF with UUID '{af_uuid}' and name '{name_af}' - SKIPPING SYNCHRONIZATION FOR THIS AF."
        )
        return None

    af_exists = DB.session.scalar(
        exists().where(TAcquisitionFramework.unique_acquisition_framework_id == af_uuid).select()
    )

    # Update statement if AF already exists in DB else insert statement
    statement = (
        update(TAcquisitionFramework)
        .where(TAcquisitionFramework.unique_acquisition_framework_id == af_uuid)
        .values(**af)
    )
    if not af_exists:
        statement = (
            pg_insert(TAcquisitionFramework)
            .values(**af)
            .on_conflict_do_nothing(index_elements=["unique_acquisition_framework_id"])
        )
    DB.session.execute(statement)

    acquisition_framework = DB.session.scalars(
        select(TAcquisitionFramework).filter_by(unique_acquisition_framework_id=af_uuid)
    ).first()

    return acquisition_framework


def add_or_update_organism(uuid, nom, email):
    """
    Create or update organism if UUID not exists in DB.

    :param uuid: uniq organism uuid
    :param nom: org name
    :param email: org email
    """
    # Test if actor already exists to avoid nextVal increase
    org_exist = DB.session.scalar(exists().where(BibOrganismes.uuid_organisme == uuid).select())

    if org_exist:
        statement = (
            update(BibOrganismes)
            .where(BibOrganismes.uuid_organisme == uuid)
            .values(
                dict(
                    nom_organisme=nom,
                    email_organisme=email,
                )
            )
            .returning(BibOrganismes.id_organisme)
        )
    else:
        statement = (
            pg_insert(BibOrganismes)
            .values(
                uuid_organisme=uuid,
                nom_organisme=nom,
                email_organisme=email,
            )
            .on_conflict_do_nothing(index_elements=["uuid_organisme"])
            .returning(BibOrganismes.id_organisme)
        )
    return DB.session.execute(statement).scalar()


def associate_actors(
    actors,
    CorActor: Union[CorAcquisitionFrameworkActor, CorDatasetActor],
    pk_name: Literal["id_acquisition_framework", "id_dataset"],
    pk_value: str,
    uuid_mtd: str,
):
    """
    Associate actors with either a given :
    - Acquisition framework - writing to the table `gn_meta.cor_acquisition_framework_actor`.
    - Dataset - writing to the table `gn_meta.cor_dataset_actor`.

    Parameters
    ----------
    actors : list
        list of actors
    CorActor : Union[CorAcquisitionFrameworkActor, CorDatasetActor]
        the SQLAlchemy model corresponding to the destination table
        effectively CorAcquisitionFrameworkActor or CorDatasetActor
    pk_name : Literal['id_acquisition_framework', 'id_dataset']
        pk attribute name:
        - 'id_acquisition_framework' for AF
        - 'id_dataset' for DS
    pk_value : str
        pk value: ID of the AF or DS
    uuid_mtd : str
        UUID of the AF or DS
    """
    type_mtd = "AF" if pk_name == "id_acquisition_framework" else "DS"
    for actor in actors:
        id_organism = None
        uuid_organism = actor["uuid_organism"]
        organism_name = actor.get("organism", None)
        email_actor = actor["email"]
        if uuid_organism:
            if not organism_name:
                logger.warning(
                    f"MTD - actor association impossible for {type_mtd} with UUID '{uuid_mtd}'"
                    f" because the actor has no organism name specified while having a organism UUID specified, which is abnormal"
                    f" - with the following actor information:"
                    f"\n" + format_str_dict_actor_for_logging(actor)
                )
                continue
            with DB.session.begin_nested():
                # create or update organisme
                # FIXME: prevent update of organism email from actor email ! Several actors may be associated to the same organism and still have different mails !
                id_organism = add_or_update_organism(
                    uuid=uuid_organism,
                    nom=organism_name if organism_name else None,
                    email=email_actor,
                )
        else:
            # Retrieve or create an organism in database with `organism_name` as the organism name
            # /!\ Handle case where there is also an organism with the name equals to the value of `name_organism`
            #   - check if there already is an organism with the name `organism_name`
            #       - if there is one:
            #           - set `id_organism` with the ID of the existing organism
            #       - if there is not:
            #           - set `id_organism` with the ID of a newly created organism
            if organism_name:
                is_exists_organism = DB.session.scalar(
                    exists().where(BibOrganismes.nom_organisme == organism_name).select()
                )
                if is_exists_organism:
                    id_organism = DB.session.scalar(
                        select(BibOrganismes.id_organisme)
                        .where(BibOrganismes.nom_organisme == organism_name)
                        .limit(1)
                    )
                else:
                    with DB.session.begin_nested():
                        # Create a new organism with the provided name
                        #   /!\ We do not use the actor email as the organism email - field `bib_organismes.email_organisme` will be empty
                        #   Only the three non-null fields will be written: `id_organisme`, `uuid_organisme`, `nom_organisme`.
                        id_organism = add_or_update_organism(
                            uuid=str(uuid.uuid4()),
                            nom=organism_name,
                            email=None,
                        )
        cd_nomenclature_actor_role = actor["actor_role"]
        id_nomenclature_actor_role = func.ref_nomenclatures.get_id_nomenclature(
            "ROLE_ACTEUR", cd_nomenclature_actor_role
        )
        values = dict(
            id_nomenclature_actor_role=id_nomenclature_actor_role,
            **{pk_name: pk_value},
        )
        # TODO: choose wether to:
        #   - (retained) Try to associate to an organism first and then to a user
        #   - Try to associate to a user first and then to an organism
        # Try to associate to an organism first, and if that is impossible, to a user
        if id_organism:
            values["id_organism"] = id_organism
        # TODO: handle case where no user is retrieved for the actor email:
        #   - (retained) If the actor role is "Contact Principal" associate to a new user with only a UUID and an ID, else just do not try to associate the actor with the metadata
        #   - Try to retrieve an id_organism from the organism name - field `organism`
        #   - Try to retrieve an id_organism from the actor email considered as an organism email - field `email`
        #   - Try to insert a new user from the actor name - field `name` - and possibly also email - field `email`
        else:
            id_user_from_email = DB.session.scalar(
                select(User.id_role).filter_by(email=email_actor).where(User.groupe.is_(False))
            )
            if id_user_from_email:
                values["id_role"] = id_user_from_email
            else:
                # If actor role is "Contact Principal", i.e. cd_nomenclature_actor_role = '1' ,
                #   then we use a dedicated user for 'orphan' metadata - metadata with no associated "Contact principal" actor that could be retrieved
                #   the three non-null fields for `utilisateurs.t_roles` will be set to default:
                #       - `groupe`: False - the role is a user and not a group
                #       - `id_role`: generated by the nextval sequence
                #       - `uuid_role`: generated by uuid_generate_v4()
                #   in particular:
                #       - we do not specify field `email` even if `email_actor` is to be set
                #       - only the field `dec_role` will be written to a non-default value, so as to identify this particular "Contact principal"-for-orphan-metadata user
                cd_nomenclature_actor_role_for_contact_principal_af = "1"
                if (
                    type_mtd == "AF"
                    and cd_nomenclature_actor_role
                    == cd_nomenclature_actor_role_for_contact_principal_af
                ):
                    # Retrieve the "Contact principal"-for-orphan-metadata user
                    desc_role_for_user_contact_principal_for_orphan_metadata = "Contact principal for 'orphan' metadata - i.e. with no 'Contact Principal' that could be retrieved during INPN MTD synchronisation"
                    id_user_contact_principal_for_orphan_metadata = 0
                    user_contact_principal_for_orphan_metadata = DB.session.get(
                        User, id_user_contact_principal_for_orphan_metadata
                    )
                    # /!\ Assert that the user with ID 0 retrieved is actually the "Contact principal"-for-orphan-metadata user with the right "desc_role"
                    #   If an error is raised, one must choose how to handle this situation:
                    #       - Check for the current user with ID 0
                    #       - Possibly change the ID of this user to an ID other than 0
                    #           /!\ Be careful to the other entries associated to this user
                    #           /!\ Be careful when choosing a new ID : positive integer should be reserved for users retrieved from the INPN
                    #       - Eventually change the code to:
                    #           - set an ID other than 0 for the "Contact principal"-for-orphan-metadata user
                    #           - possibly allow to configure a different ID for different GN instances
                    if user_contact_principal_for_orphan_metadata:
                        assert (
                            user_contact_principal_for_orphan_metadata.desc_role
                            == desc_role_for_user_contact_principal_for_orphan_metadata
                        )
                    # If the user does not yet exist, create it
                    else:
                        dict_data_generated_user = {
                            "id_role": id_user_contact_principal_for_orphan_metadata,
                            "desc_role": desc_role_for_user_contact_principal_for_orphan_metadata,
                        }
                        id_provider_inpn = current_app.config["MTD_SYNC"]["ID_PROVIDER_INPN"]
                        idprov = AuthenficationCASINPN()
                        idprov.id_provider = id_provider_inpn
                        dict_data_generated_user = idprov.insert_or_update_role(
                            user_dict=dict_data_generated_user,
                            reconciliate_attr="desc_role",
                        )
                    # Commit to ensure that the insert from previous statement is actually committed
                    DB.session.commit()
                    values["id_role"] = id_user_contact_principal_for_orphan_metadata
                else:
                    logger.warning(
                        f"MTD - actor association impossible for {type_mtd} with UUID '{uuid_mtd}' because no id_organism nor id_role could be retrieved - with the following actor information:\n"
                        + format_str_dict_actor_for_logging(actor)
                    )
                    continue
        try:
            statement = (
                pg_insert(CorActor)
                .values(**values)
                .on_conflict_do_nothing(
                    index_elements=[
                        pk_name,
                        "id_organism" if id_organism else "id_role",
                        "id_nomenclature_actor_role",
                    ],
                )
            )
            DB.session.execute(statement)
        except IntegrityError as I:
            DB.session.rollback()
            logger.error(
                f"MTD - DB INTEGRITY ERROR - actor association failed for {type_mtd} with UUID '{uuid_mtd}' and following actor information:\n"
                + format_sqlalchemy_error_for_logging(I)
                + format_str_dict_actor_for_logging(actor)
            )


def associate_dataset_modules(dataset):
    """
    Associate a dataset to modules specified in [MTD][JDD_MODULE_CODE_ASSOCIATION] parameter (geonature config)

    :param dataset: <geonature.core.gn_meta.models.TDatasets> dataset (SQLAlchemy model object)
    """
    dataset.modules.extend(
        DB.session.scalars(
            select(TModules).where(
                TModules.module_code.in_(
                    current_app.config["MTD_SYNC"]["JDD_MODULE_CODE_ASSOCIATION"]
                )
            )
        ).all()
    )


def format_sqlalchemy_error_for_logging(error: SQLAlchemyError):
    """
    Format SQLAlchemy error information in a nice way for MTD logging

    Parameters
    ----------
    error : SQLAlchemyError
        the SQLAlchemy error

    Returns
    -------
    str
        formatted error information
    """
    indented_original_error_message = str(error.orig).replace("\n", "\n\t")

    formatted_error_message = "".join(
        [
            f"\t{indented_original_error_message}",
            f"SQL QUERY:  {error.statement}\n",
            f"\tSQL PARAMS:  {error.params}\n",
        ]
    )

    return formatted_error_message


def format_str_dict_actor_for_logging(actor: dict):
    """
    Format actor information in a nice way for MTD logging

    Parameters
    ----------
    actor : dict
        actor information: actor_role, email, name, organism, uuid_organism, ...

    Returns
    -------
    str
        formatted actor information
    """
    formatted_str_dict_actor = "\tACTOR:\n\t\t" + pprint.pformat(actor).replace(
        "\n", "\n\t\t"
    ).rstrip("\t")

    return formatted_str_dict_actor


class CasAuthentificationError(GeonatureApiError):
    pass


def insert_user_and_org(info_user, update_user_organism: bool = True):
    id_provider_inpn = current_app.config["MTD_SYNC"]["ID_PROVIDER_INPN"]
    # TODO: use `auth_manager.get_provider(id_provider_inpn)` rather than instanciating from `AuthenficationCASINPN`
    #   Make same modification in other parts of the code
    idprov = AuthenficationCASINPN()
    idprov.id_provider = id_provider_inpn
    # TODO: remove two following lines - unnecessary
    if id_provider_inpn not in auth_manager:
        auth_manager.add_provider(id_provider_inpn, idprov)

    # TODO: remove following section - unnecessary
    # if not id_provider_inpn in auth_manager:
    #     raise GeonatureApiError(
    #         f"Identity provider named {id_provider_inpn} is not registered ! "
    #     )
    inpn_identity_provider = idprov

    organism_id = info_user["codeOrganisme"]
    organism_name = info_user.get("libelleLongOrganisme", "Autre")
    user_login = info_user["login"]
    user_id = info_user["id"]

    try:
        assert user_id is not None and user_login is not None
    except AssertionError:
        logger.error("'CAS ERROR: no ID or LOGIN provided'")
        raise CasAuthentificationError("CAS ERROR: no ID or LOGIN provided", status_code=500)

    # Reconciliation avec base GeoNature
    if organism_id:
        organism = {"id_organisme": organism_id, "nom_organisme": organism_name}
        insert_or_update_organism(organism)

    # Retrieve user information from `info_user`
    user_info = {
        "id_role": user_id,
        "identifiant": user_login,
        "nom_role": info_user["nom"],
        "prenom_role": info_user["prenom"],
        "id_organisme": organism_id,
        "email": info_user["email"],
        "active": True,
    }

    # If not updating user organism and user already exists, retrieve existing user organism information rather than information from `info_user`
    existing_user = User.query.get(user_id)
    if not update_user_organism and existing_user:
        user_info["id_organisme"] = existing_user.id_organisme

    # Insert or update user

    with current_app.app_context():
        user_info = inpn_identity_provider.insert_or_update_role(user_info, "email")

    # Associate user to a default group if the user is not associated to any group
    user = existing_user or DB.session.get(User, user_id)

    if not user.groups:
        if current_app.config["MTD_SYNC"]["USERS_CAN_SEE_ORGANISM_DATA"] and organism_id:
            # group socle 2 - for a user associated to an organism if users can see data from their organism
            group_id = current_app.config["MTD_SYNC"]["ID_USER_SOCLE_2"]
        else:
            # group socle 1
            group_id = current_app.config["MTD_SYNC"]["ID_USER_SOCLE_1"]
        group = DB.session.get(User, group_id)
        user.groups.append(group)

    return user_info
