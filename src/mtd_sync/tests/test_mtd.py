from pathlib import Path
from unittest.mock import patch

import pytest
from flask import url_for, g
import logging

from sqlalchemy import select, func

from geonature.core.gn_meta.models import TAcquisitionFramework, TDatasets
from geonature.utils.env import db
from mtd_sync.mtd_sync import sync_af_and_ds

from pypnusershub.tests.utils import set_logged_user
from mtd_sync.mail_builder import MailBuilder
from pypnusershub.db import db, models, User
from mtd_sync.mtd_utils import get_or_create_empty_mail_user

logger = logging.getLogger(__name__)


class TestMtd:
    def test_mtd(self):
        assert 1 == 1


@pytest.fixture
def users_with_mail(users):
    """
    Extend the fixture users by adding mails to every users
    """
    for user in users.values():
        user.email = f"{user.prenom_role}@example.com"
    db.session.commit()
    return users


@pytest.mark.usefixtures("client_class", "temporary_transaction")
class TestBlueprint:
    def test_extend_af_publication(
        self, app, users_with_mail, acquisition_frameworks, synthese_data, caplog
    ):
        """
        We check if the mechanism of extension of af publish works.
        """
        set_logged_user(self.client, users_with_mail["user"])
        af = acquisition_frameworks["af_1"]
        # Configure the extension by setting mtd_sync route as extended af publish route
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
        # We didn't setup mail sending so we only test if the connection refused error is in log when trying to send
        # mail. This is only present if we successfully called the route.
        assert (
            f" Erreur de type GeoNatureError lors de la publication du cadre : Custom route extended_af_publish "
            f"called on {af.id_acquisition_framework} raised : [Errno 111] Connection refused"
        ) in caplog.text

    def test_publish_acquisition_framework_mail_route(
        self, app, users_with_mail, acquisition_frameworks, synthese_data, caplog
    ):
        """
        We test our route by calling it directly
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
        # Same thing, the mail server is not configured so we check only if the right error is present
        assert response.status_code == 500
        assert "[Errno 111] Connection refused" in caplog.text


@pytest.mark.usefixtures("client_class", "temporary_transaction")
class TestMail:
    def test_mail_builder(self, app, users_with_mail, acquisition_frameworks):
        """
        Test if the mail builded correspond to what we expect
        """
        set_logged_user(self.client, users_with_mail["user"])
        af = acquisition_frameworks["af_1"]
        # We need to simulate a request context because the mail builder use the current user
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
    fixture_dir = Path(__file__).parent / "fixtures"

    @pytest.fixture(scope="class", autouse=True)
    def setup_test_sync(self, app):
        # So we don't take into account the instance id
        app.config["MTD_SYNC"]["ID_INSTANCE_FILTER"] = None

    def get_af_ds(self, af_file_name: str, ds_file_name: str) -> tuple[bytes, bytes]:
        with open(self.fixture_dir / af_file_name, "rb") as f:
            af_xml = f.read()
        with open(self.fixture_dir / ds_file_name, "rb") as f:
            ds_xml = f.read()
        return af_xml, ds_xml

    @staticmethod
    def custom_mock_add_digitizer(id_digitizer):
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
    def test_sync_af_and_ds_with_local_files(self, mock_add_digitize, mock_af, mock_ds, app):
        """
        Test the sync_af_and_ds function by mocking API calls
        using local files to simulate API responses.
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
        # Here we do a full test when database had no af/ds previously
        if not initial_af_count and not initial_ds_count:
            assert af_count == 312
            assert ds_count == 583

    @patch("mtd_sync.mtd_sync.MTDInstanceApi._get_ds_xml")
    @patch("mtd_sync.mtd_sync.MTDInstanceApi._get_af_xml")
    @patch("mtd_sync.mtd_sync.add_unexisting_digitizer")
    def test_sync_af_empty_mail(self, mock_add_digitize, mock_af, mock_ds, app):
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
