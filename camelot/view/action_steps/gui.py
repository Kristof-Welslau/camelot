#  ============================================================================
#
#  Copyright (C) 2007-2013 Conceptive Engineering bvba. All rights reserved.
#  www.conceptive.be / info@conceptive.be
#
#  This file is part of the Camelot Library.
#
#  This file may be used under the terms of the GNU General Public
#  License version 2.0 as published by the Free Software Foundation
#  and appearing in the file license.txt included in the packaging of
#  this file.  Please review this information to ensure GNU
#  General Public Licensing requirements will be met.
#
#  If you are unsure which license is appropriate for your use, please
#  visit www.python-camelot.com or contact info@conceptive.be
#
#  This file is provided AS IS with NO WARRANTY OF ANY KIND, INCLUDING THE
#  WARRANTY OF DESIGN, MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE.
#
#  For use of this library in commercial applications, please contact
#  info@conceptive.be
#
#  ============================================================================

"""
Various ``ActionStep`` subclasses that manipulate the GUI of the application.
"""

from PyQt4 import QtGui, QtCore
from PyQt4.QtCore import Qt

from camelot.admin.action.base import ActionStep
from camelot.core.exception import CancelRequest
from camelot.core.utils import ugettext, ugettext_lazy as _
from camelot.view.controls import editors
from camelot.view.controls.inheritance import SubclassDialog
from camelot.view.controls.standalone_wizard_page import StandaloneWizardPage

class UpdateEditor(ActionStep):
    """This step should be used in the context of an editor action.  It
    will update an attribute of the editor.

    :param attribute: the name of the attribute of the editor to update
    :param value: the new value of the attribute
    """

    def __init__(self, attribute, value):
        self.attribute = attribute
        self.value = value

    def gui_run(self, gui_context):
        setattr(gui_context.editor, self.attribute, self.value)

class OpenFormView( ActionStep ):
    """Open the form view for a list of objects, in a non blocking way.

    :param objects: the list of objects to display in the form view, if objects
        is set to `None`, the model of the item view of the gui context is
        reused
    :param admin: the admin class to use to display the form

    .. attribute:: row

        Which object to display when opening the form, defaults to the first
        object, so row is 0 by default

    .. attribute:: actions

        A list of `camelot.admin.action.base.Action` objects to be displayed
        at the side of the form, this defaults to the ones returned by the
        admin

    .. attribute:: top_toolbar_actions

        A list of `camelot.admin.action.base.Action` objects to be displayed
        at the top toolbar of the form, this defaults to the ones returned by the
        admin
    """

    def __init__( self, objects, admin ):
        self.objects = objects
        self.admin = admin
        self.row = 0
        self.actions = admin.get_form_actions(None)
        get_form_toolbar_actions = admin.get_form_toolbar_actions
        self.top_toolbar_actions = get_form_toolbar_actions(Qt.TopToolBarArea)
        self.title = u' '
        self._columns = admin.get_fields()
        self._form_display = admin.get_form_display()

    def render(self, model, row):
        from camelot.view.controls.formview import FormView
        form = FormView(title=self.title, admin=self.admin, model=model,
                        columns=self._columns, form_display=self._form_display,
                        index=row)
        form.set_actions(self.actions)
        form.set_toolbar_actions(self.top_toolbar_actions)
        self.admin._apply_form_state( form )
        return form

    def gui_run( self, gui_context ):
        from camelot.view.proxy.queryproxy import QueryTableProxy
        from camelot.view.proxy.collection_proxy import CollectionProxy
        from camelot.view.workspace import show_top_level

        if self.objects is None:
            related_model = gui_context.item_view.model()
            #
            # depending on the type of related model, create a new model
            #
            row = gui_context.item_view.currentIndex().row()
            if isinstance( related_model, QueryTableProxy ):
                model = QueryTableProxy(
                    gui_context.admin,
                    related_model.get_query_getter(),
                    gui_context.admin.get_fields,
                    max_number_of_rows = 1,
                    cache_collection_proxy = related_model,
                )
            else:
                # no cache or sorting information is transferred
                model = CollectionProxy(
                    gui_context.admin,
                    related_model.get_collection,
                    gui_context.admin.get_fields,
                    max_number_of_rows = 1,
                )
                # get the unsorted row
                row = related_model.map_to_source( row )
        else:
            row = self.row
            def create_collection_getter( objects ):
                return lambda:objects

            model = CollectionProxy(
                self.admin,
                create_collection_getter(self.objects),
                self.admin.get_fields,
                max_number_of_rows=10
            )
        formview = self.render(model, row)
        show_top_level( formview, gui_context.workspace )

class SelectSubclass(ActionStep):
    """Allow the user to select a subclass out of a class hierarchy.  If the
    hierarch has only one class, this step returns immediately.

    :param admin: a :class:`camelot.admin.object_admin.ObjectAdmin` object

    yielding this step will return the admin for the subclass selected by the
    user.
    """

    def __init__(self, admin):
        self.admin = admin
        self.subclass_tree = admin.get_subclass_tree()

    def render(self):
        subclass_dialog = SubclassDialog(admin=self.admin,
                                         subclass_tree=self.subclass_tree)
        subclass_dialog.setWindowTitle(ugettext('Select'))
        return subclass_dialog

    def gui_run(self, gui_context):
        if not len(self.subclass_tree):
            return self.admin
        dialog = self.render()
        result = dialog.exec_()
        if result == QtGui.QDialog.Rejected:
            raise CancelRequest()
        return dialog.selected_subclass

class Refresh( ActionStep ):
    """Refresh all the open screens on the desktop, this will reload queries
    from the database"""

    def gui_run( self, gui_context ):
        if gui_context.workspace:
            gui_context.workspace.refresh()

class ItemSelectionDialog(StandaloneWizardPage):

    def __init__( self,
                  window_title=None,
                  autoaccept=False,
                  parent=None):
        """
        :param autoaccept: if True, the value of the ComboBox is immediately
        accepted after selecting it.
        """
        super(ItemSelectionDialog, self).__init__( window_title = window_title,
                                                   parent = parent )
        self.autoaccept = autoaccept
        self.set_default_buttons()
        layout = QtGui.QVBoxLayout()
        combobox = editors.ChoicesEditor()
        combobox.setObjectName( 'combobox' )
        combobox.editingFinished.connect( self._combobox_activated )
        layout.addWidget( combobox )
        self.main_widget().setLayout(layout)

    @QtCore.pyqtSlot()
    def _combobox_activated(self):
        if self.autoaccept:
            self.accept()

    def set_choices(self, choices):
        combobox = self.findChild( QtGui.QWidget, 'combobox' )
        if combobox != None:
            combobox.set_choices(choices)

    def get_value(self):
        combobox = self.findChild( QtGui.QWidget, 'combobox' )
        if combobox != None:
            return combobox.get_value()

    def set_value(self, value):
        combobox = self.findChild( QtGui.QWidget, 'combobox' )
        if combobox != None:
            return combobox.set_value(value)

class SelectItem( ActionStep ):
    """This action step pops up a single combobox dialog in which the user can
    select one item from a list of items.

    :param items: a list of tuples with values and the visible name of the items
       from which the user can select, such as `[(1, 'first'), (2,'second')]
    :param value: the value that should be selected when the dialog pops up
    :param autoaccept: if `True` the dialog closes immediately after the user
       selected an option.  When this is `False`, the user should press
       :guilabel:`OK` first.
    """

    def __init__( self, items, value=None ):
        self.items = items
        self.value = value
        self.autoaccept = True
        self.title =  _('Please select')
        self.subtitle = _('Make a selection and press the OK button')

    def render(self):
        dialog = ItemSelectionDialog( autoaccept = self.autoaccept )
        dialog.set_choices(self.items)
        dialog.set_value(self.value)
        dialog.setWindowTitle( unicode( self.title ) )
        dialog.set_banner_subtitle( unicode( self.subtitle ) )
        return dialog

    def gui_run(self, gui_context):
        dialog = self.render()
        result = dialog.exec_()
        if result == QtGui.QDialog.Rejected:
            raise CancelRequest()
        return dialog.get_value()

class ShowChart( ActionStep ):
    """Show a full screen chart.

    :param chart: a :class:`camelot.container.chartcontainer.FigureContainer` or
        :class:`camelot.container.chartcontainer.AxesContainer`
    """

    def __init__( self, chart ):
        self.chart = chart

    def gui_run( self, gui_context ):
        from camelot.view.controls.editors import ChartEditor
        ChartEditor.show_fullscreen_chart( self.chart,
                                           gui_context.workspace )


class ShowPixmap( ActionStep ):
    """Show a full screen pixmap

    :param pixmap: a :class:`camelot.view.art.Pixmap` object
    """

    def __init__( self, pixmap ):
        self.pixmap = pixmap

    def gui_run( self, gui_context ):
        from camelot.view.controls.liteboxview import LiteBoxView
        litebox = LiteBoxView( parent = gui_context.workspace )
        litebox.show_fullscreen_pixmap( self.pixmap.getQPixmap() )

class CloseView( ActionStep ):
    """
    Close the view that triggered the action, if such a view is available.

    :param accept: a boolean indicating if the view's widget should accept the
        close event.  This defaults to :const:`True`, when this is set to
        :const:`False`, the view will trigger it's corresponding close action
        instead of accepting the close event.  The close action might involve
        validating if the view can be closed, or requesting confirmation from
        the user.
    """

    def __init__( self, accept = True ):
        self.accept = accept

    def gui_run( self, gui_context ):
        view = gui_context.view
        if view != None:
            view.close_view( self.accept )

class ToFirstForm( ActionStep ):
    
    def gui_run( self, gui_context ):
        gui_context.widget_mapper.toFirst()

class ToNextForm( ActionStep ):
    
    def gui_run( self, gui_context ):
        gui_context.widget_mapper.toNext()
        
class ToLastForm( ActionStep ):
    
    def gui_run( self, gui_context ):
        gui_context.widget_mapper.toLast()
        
class ToPreviousForm( ActionStep ):
    
    def gui_run( self, gui_context ):
        gui_context.widget_mapper.toPrevious()

class MessageBox( ActionStep ):
    """
    Popup a :class:`QtGui.QMessageBox` and send it result back.  The arguments
    of this action are the same as those of the :class:`QtGui.QMessageBox`
    constructor.

    :param text: the text to be displayed within the message box
    :param icon: one of the :class:`QtGui.QMessageBox.Icon` constants
    :param title: the window title of the message box
    :param standard_buttons: the buttons to be displayed on the message box,
        out of the :class:`QtGui.QMessageBox.StandardButton` enumeration. by
        default an :guilabel:`Ok` and a button :guilabel:`Cancel` will be shown.

    When the :guilabel:`Cancel` button is pressed, this action step will raise
    a `CancelRequest`

    .. image:: /_static/listactions/import_from_file_confirmation.png

    """

    default_buttons = QtGui.QMessageBox.Ok | QtGui.QMessageBox.Cancel

    def __init__( self,
                  text,
                  icon = QtGui.QMessageBox.Information,
                  title = _('Message'),
                  standard_buttons = default_buttons ):
        self.icon = icon
        self.title = unicode( title )
        self.text = unicode( text )
        self.standard_buttons = standard_buttons
        self.informative_text = ''
        self.detailed_text = ''

    def render( self ):
        """create the message box. this method is used to unit test
        the action step."""
        message_box =  QtGui.QMessageBox( self.icon,
                                          self.title,
                                          self.text,
                                          self.standard_buttons )
        message_box.setInformativeText(unicode(self.informative_text))
        message_box.setDetailedText(unicode(self.detailed_text))
        return message_box

    def gui_run( self, gui_context ):
        message_box = self.render()
        result = message_box.exec_()
        if result == QtGui.QMessageBox.Cancel:
            raise CancelRequest()
        return result

