# -*- coding: utf-8 -*-
#@author: RaNaN

from __future__ import absolute_import
from __future__ import unicode_literals
from builtins import str
from mod_pywebsocket.msgutil import receive_message

from pyload.Api import ExceptionObject

from .abstracthandler import AbstractHandler


class ApiHandler(AbstractHandler):
    """Provides access to the API.

    Send your request as json encoded string in the following manner:
    ["function", [*args]] or ["function", {**kwargs}]

    the result will be:

    [code, result]

    Don't forget to login first.
    Non json request will be ignored.
    """

    PATH = "/api"

    def transfer_data(self, req):
        while True:
            try:
                line = receive_message(req)
            except TypeError as e: # connection closed
                self.log.debug("WS Error: %s" % e)
                return self.passive_closing_handshake(req)

            self.handle_message(line, req)

    def handle_message(self, msg, req):

        func, args, kwargs = self.handle_call(msg, req)
        if not func:
            return # handle_call already sent the result

        if func == 'login':
            return self.do_login(req, args, kwargs)
        elif func == 'logout':
            return self.do_logout(req)
        else:
            if not req.api:
                return self.send_result(req, self.FORBIDDEN, "Forbidden")

            if not self.api.isAuthorized(func, req.api.user):
                return self.send_result(req, self.UNAUTHORIZED, "Unauthorized")

            try:
                result = getattr(req.api, func)(*args, **kwargs)
            except ExceptionObject as e:
                return self.send_result(req, self.BAD_REQUEST, e)
            except AttributeError:
                return self.send_result(req, self.NOT_FOUND, "Not Found")
            except Exception as e:
                self.pyload.print_exc()
                return self.send_result(req, self.ERROR, str(e))

            # None is invalid json type
            if result is None: result = True

            return self.send_result(req, self.OK, result)