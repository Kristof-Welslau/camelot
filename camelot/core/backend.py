import logging
import json

from camelot.core.qt import QtWidgets, QtCore
from ..view.requests import AbstractRequest, CancelRequest
from .singleton import QSingleton

LOGGER = logging.getLogger(__name__)

_backend = None
_window = None

def get_root_backend():
    """
    Get the root backend that is used to communicate between python and C++/QML.
    """
    global _backend
    if _backend is None:
        app = QtWidgets.QApplication.instance()
        _backend = app.findChild(QtCore.QObject, 'cpp_root_backend')
        assert _backend
    return _backend

def get_window():
    """
    Get the QQuickView that was created in C++.
    """
    global _window
    if _window is None:
        _window = get_root_backend().window()
        assert _window
    return _window

def is_cpp_gui_context_name(gui_context_name):
    """
    Check if a GUI context name was created in C++. This is the case when the name starts with 'cpp_gui_context'.
    """
    if not len(gui_context_name):
        return False
    return gui_context_name[0] == 'cpp_gui_context'


def cpp_action_step(gui_context_name, name, step=QtCore.QByteArray()):
    response = get_root_backend().action_step(gui_context_name, name, step)
    return json.loads(response.data())


class PythonBackend(QtCore.QObject):
    """
    Dispatch requests from the root backend that cannot be handled
    by the root backend to this python backend object.
    @todo : move this class to the view classes, as it is part of the ui.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        root_backend = get_root_backend()
        root_backend.unhandled_action_step.connect(self.on_unhandled_action_step)

    @QtCore.qt_slot('QStringList', str, 'QStringList', bool, QtCore.QByteArray)
    def on_unhandled_action_step(self, gui_run_name, step_type, gui_context_name, blocking, serialized_step):
        """The backend has cannot handle an action step"""
        LOGGER.debug('Unhandled action step {}, blocking : {}'.format(step_type, blocking))
        from ..admin.action.base import MetaActionStep
        root_backend = get_root_backend()
        try:
            step_cls = MetaActionStep.action_steps[step_type]
            step_cls.gui_run(tuple(gui_run_name), tuple(gui_context_name), bytes(serialized_step))
        except CancelRequest:
            root_backend.action_step_result_valid(gui_run_name, None, True, "")
        except Exception as e:
            LOGGER.error("Step type {}".format(step_type))
            LOGGER.error("Gui context name {}".format(gui_context_name))
            LOGGER.error("Unhandled action step raised an exception", exc_info=e)
            root_backend.action_step_result_valid(gui_run_name, None, False, str(e))


class PythonConnection(QtCore.QObject, metaclass=QSingleton):
    """Use python to connect to a server, this is done by using
    the PythonRootBackend, and lister for signals from the action runner
    and the dgc.  As any instance of this class listens to requests for the
    server, only one instance of this class should exist, to avoid sending
    multiple responses for the same request to the client.
    """

    def __init__(self):
        super().__init__()
        backend = get_root_backend()
        dgc = backend.distributed_garbage_collector()
        dgc.request.connect(self.on_request)
        backend.action_runner().request.connect(self.on_request)
        # would this start the main action ?? or only if one was bound ?
        backend.action_runner().onConnected()

    @classmethod
    def _execute_serialized_request(cls, serialized_request, response_handler):
        try:
            AbstractRequest.handle_request(
                serialized_request, response_handler, response_handler
            )
        except Exception as e:
            LOGGER.error('Unhandled exception in model process', exc_info=e)
            import traceback
            traceback.print_exc()
        except SystemExit:
            LOGGER.info('Terminating')
            raise
        except:
            LOGGER.error('Unhandled event in model process')

    @QtCore.qt_slot(QtCore.QByteArray)
    def on_request(self, request):
        self._execute_serialized_request(request.data(), self)

    @classmethod
    def send_response(cls, response):
        backend = get_root_backend()
        action_runner = backend.action_runner()
        action_runner.onResponse(QtCore.QByteArray(response._to_bytes()))

    @classmethod
    def send_action_step(cls, gui_context_name, step):
        return cpp_action_step(gui_context_name, type(step).__name__, step._to_bytes())

    def has_cancel_request(self):
        return False
