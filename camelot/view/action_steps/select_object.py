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

from ...core.qt import Qt, QtWidgets

from camelot.admin.action import ActionStep, Action
from camelot.core.exception import CancelRequest
from camelot.core.utils import ugettext as _
from camelot.view.art import FontIcon
from camelot.view.action_runner import hide_progress_dialog
from camelot.view.controls.tableview import TableView

from .item_view import OpenTableView

class SetSelectedObjects(ActionStep):

    def __init__(self, objects):
        self.objects = objects

    def gui_run(self, gui_context):
        dialog = gui_context.view.parent()
        dialog.objects = self.objects
        dialog.accept()

class ConfirmSelection(Action):

    verbose_name = _('OK')
    icon = FontIcon('check') # 'tango/16x16/emblems/emblem-symbolic-link.png'

    def model_run(self, model_context):
        yield SetSelectedObjects(list(model_context.get_selection()))

class CancelSelection(Action):

    verbose_name = _('Cancel')

    def gui_run(self, gui_context):
        gui_context.view.parent().reject()

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
        layout.addWidget(table)
        self.setLayout( layout )
        self.objects = []

class SelectObjects( OpenTableView ):
    """Select one or more object from a query.  The `yield` of this action step
    return a list of objects.

    :param admin: a :class:`camelot.admin.object_admin.ObjectAdmin` object
    :param search_text: a default string on which to search for in the selection
        dialog
    :param value: a query or a list of object from which the selection should
        be made.  If none is given, the default query from the admin is taken.
    """

    def __init__(self, admin, search_text=None, value=None):
        if value is None:
            value = admin.get_query()
        super(SelectObjects, self).__init__(admin, value)
        self.search_text = search_text
        self.verbose_name_plural = str(admin.get_verbose_name_plural())
        self.list_actions = [CancelSelection(), ConfirmSelection()]
        self.left_toolbar_actions = admin.get_select_list_toolbar_actions(Qt.LeftToolBarArea)
        self.right_toolbar_actions = admin.get_select_list_toolbar_actions(Qt.RightToolBarArea)
        self.top_toolbar_actions = admin.get_select_list_toolbar_actions(Qt.TopToolBarArea)
        self.bottom_toolbar_actions = admin.get_select_list_toolbar_actions(Qt.BottomToolBarArea)
        self.list_action = ConfirmSelection()

    def render(self, gui_context):
        dialog = SelectDialog(gui_context, self.admin_route, self.verbose_name_plural)
        table_view = dialog.findChild(QtWidgets.QWidget, 'table_view')
        self.update_table_view(table_view)
        return dialog

    def gui_run( self, gui_context ):
        dialog = self.render(gui_context)
        with hide_progress_dialog(gui_context):
            # strange things happen on windows 7 and later with maximizing
            # this dialog, maximizing it here appears to work
            dialog.showMaximized()
            if dialog.exec_() == QtWidgets.QDialog.Rejected:
                raise CancelRequest()
            return dialog.objects


