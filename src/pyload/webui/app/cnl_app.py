# -*- coding: utf-8 -*-

from pyload.webui.app import app

import json
import os
import re
from base64 import standard_b64decode
from binascii import unhexlify
from builtins import str
from urllib.parse import unquote

import flask
import js2py
from cryptography.fernet import Fernet

from pyload.webui.server_thread import PYLOAD_API


bp = flask.Blueprint('cnl', __name__)


def local_check(func):
    def _view(*args, **kwargs):
        if flask.request.environ.get("REMOTE_ADDR", "0") in (
            "127.0.0.1",
            "localhost",
        ) or flask.request.environ.get("HTTP_HOST", "0") in (
            "127.0.0.1:9666",
            "localhost:9666",
        ):
            return func(*args, **kwargs)
        else:
            return "Forbidden", 403

    return _view


@bp.route(r"/flash/<id>")
@bp.route(r"/flash", methods=['GET', 'POST'])
@local_check
def flash(id="0"):
    return "JDownloader\r\n"


@bp.route(r"/flash/add", methods=['POST'])
@local_check
def add():
    package = flask.request.form.get(
        "package",
        flask.request.form.get("source", flask.request.form.get("referer", None)),
    )
    urls = list(filter(None, map(str.strip, flask.request.form["urls"].split("\n"))))

    if package:
        PYLOAD_API.addPackage(package, urls, 0)
    else:
        PYLOAD_API.generateAndAddPackages(urls, 0)

    return ""


@bp.route(r"/flash/addcrypted", methods=['POST'])
@local_check
def addcrypted():
    package = flask.request.form.get(
        "package",
        flask.request.form.get("source", flask.request.form.get("referer", None)),
    )
    dlc = flask.request.form["crypted"].replace(" ", "+")

    dl_path = PYLOAD_API.getConfigValue("general", "download_folder")
    dlc_path = os.path.join(
        dl_path, package.replace("/", "").replace("\\", "").replace(":", "") + ".dlc"
    )
    with open(dlc_path, mode="wb") as dlc_file:
        dlc_file.write(dlc)

    try:
        PYLOAD_API.addPackage(package, [dlc_path], 0)
    except Exception:
        return flask.abort(500)
    else:
        return "success\r\n"


@bp.route(r"/flash/addcrypted2", methods=['POST'])
@local_check
def addcrypted2():
    package = flask.request.form.get(
        "package",
        flask.request.form.get("source", flask.request.form.get("referer", None)),
    )
    crypted = flask.request.form["crypted"]
    jk = flask.request.form["jk"]

    crypted = standard_b64decode(unquote(crypted.replace(" ", "+")))
    jk = "{} f()".format(jk)
    jk = js2py.eval_js(jk)

    try:
        key = unhexlify(jk)
    except Exception:
        print("Could not decrypt key, please install py-spidermonkey or ossp-js")
        return "failed"

    obj = Fernet(key)
    urls = obj.decrypt(crypted).replace("\x00", "").replace("\r", "").split("\n")

    urls = list(filter(None, map(str.strip, urls)))

    try:
        if package:
            PYLOAD_API.addPackage(package, urls, 0)
        else:
            PYLOAD_API.generateAndAddPackages(urls, 0)
    except Exception:
        return "failed can't add"
    else:
        return "success\r\n"


@bp.route(r"/flashgot_pyload", methods=['GET', 'POST'])
@bp.route(r"/flashgot", methods=['GET', 'POST'])
@local_check
def flashgot():
    if flask.request.environ["HTTP_REFERER"] not in (
        "http://localhost:9666/flashgot",
        "http://127.0.0.1:9666/flashgot",
    ):
        return flask.abort(500)

    autostart = int(flask.request.form.get("autostart", 0))
    package = flask.request.form.get("package", None)

    urls = list(filter(None, map(str.strip, flask.request.form["urls"].split("\n"))))
    # folder = flask.request.form.get('dir', None)

    if package:
        PYLOAD_API.addPackage(package, urls, autostart)
    else:
        PYLOAD_API.generateAndAddPackages(urls, autostart)

    return ""


@bp.route(r"/crossdomain.xml")
@local_check
def crossdomain():
    rep = '<?xml version="1.0"?>\n'
    rep += '<!DOCTYPE cross-domain-policy SYSTEM "http://www.macromedia.com/xml/dtds/cross-domain-policy.dtd">\n'
    rep += "<cross-domain-policy>\n"
    rep += '<allow-access-from domain="*" />\n'
    rep += "</cross-domain-policy>"
    return rep


@bp.route(r"/flash/checkSupportForUrl")
@local_check
def checksupport():
    url = flask.request.form.get("url")
    res = PYLOAD_API.checkURLs([url])
    supported = not res[0][1] is None

    return str(supported).lower()


@bp.route(r"/jdcheck.js")
@local_check
def jdcheck():
    rep = "jdownloader=true;\n"
    rep += "var version='9.581;'"
    return rep