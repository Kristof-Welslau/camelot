#  ============================================================================
#
#  Copyright (C) 2007-2016 Conceptive Engineering bvba.
#  www.conceptive.be / info@conceptive.be
#
#  Redistribution and use in source and binary forms, with or without
#  modification, are permitted provided that the following conditions are met:
#      * Redistributions of source code must retain the above copyright
#        notice, this list of conditions and the following disclaimer.
#      * Redistributions in binary form must reproduce the above copyright
#        notice, this list of conditions and the following disclaimer in the
#        documentation and/or other materials provided with the distribution.
#      * Neither the name of Conceptive Engineering nor the
#        names of its contributors may be used to endorse or promote products
#        derived from this software without specific prior written permission.
#  
#  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
#  ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
#  WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
#  DISCLAIMED. IN NO EVENT SHALL <COPYRIGHT HOLDER> BE LIABLE FOR ANY
#  DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
#  (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
#  LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
#  ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
#  (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
#  SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
#  ============================================================================


from dataclasses import dataclass, InitVar, field
import json

from ...core.qt import QtWidgets, QtCore

from camelot.admin.admin_route import RouteWithRenderHint, AdminRoute
from camelot.admin.action import ActionStep, Action
from camelot.admin.icon import Icon
from camelot.core.exception import CancelRequest
from camelot.core.utils import ugettext as _
from camelot.view.action_runner import hide_progress_dialog
from camelot.view.controls.tableview import TableView
from camelot.view.qml_view import qml_action_step, qml_action_dispatch

from .item_view import OpenTableView, OpenQmlTableView

@dataclass
class SetSelectedObjects(ActionStep):

    objects: list

    def gui_run(self, gui_context):
        dialog = gui_context.view
        dialog.objects = self.objects
        dialog.hide()

class ConfirmSelection(Action):

    verbose_name = _('OK')
    name = 'confirm_selection'
    icon = Icon('check') # 'tango/16x16/emblems/emblem-symbolic-link.png'

    def model_run(self, model_context, mode):
        yield SetSelectedObjects(list(model_context.get_selection()))

confirm_selection = ConfirmSelection()

class CancelSelection(Action):

    verbose_name = _('Cancel')
    name = 'cancel_selection'

    def gui_run(self, gui_context):
        gui_context.view.hide()

cancel_selection = CancelSelection()

class SelectDialog(QtWidgets.QDialog):
    
    def __init__(self, gui_context, admin_route, verbose_name, parent = None):
        super( SelectDialog, self ).__init__( parent )
        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins( 0, 0, 0, 0 )
        layout.setSpacing( 0 )
        self.setWindowTitle( _('Select %s') % verbose_name )
        self.setSizeGripEnabled(True)
        table = TableView(gui_context, admin_route, parent=self)
        table.setObjectName('table_view')
        table.close_clicked_signal.connect(self.close_view)
        layout.addWidget(table)
        self.setLayout( layout )
        self.objects = []

    @QtCore.qt_slot()
    def close_view(self):
        self.reject()


@dataclass
class SelectObjects( OpenTableView ):
    """Select one or more object from a query.  The `yield` of this action step
    return a list of objects.

    :param admin: a :class:`camelot.admin.object_admin.ObjectAdmin` object
    :param search_text: a default string on which to search for in the selection
        dialog
    :param value: a query or a list of object from which the selection should
        be made.  If none is given, the default query from the admin is taken.
    """

    value: InitVar = None
    verbose_name_plural: str = field(init=False)


    def __post_init__(self, admin, value):
        if value is None:
            value = admin.get_query()
        super(SelectObjects, self).__post_init__(admin, value)
        self.verbose_name_plural = str(admin.get_verbose_name_plural())
        # actions
        self.actions = [
            RouteWithRenderHint(AdminRoute._register_list_action_route(admin.get_admin_route(), action),
                                action.render_hint) for action in [cancel_selection, confirm_selection]
        ]
        self.actions.extend(admin.get_select_list_toolbar_actions())
        self.action_states = list()
        self._add_action_states(admin, admin.get_proxy(value), self.actions, self.action_states)
        # list_action
        self.list_action = AdminRoute._register_list_action_route(admin.get_admin_route(), confirm_selection)

    @classmethod
    def render(cls, gui_context, step):
        dialog = SelectDialog(gui_context, tuple(step['admin_route']), step['verbose_name_plural'])
        table_view = dialog.findChild(QtWidgets.QWidget, 'table_view')
        cls.update_table_view(table_view, step)
        return dialog

    @classmethod
    def gui_run(cls, gui_context, serialized_step):
        with hide_progress_dialog(gui_context):
            response, model = OpenQmlTableView.render(gui_context, 'SelectObjectsInitialize', serialized_step)
            context_id = response['context_id']
            list_gui_context = qml_action_dispatch.get_context(context_id)
            response = qml_action_step(list_gui_context, 'SelectObjectsFinalize', serialized_step)

            if hasattr(list_gui_context.view, 'objects'):
                return list_gui_context.view.objects
            raise CancelRequest()
