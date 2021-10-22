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

from ....admin.action.base import RenderHint
from ....admin.admin_route import AdminRoute
from ....core.qt import QtGui, QtCore, QtWidgets, variant_to_py, Qt

from camelot.admin.action import FieldActionGuiContext
from camelot.view.proxy import ValueLoading

from ..action_widget import ActionToolbutton


def set_background_color_palette(widget, background_color):
    """
    Set the palette of a widget to have a cerain background color.
    :param widget: a QWidget
    :param background_color: a QColor
    """
    #
    # WARNING : Changing this code requires extensive testing of all editors
    # in all states on all platforms (Mac, Linux, Win XP, Win Vista, Win 7)
    #
    if background_color not in (None, ValueLoading):
        palette = QtGui.QPalette(widget.palette())
        for x in [QtGui.QPalette.ColorGroup.Active, QtGui.QPalette.ColorGroup.Inactive,
                  QtGui.QPalette.ColorGroup.Disabled]:
            #
            # backgroundRole : role that is used to render the background, If
            #                  role is QPalette.ColorRole.NoRole, then the widget
            #                  inherits its parent's background role
            # Window : general background color
            # Base : background color for text entry widgets
            #
            for y in [widget.backgroundRole(), QtGui.QPalette.ColorRole.Window,
                      QtGui.QPalette.ColorRole.Base]:
                palette.setColor(x, y, background_color)
        widget.setPalette(palette)
    else:
        widget.setPalette(QtWidgets.QApplication.palette())


class AbstractCustomEditor(object):
    """
    Helper class to be used to build custom editors.
    This class provides functionality to store and retrieve
    `ValueLoading` as an editor's value.

    Guidelines for implementing CustomEditors :

    * When an editor consists of multiple widgets, one widget must be the
      focusProxy of the editor, to have that widget immediately activated when
      the user single clicks in the table view.

    * When an editor has widgets that should not get selected when the user
      tabs through the editor, setFocusPolicy(Qt.FocusPolicy.ClickFocus) should be called
      on those widgets.

    * Editor should set their size policy, for most editor this means their
      vertical size policy should be  `QtWidgets.QSizePolicy.Policy.Fixed`
    """

    def __init__(self):
        self.setProperty('value_loading', True)
        self.field_attributes = {}
        self.field_label = None

    def set_label(self, label):
        self.field_label = label
        # set label might be called after a set_field_attributes, so
        # immediately update the attributes of the label
        self.field_label.set_field_attributes(**self.field_attributes)

    def set_value(self, value):
        if value is ValueLoading:
            self.setProperty('value_loading', True)
            return None
        else:
            self.setProperty('value_loading', False)
            return value

    def get_value(self):
        if variant_to_py(self.property('value_loading')):
            return ValueLoading
        return None

    def get_field_attributes(self):
        return self.field_attributes

    def set_field_attributes(self, **kwargs):
        self.set_background_color(kwargs.get('background_color', None))
        self.field_attributes = kwargs
        self.setVisible(kwargs.get('visible', True))
        if self.field_label is not None:
            self.field_label.set_field_attributes(**kwargs)

    def set_background_color(self, background_color):
        set_background_color_palette(self, background_color)

    def render_action(self, action, parent):
        if action.render_hint == RenderHint.TOOL_BUTTON:
            button = ActionToolbutton(action, self.gui_context, parent)
            button.setAutoRaise(True)
            button.setFocusPolicy(Qt.FocusPolicy.ClickFocus)
            return button
        raise Exception('Unhandled render hint {} for {}'.format(action.render_hint, type(action)))


class CustomEditor(QtWidgets.QWidget, AbstractCustomEditor):
    """
    Base class for implementing custom editor widgets.
    This class provides dual state functionality.  Each
    editor should have the posibility to have `ValueLoading`
    as its value, specifying that no value has been set yet.
    """

    editingFinished = QtCore.qt_signal()
    valueChanged = QtCore.qt_signal()
    completionPrefixChanged = QtCore.qt_signal(str)

    _font_height = None
    _font_width = None

    def __init__(self, parent, column_width=None):
        QtWidgets.QWidget.__init__(self, parent)
        AbstractCustomEditor.__init__(self)
        self.gui_context = FieldActionGuiContext()
        self.gui_context.editor = self
        self.gui_context.admin_route = None

        if CustomEditor._font_width is None:
            font_metrics = QtGui.QFontMetrics(self.font())
            CustomEditor._font_height = font_metrics.height()
            CustomEditor._font_width = font_metrics.averageCharWidth()

        if column_width is None:
            self.size_hint_width = None
        else:
            self.size_hint_width = column_width * CustomEditor._font_width

    def get_height(self):
        """
        Get the 'standard' height for a cell
        """
        return self.contentsRect().height()

    def add_actions(self, action_routes, layout):
        for action_route in action_routes:
            action = AdminRoute.action_for(action_route)
            action_widget = self.render_action(action, self)
            action_widget.action_route = action_route
            action_widget.setFixedHeight(self.get_height())
            layout.addWidget(action_widget)

    def sizeHint(self):
        size_hint = super(CustomEditor, self).sizeHint()
        if self.size_hint_width is not None:
            size_hint.setWidth(max(size_hint.width(), self.size_hint_width))
        return size_hint

