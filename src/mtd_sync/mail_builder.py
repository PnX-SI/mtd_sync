import logging

from flask import current_app, g

from geonature.utils.env import db
from geonature.utils.errors import GeoNatureError
from pypnusershub.db import User
from lxml import etree as ET

from .mtd_webservice import get_acquisition_framework
from .xml_parser import get_tag_content
import geonature.utils.utilsmails as mail
from geonature.utils.config import config

logger = logging.getLogger()
configuration_mtd = config["MTD_SYNC"]


class MailBuilder:
    def __init__(self, acquisition_framework):
        """
        Build a mail from an acquisition framework
        """
        self.af = acquisition_framework
        self.ca_idtps = self._get_ca_idtps()
        self.subject = self._build_subject()
        self.content = self._build_content()
        self.recipients = self._build_recipient()
        self.mail = {
            "recipients": list(self.recipients),
            "subject": self.subject,
            "msg_html": self.content,
        }

    def send_mail(self) -> None:
        """
        Send the built mail  only if, subjects, content and recipients are set.
        """
        if self.subject and self.content and len(self.recipients) > 0:
            mail.send_mail(**self.mail)
            logger.info(f"mail {self.subject} sent to {self.recipients}")
        else:
            raise GeoNatureError(
                f"Couldn't send mail because one of those property is empty : [{self.subject:}], [{self.content}], "
                f"[{self.recipients}]"
            )

    def _build_subject(self):
        """
        Fill the subject of the mail
        """
        mail_subject = (
            "Dépôt du cadre d'acquisition " + str(self.af.unique_acquisition_framework_id).upper()
        )
        mail_subject_base = configuration_mtd["MAIL_SUBJECT_AF_CLOSED_BASE"]
        if mail_subject_base:
            mail_subject = mail_subject_base + " " + mail_subject
        if self.ca_idtps:
            mail_subject = mail_subject + " pour le dossier {}".format(self.ca_idtps)
        return mail_subject

    def _get_ca_idtps(self) -> str:
        """
        Get a parameter of xml call idTPS. If empty return empty string
        """
        # Parsing the AF XML from MTD to get the idTPS parameter
        self.af_xml = get_acquisition_framework(
            str(self.af.unique_acquisition_framework_id).upper()
        )
        self.xml_parser = ET.XMLParser(ns_clean=True, recover=True, encoding="utf-8")
        namespace = configuration_mtd.get("XML_NAMESPACE", "{http://inpn.mnhn.fr/mtd}")
        root = ET.fromstring(self.af_xml, parser=self.xml_parser)
        try:
            ca = root.find(".//" + namespace + "CadreAcquisition")
            ca_idtps = get_tag_content(ca, "idTPS")
        except AttributeError:
            ca_idtps = ""
        return ca_idtps

    def _build_content(self) -> str:
        """
        Build the content of the mail from AF information
        """
        # Generate the links for the AF's deposite certificate and framework download
        pdf_url = (
            current_app.config["API_ENDPOINT"]
            + "/meta/acquisition_frameworks/export_pdf/"
            + str(self.af.id_acquisition_framework)
        )

        mail_content = f"""Bonjour,<br>
           <br>
           Le cadre d'acquisition <i> "{self.af.acquisition_framework_name}" </i> dont l’identifiant est
           "{str(self.af.unique_acquisition_framework_id).upper()}" que vous nous avez transmis a été déposé"""

        mail_content_additions = configuration_mtd["MAIL_CONTENT_AF_CLOSED_ADDITION"]
        mail_content_pdf = configuration_mtd["MAIL_CONTENT_AF_CLOSED_PDF"]
        mail_content_greetings = configuration_mtd["MAIL_CONTENT_AF_CLOSED_GREETINGS"]

        if self.ca_idtps:
            mail_content = mail_content + f"dans le cadre du dossier {self.ca_idtps}"

        mail_content += mail_content_additions if mail_content_additions else ".<br>"
        if mail_content_pdf:
            mail_content += mail_content_pdf.format(pdf_url) + pdf_url + "<br>"

        if mail_content_greetings:
            mail_content += mail_content_greetings
        return mail_content

    def _build_recipient(self) -> set[str]:
        """
        Create the recipients of the mail. If the publisher is the the AF digitizer, we send a mail to both of them
        """
        mail_recipients = set()
        cur_user = g.current_user
        if cur_user and cur_user.email:
            mail_recipients.add(cur_user.email)

        if self.af.id_digitizer:
            digitizer = db.session.get(User, self.af.id_digitizer)
            if digitizer and digitizer.email:
                mail_recipients.add(digitizer.email)
        return mail_recipients
