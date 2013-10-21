import gevent
from flask import Flask, current_app
from ..models import project_signal, package_signal, index_project
from ..search import index_project as index_search
from .assets import extract_assets
from .dependent import calculate_dependents
from .meta import meta_info


def _connect_package(sender, changes):
    package, operation = changes

    def _run(config):
        app = Flask('yuan')
        app.config = config
        with app.test_request_context():
            extract_assets(package, operation)
            calculate_dependents(package, operation)
            meta_info(package, operation)

    if current_app.testing:
        extract_assets(package, operation)
        calculate_dependents(package, operation)
    else:
        gevent.spawn(_run, current_app.config)


def _connect_project(sender, changes):
    project, operation = changes

    def _run(config):
        app = Flask('yuan')
        app.config = config
        with app.test_request_context():
            # must index search first.
            index_search(project, operation)
            index_project(project, operation)

    if current_app.testing:
        index_project(project, operation)
    else:
        gevent.spawn(_run, current_app.config)


def connect():
    package_signal.connect(_connect_package)
    project_signal.connect(_connect_project)
