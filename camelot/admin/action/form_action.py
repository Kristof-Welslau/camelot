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

import six

from ...core.qt import QtGui, QtWidgets, is_deleted
from camelot.admin.action.base import Action, GuiContext
from camelot.core.orm.entity import EntityFacade
from camelot.core.utils import ugettext as _
from camelot.view.art import FontIcon

from .application_action import ( ApplicationActionGuiContext,
                                 ApplicationActionModelContext )
from . import list_action
from .base import RenderHint

class FormActionModelContext( ApplicationActionModelContext ):
    """On top of the attributes of the 
    :class:`camelot.admin.action.application_action.ApplicationActionModelContext`, 
    this context contains :
        
    .. attribute:: current_row
    
        the row in the list that is currently displayed in the form
        
    .. attribute:: collection_count
    
        the number of objects that can be reached in the form.
        
    .. attribute:: selection_count
    
        the number of objects displayed in the form, at most 1.
                
    .. attribute:: session
    
        The session to which the objects in the list belong.

    .. attribute:: proxy

        A :class:`camelot.core.item_model.AbstractModelProxy` object that gives
        access to the objects in the list

    The :attr:`selection_count` attribute allows the 
    :meth:`model_run` to quickly evaluate the size of the collection without 
    calling the potetially time consuming method :meth:`get_collection`.
    """
    
    def __init__( self ):
        super( FormActionModelContext, self ).__init__()
        self.proxy = None
        self.admin = None
        self.current_row = None
        self.collection_count = 0
        self.selection_count = 0
        
    def get_object( self ):
        """
        :return: the object currently displayed in the form, None if no object
            is displayed yet
        """
        for obj in self.get_selection():
            return obj

    def get_collection( self, yield_per = None ):
        """
        :param yield_per: an integer number giving a hint on how many objects
            should fetched from the database at the same time.
        :return: a generator over the objects in the list
        """
        for obj in self.proxy[0, self.collection_count]:
            yield obj
            
    def get_selection( self, yield_per = None ):
        """
        Method to be compatible with a 
        :class:`camelot.admin.action.list_action.ListActionModelContext`, this
        allows creating a single Action to be used on a form and on list.
        
        :param yield_per: this parameter has no effect, it's here only for
            compatibility with :meth:`camelot.admin.action.list_action.ListActionModelContext.get_selection`
        :return: a generator that yields the current object displayed in the 
            form and does not yield anything if no object is displayed yet
            in the form.
        """
        if self.selection_count:
            for obj in self.proxy[self.current_row:self.current_row+1]:
                yield obj

class FormActionGuiContext( ApplicationActionGuiContext ):
    """The context for an :class:`Action` on a form.  On top of the attributes of the 
    :class:`camelot.admin.action.application_action.ApplicationActionGuiContext`, 
    this context contains :

    .. attribute:: widget_mapper

       the :class:`QtGui.QDataWidgetMapper` class that relates the form 
       widget to the model.
       
    .. attribute:: view
    
       a :class:`camelot.view.controls.view.AbstractView` class that represents
       the view in which the action is triggered.
       
    """
        
    model_context = FormActionModelContext
    
    def __init__(self):
        super( FormActionGuiContext, self ).__init__()
        self.widget_mapper = None
        self.view = None
        # temporary admin, so be able to do a cleanup context by context
        self.admin = None

    def get_progress_dialog(self):
        return GuiContext.get_progress_dialog(self)

    def get_window(self):
        if self.view is not None and not is_deleted(self.view):
            return self.view.window()
        return super(FormActionGuiContext, self).get_window()

    def create_model_context(self):
        context = super( FormActionGuiContext, self ).create_model_context()
        # temporary admin, so be able to do a cleanup context by context
        context.admin = self.admin
        context.proxy = self.widget_mapper.model().get_value()
        current_index = self.widget_mapper.currentIndex()
        if current_index >= 0:
            context.current_row = current_index
            context.selection_count = 1
        return context
        
    def copy(self, base_class = None):
        new_context = super( FormActionGuiContext, self ).copy( base_class )
        new_context.widget_mapper = self.widget_mapper
        new_context.view = self.view
        # temporary admin, so be able to do a cleanup context by context
        new_context.admin = self.admin
        return new_context

class ShowHistory( Action ):

    render_hint = RenderHint.TOOL_BUTTON
    icon = FontIcon('history') # 'tango/16x16/actions/format-justify-fill.png'
    verbose_name = _('History')
    tooltip = _('Show recent changes on this form')
        
    def model_run( self, model_context ):
        from ..object_admin import ObjectAdmin
        from ...view import action_steps
        from ...view.controls import delegates
            
        obj = model_context.get_object()
        memento = model_context.admin.get_memento()
        subsystem_obj = model_context.admin.get_subsystem_object(obj)
        
        class ChangeAdmin( ObjectAdmin ):
            verbose_name = _('Change')
            verbose_name_plural = _('Changes')
            list_display = ['at', 'by', 'memento_type', 'changes']
            field_attributes = {'at':{'delegate':delegates.DateTimeDelegate},
                                'memento_type':{'delegate':delegates.ComboBoxDelegate,
                                                'choices':memento.memento_types,
                                                'name':_('Type')} }
    
            def get_related_toolbar_actions( self, toolbar_area, direction ):
                return []
            
        if obj != None:
            primary_key = model_context.admin.primary_key( obj )
            if primary_key is not None:
                if None not in primary_key:
                    changes = list( memento.get_changes( model = six.text_type( subsystem_obj.__class__.__name__ ),
                                                         primary_key = primary_key,
                                                         current_attributes = {} ) )
                    admin = ChangeAdmin( model_context.admin, object )
                    step = action_steps.ChangeObjects( changes, admin )
                    step.icon = FontIcon('history') # 'tango/16x16/actions/format-justify-fill.png'
                    step.title = _('Recent changes')
                    step.subtitle = model_context.admin.get_verbose_identifier( obj )
                    yield step
        
class CloseForm( Action ):
    """Validte the form can be closed, and close it"""

    render_hint = RenderHint.TOOL_BUTTON
    shortcut = QtGui.QKeySequence.Close
    icon = FontIcon('times-circle') # 'tango/16x16/actions/system-log-out.png'
    verbose_name = _('Close')
    tooltip = _('Close this form')
    
    def step_when_valid(self):
        """
        :return: the `ActionStep` to take when the current object is valid
        """
        from camelot.view import action_steps
        return action_steps.CloseView()
    
    def gui_run( self, gui_context ):
        if not is_deleted(gui_context.widget_mapper):
            gui_context.widget_mapper.submit()
        super( CloseForm, self ).gui_run( gui_context )
        
    def model_run( self, model_context ):
        from camelot.view import action_steps
        yield action_steps.UpdateProgress( text = _('Closing form') )
        validator = model_context.admin.get_validator()
        obj = model_context.get_object()
        admin  = model_context.admin
        subsystem_obj = admin.get_subsystem_object(obj)
        if obj is None:
            yield self.step_when_valid()
            return
        #
        # validate the object, and if the object is valid, simply close
        # the view
        #
        messages = validator.validate_object( obj )
        valid = ( len( messages ) == 0 )
        if valid:
            yield self.step_when_valid()
        else:
            #
            # if the object is not valid, request the user what to do
            #
            message = action_steps.MessageBox( '\n'.join( messages ),
                                               QtWidgets.QMessageBox.Warning,
                                               _('Invalid form'),
                                               QtWidgets.QMessageBox.Ok | QtWidgets.QMessageBox.Discard )
            reply = yield message
            if reply == QtWidgets.QMessageBox.Discard:
                if admin.is_persistent( obj ):
                    admin.refresh( obj )
                    yield action_steps.UpdateObjects((subsystem_obj,))
                else:
                    depending_objects = list(admin.get_depending_objects(obj))
                    model_context.proxy.remove(subsystem_obj)
                    yield action_steps.DeleteObjects((subsystem_obj,))
                    admin.expunge(obj)
                    yield action_steps.UpdateObjects(depending_objects)
                # only close the form after the object has been discarded or
                # deleted, to avoid yielding action steps after the widget mapper
                # has been garbage collected
                yield self.step_when_valid()
    
class ToPreviousForm( list_action.AbstractToPrevious, CloseForm ):
    """Move to the previous form"""

    def step_when_valid(self):
        from camelot.view import action_steps
        return action_steps.ToPreviousForm()

class ToFirstForm( list_action.AbstractToFirst, CloseForm ):
    """Move to the form"""
    
    def step_when_valid(self):
        from camelot.view import action_steps
        return action_steps.ToFirstForm()

class ToNextForm( list_action.AbstractToNext, CloseForm ):
    """Move to the next form"""

    def step_when_valid(self):
        from camelot.view import action_steps
        return action_steps.ToNextForm()

class ToLastForm( list_action.AbstractToLast, CloseForm ):
    """Move to the last form"""

    def step_when_valid(self):
        from camelot.view import action_steps
        return action_steps.ToLastForm()

def structure_to_form_actions( structure ):
    """Convert a list of python objects to a list of form actions.
    If the python object is an instance of as Action, it is kept as is.
    """

    def object_to_action( o ):
        assert isinstance( o, Action )
        return o

    return [object_to_action( o ) for o in structure]



