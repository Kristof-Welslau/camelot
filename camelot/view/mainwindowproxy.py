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
logger = logging.getLogger('camelot.view.mainwindow')

from ..core.qt import (
    QtWidgets, QtCore, py_to_variant, variant_to_py, transferto
)

from camelot.view.controls.busy_widget import BusyWidget


class MainWindowProxy(QtCore.QObject):
    """Proxy for a main window of a Desktop Camelot application
    
    :param gui_context: an :class:`camelot.admin.action.application_action.ApplicationActionGuiContext`
        object
    :param window: a :class:`QtWidgets.QMainWindow` object or :class:`None`
    
    If window is None, a new QMainWindow will be created.
    The QMainWindow will be set as parent of this QObject.
    """

    def __init__(self, gui_context, window=None):
        from .workspace import DesktopWorkspace
        logger.debug('initializing main window')
        QtCore.QObject.__init__(self)
        assert isinstance(gui_context.admin_route, tuple)

        if window is None:
            window = QtWidgets.QMainWindow()

        # make the QMainWindow the parent of this QObject
        self.setParent(window)
        # prevent garbage collection of the mainwindow, by keeping it
        # out of the garbage collection cyle
        transferto(window, window)
        # install event filter to capture close event
        window.installEventFilter(self)
        logger.debug('setting up workspace')
        self.gui_context = gui_context
        self.workspace = DesktopWorkspace(gui_context.admin_route, window )
        self.gui_context.workspace = self.workspace

        logger.debug('setting child windows dictionary')

        logger.debug('setting central widget to our workspace')
        window.setCentralWidget( self.workspace )
        self.workspace.view_activated_signal.connect( self.view_activated )
        logger.debug('reading saved settings')
        self.read_settings()
        logger.debug('initialization complete')

    def read_settings( self ):
        """Restore the geometry of the main window to its last saved state"""
        settings = QtCore.QSettings()
        geometry = variant_to_py( settings.value('geometry') )
        if geometry:
            self.parent().restoreGeometry( geometry )

    def write_settings(self):
        """Store the current geometry of the main window"""
        logger.debug('writing application settings')
        settings = QtCore.QSettings()
        settings.setValue('geometry', py_to_variant(self.parent().saveGeometry()))
        logger.debug('settings written')

    @QtCore.qt_slot( object )
    def set_main_menu( self, main_menu ):
        """Set the main menu
        :param main_menu: a list of :class:`camelot.admin.menu.Menu` objects,
            as returned by the :meth:`camelot.admin.application_admin.ApplicationAdmin.get_main_menu`
            method.
        """
        if main_menu == None:
            return
        menu_bar = self.parent().menuBar()
        for menu in main_menu:
            menu_bar.addMenu( menu.render( self.gui_context, menu_bar ) )
        menu_bar.setCornerWidget( BusyWidget() )

    def get_gui_context( self ):
        """Get the :class:`GuiContext` of the active view in the mainwindow,
        or the :class:`GuiContext` of the application.

        :return: a :class:`camelot.admin.action.base.GuiContext`
        """
        active_view = self.gui_context.workspace.active_view()
        if active_view:
            return active_view.gui_context
        return self.gui_context
        
    @QtCore.qt_slot()
    def view_activated( self ):
        pass

    def eventFilter(self, qobject, event):
        if event.type() == QtCore.QEvent.Close:
            from camelot.view.model_thread import get_model_thread
            model_thread = get_model_thread()
            self.workspace.close_all_views()
            self.write_settings()
            logger.info( 'closing mainwindow' )
            model_thread.stop()
            QtCore.QCoreApplication.exit(0)

        # allow events to propagate
        return False
