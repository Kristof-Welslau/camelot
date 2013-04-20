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

"""The ORM part of the classes that store the change history of objects to
the database.  The table defined here is used in :mod:`camelot.core.memento` 
to store the changes.

To prevent this table to be used to store changes, overwrite the 
:meth:`camelot.admin.application_admin.ApplicationAdmin.get_memento` method
the custom `ApplicationAdmin`.
"""

import datetime

import six

from sqlalchemy import schema, orm
from sqlalchemy.types import Unicode, Integer, DateTime, PickleType

from camelot.admin.entity_admin import EntityAdmin
from camelot.admin.object_admin import ObjectAdmin
from camelot.admin.not_editable_admin import not_editable_admin
from camelot.core.orm import Entity, ManyToOne
from camelot.core.utils import ugettext_lazy as _
from camelot.view import filters
from camelot.view.controls import delegates

from .authentication import AuthenticationMechanism

class PreviousAttribute( object ):
    """Helper class to display previous attributes"""
    
    def __init__( self, attribute, previous_value ):
        self.attribute = attribute
        self.previous_value = six.text_type( previous_value )
        
    class Admin( ObjectAdmin ):
        list_display = ['attribute', 'previous_value']
        
class Memento( Entity ):
    """Keeps information on the previous state of objects, to keep track
    of changes and enable restore to that previous state"""
    
    __tablename__ = 'memento'
    
    model = schema.Column( Unicode( 256 ), index = True, nullable = False )
    primary_key = schema.Column( Integer(), index = True, nullable = False )
    creation_date = schema.Column( DateTime(), default = datetime.datetime.now )
    authentication = ManyToOne( AuthenticationMechanism,
                                required = True,
                                ondelete = 'restrict',
                                onupdate = 'cascade' )
    memento_type = schema.Column( Integer, 
                                  nullable = False,
                                  index = True )    
    previous_attributes = orm.deferred( schema.Column( PickleType() ) )
    
    @property
    def previous( self ):
        previous = self.previous_attributes
        if previous:
            return [PreviousAttribute(k,v) for k,v in previous.items()]
        return []
    
    class Admin( EntityAdmin ):
        verbose_name = _( 'History' )
        verbose_name_plural = _( 'History' )
        list_display = ['creation_date', 'authentication', 'model',
                        'primary_key', ]
        form_display = list_display + ['previous']
        list_filter = [filters.ComboBoxFilter('model')]
        field_attributes = {'previous':{'target':PreviousAttribute,
                                        'delegate':delegates.One2ManyDelegate,
                                        'python_type':list}
                            }
        
    Admin = not_editable_admin( Admin )

