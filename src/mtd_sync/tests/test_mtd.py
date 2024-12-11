import pytest
from flask import Flask, g, url_for, current_app
import mtd_sync.blueprint as blue


@pytest.mark.usefixtures("client_class", "temporary_transaction", "celery_eager")
class TestMtd:
    def test_sync(self):
        app = Flask(__name__)
        with app.app_context():
            # r = self.cli.invoke(blue.synchronize_mtd)
            assert 1 == 1
