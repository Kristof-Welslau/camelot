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

import logging

from ...admin.action.base import ActionStep
from ...core.qt import QtCore, Qt, QtWidgets

LOGGER = logging.getLogger(__name__)


class Exit( ActionStep ):
    """
    Stop the event loop, and exit the application
    """
    
    def __init__( self, return_code=0 ):
        self.return_code = return_code
        
    def gui_run( self, gui_context ):
        QtCore.QCoreApplication.exit(self.return_code)

class MainWindow( ActionStep ):
    """
    Open a top level application window
    
    :param admin: a :class:`camelot.admin.application_admin.ApplicationAdmin'
        object

    .. attribute:: window_title

        The title of the main window, defaults to the application name if `None`
        is given

    """
    
    def __init__(self, admin):
        self.admin = admin
        self.window_title = admin.get_name()

    def render( self, gui_context ):
        """create the main window. this method is used to unit test
        the action step."""
        from ..mainwindowproxy import MainWindowProxy

        main_window_context = gui_context.copy()
        main_window_context.progress_dialog = None
        main_window_context.admin = self.admin

        # Check if a QMainWindow already exists
        window = None
        app = QtWidgets.QApplication.instance()
        for widget in app.allWidgets():
            if isinstance(widget, QtWidgets.QMainWindow):
                # Make sure a QMainWindow is reused only once
                if not hasattr(widget, '_reused_by_view_action_steps_application'):
                    widget._reused_by_view_action_steps_application = True
                    window = widget
                    break

        main_window_proxy = MainWindowProxy( gui_context=main_window_context, window=window )

        gui_context.workspace = main_window_context.workspace
        main_window_proxy.parent().setWindowTitle( self.window_title )
        return main_window_proxy.parent()
        
    def gui_run( self, gui_context ):
        main_window = self.render( gui_context )
        if main_window.statusBar() is not None:
            main_window.statusBar().hide()
        main_window.show()

class NavigationPanel(ActionStep):
    """
    Create a panel to navigate the application
    
    :param sections: a list of :class:`camelot.admin.section.Section'
        objects, with the sections of the navigation panel

    """
     
    def __init__( self, sections ):
        self.sections = [{
            'verbose_name': str(section.get_verbose_name()),
            'icon': section.get_icon().getQIcon(),
            'items': section.get_items()
        } for section in sections]

    def render( self, gui_context ):
        """create the navigation panel.
        this method is used to unit test the action step."""
        from ..controls.section_widget import NavigationPane
        navigation_panel = NavigationPane(
            gui_context,
            gui_context.workspace
        )
        navigation_panel.set_sections(self.sections)
        return navigation_panel
    
    def gui_run( self, gui_context ):
        navigation_panel = self.render(gui_context)
        gui_context.workspace.parent().addDockWidget(
            Qt.LeftDockWidgetArea, navigation_panel
        )

class MainMenu(ActionStep):
    """
    Create a main menu for the application window.
    
    :param menu: a list of :class:`camelot.admin.menu.Menu' objects

    """
     
    def __init__( self, menu ):
        self.menu = menu

    def gui_run( self, gui_context ):
        from ..mainwindowproxy import MainWindowProxy
        main_window = gui_context.workspace.parent()
        if main_window is None:
            return
        main_window_proxy = main_window.findChild(MainWindowProxy)
        if main_window_proxy is not None:
            main_window_proxy.set_main_menu(self.menu)


class InstallTranslator(ActionStep):
    """
    Install a translator in the application.  Ownership of the translator will
    be moved to the application.

    :param admin: a :class:`camelot.admin.application_admin.ApplicationAdmin'
        object

    """

    def __init__(self, admin):
        self.admin = admin

    def gui_run(self, gui_context):
        app = QtCore.QCoreApplication.instance()
        translator = self.admin.get_translator()
        if isinstance(translator, list):
            for t in translator:
                t.setParent(app)
                app.installTranslator(t)
        else:
            app.installTranslator(translator)


class RemoveTranslators(ActionStep):
    """
    Unregister all previously installed translators from the application.

    :param admin: a :class:`camelot.admin.application_admin.ApplicationAdmin'
        object
    """

    def __init__(self, admin):
        self.admin = admin

    def gui_run(self, gui_context):
        app = QtCore.QCoreApplication.instance()
        for active_translator in app.findChildren(QtCore.QTranslator):
            app.removeTranslator(active_translator)


class UpdateActionsState(ActionStep):
    """
    Update the the state of a list of `Actions`

    :param action_states: a `dict` mapping the action_routes to their
        updated state.

    """

    def __init__(self, actions_state):
        self.actions_state = actions_state

    def gui_run(self, gui_context):
        for action_route, action_state in self.actions_state.items():
            rendered_action_route = gui_context.action_routes.get(action_route)
            if rendered_action_route is None:
                LOGGER.warn('Cannot update rendered action, rendered_action_route is unknown')
                continue
            qobject = gui_context.view.findChild(QtCore.QObject, rendered_action_route)
            if qobject is None:
                LOGGER.warn('Cannot update rendered action, QObject child {} not found'.format(rendered_action_route))
                continue
            qobject.set_state(action_state)
