import logging

from flask import current_app, g

from geonature.core.gn_meta.models import TAcquisitionFramework
from geonature.utils.env import db
from geonature.utils.errors import GeoNatureError
from pypnusershub.db import User

import geonature.utils.utilsmails as mail
from geonature.utils.config import config

logger = logging.getLogger()
configuration_depobio = config["PLUGIN_DEPOBIO"]


class MailBuilder:
    def __init__(self, acquisition_framework: TAcquisitionFramework):
        """
        Build a mail from an acquisition framework

        Parameters
        ----------
        acquisition_framework
        """
        self.af = acquisition_framework
        self.folder_id = None
        if self.af.additional_data:
            self.folder_id = self.af.additional_data.get("folder_id")
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
        Send the built mail only if, subjects, content and recipients are set.
        """
        if self.subject and self.content and len(self.recipients) > 0:
            mail.send_mail(**self.mail)
            logger.info(f"mail {self.subject} sent to {self.recipients}")
        else:
            raise GeoNatureError(
                f"Couldn't send mail because one of those property is empty : [{self.subject:}], [{self.content}], "
                f"[{self.recipients}]"
            )

    def _build_subject(self) -> str:
        """
        Fill the subject of the mail

        Returns
        -------
        mail subject
        """
        mail_subject = (
            "Dépôt du cadre d'acquisition " + str(self.af.unique_acquisition_framework_id).upper()
        )
        mail_subject_base = configuration_depobio["MAIL_SUBJECT_AF_CLOSED_BASE"]
        if mail_subject_base:
            mail_subject = mail_subject_base + " " + mail_subject
        if self.folder_id:
            mail_subject = mail_subject + " pour le dossier {}".format(self.folder_id)
        return mail_subject

    def _build_content(self) -> str:
        """
        Build the content of the mail from AF information

        Returns
        -------
        mail content
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

        mail_content_additions = configuration_depobio["MAIL_CONTENT_AF_CLOSED_ADDITION"]
        mail_content_pdf = configuration_depobio["MAIL_CONTENT_AF_CLOSED_PDF"]
        mail_content_greetings = configuration_depobio["MAIL_CONTENT_AF_CLOSED_GREETINGS"]
        if self.folder_id:
            mail_content = mail_content + f" dans le cadre du dossier {self.folder_id}"

        mail_content += mail_content_additions if mail_content_additions else ".<br>"
        if mail_content_pdf:
            mail_content += mail_content_pdf.format(pdf_url) + pdf_url + "<br>"

        if mail_content_greetings:
            mail_content += mail_content_greetings
        return mail_content

    def _build_recipient(self) -> set[str]:
        """
        Create the recipients of the mail. If the publisher is the the AF digitizer, we send a mail to both of them

        Returns
        -------
        set of recipîents
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
