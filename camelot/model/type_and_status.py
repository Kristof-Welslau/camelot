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
Convenience classes to give entities a status, and create the needed related
status tables for each entity.  Status changes are tracked in a related status
history table.

Possible statuses can be defined as an enumeration or as a reference to a
table of related statuses.

Enumeration
-----------

In this setup there is a limited number of possible statuses an object can
have, this cannot be changed by the user of the application.

.. literalinclude:: ../../test/test_model.py
   :start-after: begin status enumeration definition
   :end-before: end status enumeration definition

Related status type table
-------------------------

In this setup, an additional table with possible status types is created.
The user of the application can modify this table and create additional
statuses as needed.

"""
import datetime

from sqlalchemy import orm, sql, schema, types
from sqlalchemy.ext import hybrid

from camelot.model.authentication import end_of_times
from camelot.admin.action import Action
from camelot.admin.entity_admin import EntityAdmin
from camelot.types import Enumeration, PrimaryKey
from camelot.core.orm.properties import EntityBuilder
from camelot.core.orm import Entity
from camelot.core.utils import ugettext_lazy as _
from camelot.view import action_steps
from camelot.view.filters import GroupBoxFilter, filter_data, filter_option

class StatusType( object ):
    """Mixin class to describe the different statuses an
    object can have
    """

    code = schema.Column( types.Unicode(10), index = True, nullable = False, unique = True )
    description = schema.Column( types.Unicode( 40 ), index = True )

    def __unicode__( self ):
        return self.code or ''

class StatusTypeAdmin( EntityAdmin ):
    list_display = ['code', 'description']
    form_display = ['code', 'description']

class StatusHistory( object ):
    """Mixin class to track the history of the status an object
    has.

    .. attribute:: status_datetime For statuses that occur at a specific point in time
    .. attribute:: status_from_date For statuses that require a date range
    .. attribute:: from_date When a status was enacted or set
    """

    status_datetime = schema.Column( types.Date, nullable = True )
    status_from_date = schema.Column( types.Date, nullable = True )
    status_thru_date = schema.Column( types.Date, nullable = True )
    from_date = schema.Column( types.Date, nullable = False, default = datetime.date.today )
    thru_date = schema.Column( types.Date, nullable = False, default = end_of_times )

class StatusHistoryAdmin( EntityAdmin ):
    list_display = ['status_from_date', 'status_thru_date', 'classified_by']

    def __unicode__( self ):
        return unicode(self.classified_by or u'')
    
    def get_depending_objects(self, obj):
        if obj.status_for is not None:
            yield obj.status_for

class Status( EntityBuilder ):
    """EntityBuilder that adds a related status table(s) to an `Entity`.

    These additional entities are created :

     * a `StatusType` this is the list of possible statuses an entity can have.
       If the `enumeration` parameter is used at construction, no such entity is
       created, and the list of possible statuses is limited to this enumeration.

     * a `StatusHistory` is the history of statusses an object has had.  The Status
       History refers to which `StatusType` was valid at a certain point in time.

    :param enumeration: if this parameter is used, no `StatusType` entity is created, 
        but the status type is described by the enumeration.  This parameter should
    be a list of all possible statuses the entity can have ::

    enumeration = [(1, 'draft'), (2,'ready')]

    :param status_history_table: the tablename to use to store the status
        history

    :param status_type_table: the tablename to use to starte the status types
    """

    def __init__( self, enumeration = None, 
                  status_history_table = None, status_type_table=None ):
        super( Status, self ).__init__()
        self.property = None
        self.enumeration = enumeration
        self.status_history_table = status_history_table
        self.status_type_table = status_type_table

    def attach( self, entity, name ):
        super( Status, self ).attach( entity, name )
        assert entity != Entity

        if self.status_history_table==None:
            self.status_history_table = entity.__name__.lower() + '_status'
        if self.status_type_table==None:
            self.status_type_table = entity.__name__.lower() + '_status_type'

        status_history_admin = type( entity.__name__ + 'StatusHistoryAdmin',
                                     ( StatusHistoryAdmin, ),
                                     { 'verbose_name':_(entity.__name__ + ' Status'),
                                       'verbose_name_plural':_(entity.__name__ + ' Statuses'), } )

        # use `type` instead of `class`, to give status type and history
        # classes a specific name, so these classes can be used whithin the
        # memento and the fixture module
        if self.enumeration is None:

            status_type_admin = type( entity.__name__ + 'StatusType',
                                      ( StatusTypeAdmin, ),
                                      { 'verbose_name':_(entity.__name__ + ' Status'),
                                        'verbose_name_plural':_(entity.__name__ + ' Statuses'), } )

            status_type = type( entity.__name__ + 'StatusType', 
                                (StatusType, entity._descriptor.entity_base,),
                                { '__tablename__':self.status_type_table,
                                  'Admin':status_type_admin } )	 

            foreign_key = schema.ForeignKey( status_type.id,
                                             ondelete = 'cascade', 
                                             onupdate = 'cascade')

            status_history = type( entity.__name__ + 'StatusHistory',
                                   ( StatusHistory, entity._descriptor.entity_base, ),
                                   {'__tablename__':self.status_history_table,
                                    'classified_by_id':schema.Column( PrimaryKey(), 
                                                                      foreign_key, 
                                                                      nullable = False ),
                                    'classified_by':orm.relationship( status_type ),
                                    'Admin':status_history_admin, } )

            self.status_type = status_type
            setattr( entity, '_%s_type'%name, self.status_type )

        else:

            status_history = type( entity.__name__ + 'StatusHistory',
                                   ( StatusHistory, entity._descriptor.entity_base, ),
                                   {'__tablename__':self.status_history_table,
                                    'classified_by':schema.Column( Enumeration( self.enumeration ), 
                                                                   nullable=False, index=True ),
                                    'Admin':status_history_admin,} )
            setattr( entity, '_%s_enumeration'%name, self.enumeration )

        self.status_history = status_history
        setattr( entity, '_%s_history'%name, self.status_history )

    def create_non_pk_cols( self ):
        table = orm.class_mapper( self.entity ).local_table
        for col in table.primary_key.columns:
            col_name = u'status_for_%s'%col.name
            if not hasattr( self.status_history, col_name ):
                constraint = schema.ForeignKey( col,
                                                ondelete = 'cascade', 
                                                onupdate = 'cascade')
                column = schema.Column( PrimaryKey(), constraint, nullable = False )
                setattr( self.status_history, col_name, column )

    def create_properties( self ):
        if not self.property:
            backref = orm.backref(self.name, cascade='all, delete, delete-orphan')
            self.property = orm.relationship(self.entity, backref = backref)
            self.status_history.status_for = self.property

class StatusMixin( object ):

    def get_status_from_date( self, classified_by ):
        """
        :param classified_by: the status for which to get the last `status_from_date`
        :return: the last date at which the status changed to `classified_by`, None if no such
            change occured yet
        """
        status_histories = [status_history for status_history in self.status if status_history.classified_by == classified_by]
        if len( status_histories ):
            status_histories.sort( key = lambda status_history:status_history.status_from_date, reverse = True )
            return status_histories[0].status_from_date

    def get_status_history_at( self, status_date = None ):
        """
        Get the StatusHistory valid at status_date

        :param status_date: the date at which the status history should
            be valid.  Use today if None was given.
        :return: a StatusHistory object or None if no valid status was
            found
        """
        if status_date == None:
            status_date = datetime.date.today()
        for status_history in self.status:
            if status_history.status_from_date <= status_date and status_history.status_thru_date >= status_date:
                return status_history	

    @staticmethod
    def current_status_query( status_history, status_class ):
        """
        :param status_history: the class or columns that represents the status history
        :param status_class: the class or columns of the class that have a status
        :return: a select statement that looks for the current status of the status_class
        """
        return sql.select( [status_history.classified_by],
                           whereclause = sql.and_( status_history.status_for_id == status_class.id,
                                                   status_history.status_from_date <= sql.functions.current_date(),
                                                   status_history.status_thru_date >= sql.functions.current_date() ),
                           from_obj = [status_history.table] ).order_by(status_history.id.desc()).limit(1)

    @hybrid.hybrid_property
    def current_status( self ):
        status_history = self.get_status_history_at()
        if status_history != None:
            return status_history.classified_by

    @current_status.expression
    def current_status_expression( cls ):
        return StatusMixin.current_status_query( cls._status_history, cls ).label( 'current_status' )

    def change_status( self, new_status, status_from_date=None, status_thru_date=end_of_times() ):
        from sqlalchemy import orm
        if not status_from_date:
            status_from_date = datetime.date.today()
        history_type = self._status_history
        session = orm.object_session( self )
        old_status_filter =  sql.and_( history_type.status_for == self,
                                       history_type.status_from_date <= status_from_date,
                                       history_type.status_thru_date >= status_from_date )
        old_status_query = session.query( history_type )
        old_status = old_status_query.filter( old_status_filter ).first()
        if old_status != None:
            old_status.thru_date = datetime.date.today() - datetime.timedelta( days = 1 )
            old_status.status_thru_date = status_from_date - datetime.timedelta( days = 1 )
        new_status = history_type( status_for = self,
                                   classified_by = new_status,
                                   status_from_date = status_from_date,
                                   status_thru_date = status_thru_date,
                                   from_date = datetime.date.today(),
                                   thru_date = end_of_times() )	
        session.flush()

class ChangeStatus( Action ):
    """
    An action that changes the status of an object
    :param new_status: the new status of the object
    :param verbose_name: the name of the action
    :return: a :class:`camelot.admin.action.Action` object that changes
    the status of a selection to the new status
    """

    def __init__( self, new_status, verbose_name = None ):
        self.verbose_name = verbose_name or _(new_status)
        self.new_status = new_status

    def model_run( self, model_context ):
        for obj in model_context.get_selection():
            obj.change_status( self.new_status )
            yield action_steps.UpdateObject(obj)
        yield action_steps.FlushSession( model_context.session )

class StatusFilter(GroupBoxFilter):
    """
    Filter to be used in a table view to enable filtering on the status
    of an object.  This filter will display all available statuses, and as
    such, needs not to query the distinct values used in the database to
    build up it's widget.
    
    :param attribute: the attribute that holds the status
    """
    
    def get_filter_data(self, admin):
        fa = admin.get_field_attributes(self.attribute)
        options = [ filter_option( name = _('All'),
                                   value = GroupBoxFilter.All,
                                   decorator = lambda q:q ) ]
        
        enumeration_attribute = '_%s_enumeration'%self.attribute
        for _id, name in getattr(admin.entity, enumeration_attribute):
            decorator = self.create_decorator(admin.entity.current_status, 
                                              fa, name, [])
            options.append(filter_option( name = name.capitalize(),
                                          value = name,
                                          decorator = decorator ))

        return filter_data( name = fa['name'],
                            options = options,
                            default = self.default )