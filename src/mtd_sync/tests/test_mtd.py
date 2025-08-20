from pathlib import Path
from unittest.mock import patch

import pytest
from flask import url_for, g
import logging

from sqlalchemy import select, func

from geonature.core.gn_meta.models import (
    TAcquisitionFramework,
    TDatasets,
    CorAcquisitionFrameworkActor,
)
from geonature.utils.env import db
from mtd_sync.mtd_sync import sync_af_and_ds
from pypnnomenclature.models import TNomenclatures, BibNomenclaturesTypes

from pypnusershub.tests.utils import set_logged_user
from mtd_sync.mail_builder import MailBuilder
from pypnusershub.db import db, models, User
from mtd_sync.mtd_utils import get_or_create_empty_mail_user

logger = logging.getLogger(__name__)


class TestMtd:
    """Class for testing MTD functionality"""

    def test_mtd(self) -> None:
        """Simple test to verify basic setup"""
        assert 1 == 1


@pytest.fixture
def users_with_mail(users) -> dict:
    """
    Extend the fixture users by adding mails to every users

    Args:
        users: Dictionary of users to extend

    Returns:
        dict: Users with added email addresses
    """
    for user in users.values():
        user.email = f"{user.prenom_role}@example.com"
    db.session.commit()
    return users


@pytest.mark.usefixtures("client_class", "temporary_transaction")
class TestBlueprint:
    """Class for testing blueprint routes"""

    def test_extend_af_publication(
        self, app, users_with_mail: dict, acquisition_frameworks: dict, synthese_data: dict, caplog
    ) -> None:
        """
        We check if the mechanism of extension of af publish works.

        Args:
            app: Flask app instance
            users_with_mail: Dictionary of users with email
            acquisition_frameworks: Dictionary of acquisition frameworks
            synthese_data: Dictionary of synthese data
            caplog: Pytest caplog fixture
        """
        set_logged_user(self.client, users_with_mail["user"])
        af = acquisition_frameworks["af_1"]
        route_name = "mtd_sync.extended_af_publish"
        app.config["METADATA"]["EXTENDED_AF_PUBLISH_ROUTE_NAME"] = route_name
        with caplog.at_level(logging.ERROR):
            response = self.client.get(
                url_for(
                    "gn_meta.publish_acquisition_framework",
                    af_id=af.id_acquisition_framework,
                )
            )
        assert response.status_code == 500, response.json
        assert (
            f" Erreur de type GeoNatureError lors de la publication du cadre : Custom route extended_af_publish "
            f"called on {af.id_acquisition_framework} raised : [Errno 111] Connection refused"
        ) in caplog.text

    def test_publish_acquisition_framework_mail_route(
        self, app, users_with_mail: dict, acquisition_frameworks: dict, synthese_data: dict, caplog
    ) -> None:
        """
        We test our route by calling it directly

        Args:
            app: Flask app instance
            users_with_mail: Dictionary of users with email
            acquisition_frameworks: Dictionary of acquisition frameworks
            synthese_data: Dictionary of synthese data
            caplog: Pytest caplog fixture
        """
        set_logged_user(self.client, users_with_mail["user"])
        af = acquisition_frameworks["af_1"]
        with caplog.at_level(logging.ERROR):
            response = self.client.get(
                url_for(
                    "mtd_sync.extended_af_publish",
                    af_id=af.id_acquisition_framework,
                )
            )
        assert response.status_code == 500
        assert "[Errno 111] Connection refused" in caplog.text


@pytest.mark.usefixtures("client_class", "temporary_transaction")
class TestMail:
    """Class for testing mail functionality"""

    def test_mail_builder(self, app, users_with_mail: dict, acquisition_frameworks: dict) -> None:
        """
        Test if the mail builded correspond to what we expect

        Args:
            app: Flask app instance
            users_with_mail: Dictionary of users with email
            acquisition_frameworks: Dictionary of acquisition frameworks
        """
        set_logged_user(self.client, users_with_mail["user"])
        af = acquisition_frameworks["af_1"]
        with app.test_request_context():
            g.current_user = users_with_mail["stranger_user"]
            mail_builder = MailBuilder(af)

        assert mail_builder.mail["recipients"] == ["Stranger@example.com"]
        assert (
            mail_builder.mail["subject"]
            == f"Dépôt du cadre d'acquisition {str(af.unique_acquisition_framework_id).upper()}"
        )
        assert "af_1" in mail_builder.mail["msg_html"]
        assert str(af.unique_acquisition_framework_id).upper() in mail_builder.mail["msg_html"]


@pytest.mark.usefixtures("client_class", "temporary_transaction")
class TestSync:
    """Class for testing sync functionality"""

    fixture_dir = Path(__file__).parent / "fixtures"

    @pytest.fixture(scope="class", autouse=True)
    def setup_test_sync(self, app) -> None:
        """
        Setup for sync tests. We wan"t to accept AF from every instance.

        Args:
            app: Flask app instance
        """
        app.config["MTD_SYNC"]["ID_INSTANCE_FILTER"] = None

    def get_af_ds(self, af_file_name: str, ds_file_name: str) -> tuple[bytes, bytes]:
        """
        Get AF and DS XML files contents

        Args:
            af_file_name: Acquisition framework XML filename
            ds_file_name: Dataset XML filename

        Returns:
            tuple[bytes, bytes]: AF and DS XML contents
        """
        with open(self.fixture_dir / af_file_name, "rb") as f:
            af_xml = f.read()
        with open(self.fixture_dir / ds_file_name, "rb") as f:
            ds_xml = f.read()
        return af_xml, ds_xml

    @staticmethod
    def custom_mock_add_digitizer(id_digitizer: int) -> None:
        """
        Mock function to add digitizer user

        Args:
            id_digitizer: ID of digitizer to add
        """
        if db.session.execute(db.select(models.User).filter_by(id_role=id_digitizer)).scalar():
            return
        user_ = models.User(
            **{
                "id_role": id_digitizer,
                "identifiant": id_digitizer,
                "nom_role": id_digitizer,
                "email": f"{id_digitizer}@test.fr",
            }
        )
        db.session.add(user_)
        db.session.commit()

    @patch("mtd_sync.mtd_sync.MTDInstanceApi._get_ds_xml")
    @patch("mtd_sync.mtd_sync.MTDInstanceApi._get_af_xml")
    @patch("mtd_sync.mtd_sync.add_unexisting_digitizer")
    def test_sync_af_and_ds_with_local_files(
        self, mock_add_digitize, mock_af, mock_ds, app
    ) -> None:
        """
        Test the sync_af_and_ds function by mocking API calls
        using local files to simulate API responses.

        Args:
            mock_add_digitize: Mock for add_unexisting_digitizer
            mock_af: Mock for getting AF XML
            mock_ds: Mock for getting DS XML
            app: Flask app instance
        """
        initial_af_count_statement = select(func.count()).select_from(TAcquisitionFramework)
        initial_af_count = db.session.scalar(initial_af_count_statement)
        initial_ds_count_statement = select(func.count()).select_from(TDatasets)
        initial_ds_count = db.session.scalar(initial_ds_count_statement)

        mock_add_digitize.side_effect = self.custom_mock_add_digitizer
        mock_af.return_value, mock_ds.return_value = self.get_af_ds(
            "mock_af_data.xml", "mock_ds_data.xml"
        )
        sync_af_and_ds()
        assert mock_af.called, "The mock af was not called"
        assert mock_ds.called, "The mock ds was not called"
        af_count_statement = select(func.count()).select_from(TAcquisitionFramework)
        af_count = db.session.scalar(af_count_statement)
        ds_count_statement = select(func.count()).select_from(TDatasets)
        ds_count = db.session.scalar(ds_count_statement)
        assert af_count > initial_af_count
        assert ds_count > initial_ds_count
        if not initial_af_count and not initial_ds_count:
            assert af_count == 312
            assert ds_count == 583

    @patch("mtd_sync.mtd_sync.MTDInstanceApi._get_ds_xml")
    @patch("mtd_sync.mtd_sync.MTDInstanceApi._get_af_xml")
    @patch("mtd_sync.mtd_sync.add_unexisting_digitizer")
    def test_sync_af_empty_mail(self, mock_add_digitize, mock_af, mock_ds, app) -> None:
        """
        Test if empty importing an af without mail link it to a specific user

        Args:
            mock_add_digitize: Mock for add_unexisting_digitizer
            mock_af: Mock for getting AF XML
            mock_ds: Mock for getting DS XML
            app: Flask app instance
        """
        mock_add_digitize.side_effect = self.custom_mock_add_digitizer
        mock_add_digitize.side_effect = self.custom_mock_add_digitizer
        mock_af.return_value, mock_ds.return_value = self.get_af_ds(
            "mock_af_without_mail.xml", "short_mock_ds.xml"
        )
        sync_af_and_ds()
        af_statement = select(TAcquisitionFramework).filter_by(
            unique_acquisition_framework_id="4A9DDA1F-B623-3E13-E053-2614A8C02B7C"
        )
        acquisition_framework: TAcquisitionFramework = db.session.execute(af_statement).scalar()
        cor_actor = acquisition_framework.cor_af_actor[0]
        actor = db.session.scalar(select(User).where(User.id_role == cor_actor.id_role))
        expected_actor = get_or_create_empty_mail_user()
        assert actor.identifiant == expected_actor.identifiant

    @patch("mtd_sync.mtd_sync.MTDInstanceApi._get_ds_xml")
    @patch("mtd_sync.mtd_sync.MTDInstanceApi._get_af_xml")
    @patch("mtd_sync.mtd_sync.add_unexisting_digitizer")
    def test_sync_af_and_update(self, mock_add_digitize, mock_af, mock_ds, app) -> None:
        """
        Test actor replacement on AF update. We wan't to make sure that it replace the actor and not add it

        Args:
            mock_add_digitize: Mock for add_unexisting_digitizer
            mock_af: Mock for getting AF XML
            mock_ds: Mock for getting DS XML
            app: Flask app instance
        """
        mock_add_digitize.side_effect = self.custom_mock_add_digitizer
        mock_add_digitize.side_effect = self.custom_mock_add_digitizer
        mock_af.return_value, mock_ds.return_value = self.get_af_ds(
            "short_mock_af.xml", "short_mock_ds.xml"
        )
        sync_af_and_ds()
        mock_af.return_value, mock_ds.return_value = self.get_af_ds(
            "short_mock_af_updated.xml", "short_mock_ds.xml"
        )
        sync_af_and_ds()
        af_statement = select(TAcquisitionFramework).filter_by(
            unique_acquisition_framework_id="4A9DDA1F-B623-3E13-E053-2614A8C02B7C"
        )
        acquisition_framework: TAcquisitionFramework = db.session.execute(af_statement).scalar()
        main_contacts = self.get_main_contacts(acquisition_framework)
        assert len(main_contacts) == 1

    @staticmethod
    def get_main_contact_nomenclature() -> TNomenclatures:
        """
        Get main contact nomenclature

        Returns:
            TNomenclatures: Main contact nomenclature object
        """
        nomenclature_type = db.session.execute(
            select(BibNomenclaturesTypes).where(BibNomenclaturesTypes.mnemonique == "ROLE_ACTEUR")
        ).scalar()
        main_contact_nomenclature = db.session.execute(
            select(TNomenclatures).where(
                (TNomenclatures.mnemonique == "Contact principal")
                & (TNomenclatures.id_type == nomenclature_type.id_type)
            )
        ).scalar()
        return main_contact_nomenclature

    @classmethod
    def get_main_contacts(
        cls, acquisition_framework: TAcquisitionFramework
    ) -> list[CorAcquisitionFrameworkActor]:
        """
        Get main contacts from acquisition framework

        Args:
            acquisition_framework: Acquisition framework object

        Returns:
            list[CorAcquisitionFrameworkActor]: List of main contact actors
        """
        main_contacts = []
        nomenclature = cls.get_main_contact_nomenclature()
        for actor in acquisition_framework.cor_af_actor:
            if actor.id_nomenclature_actor_role == nomenclature.id_nomenclature:
                main_contacts.append(actor)
        return main_contacts
