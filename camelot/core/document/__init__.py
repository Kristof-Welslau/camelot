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
"""Decorators to enhance the docstrings of classes
"""

import six

def documented_entity():
    """Class decorator to append an image of the default view for
  an entity to an entity class.  The image can be generated by using
  the testing framework to create images of all default views in an
  application ::

    @documented_entity()
    class Movie(Entity):
      '''A movie as played in the theater'''
      title = Field(Unicode(50))

  The resulting docstring of the Movie entity will be ::

    '''A movie as played in the theater

    image ../_static/entityviews/new_view_movie.png
    '''
  """

    def document_field( key, field ):
        from camelot.core.orm import Field
        from camelot.core.orm.relationships import Relationship
        if isinstance(field, Field):
            nullable = field.kwargs.get('nullable', True)
            required = {True:'not required', False:'required'}[nullable]
            return '%s : %s, %s'%(key, six.text_type(field.type), required)
        if isinstance(field, Relationship):
            return '%s : refers to %s'%(key, six.text_type(field.of_kind))
        
    def document_entity(model):
        #
        # Add documentation on its fields
        #
        documented_fields = []
        
        for key, value in model.__dict__.items():
            doc = document_field( key, value )
            if doc:
                documented_fields.append( doc )
                
        model.__doc__ = (model.__doc__ or '') + """

.. image:: /_static/entityviews/new_view_%s.png


**Fields** :

        """%(model.__name__.lower()) + ''.join('\n * %s'%(doc) for doc in documented_fields)
        return model

    return document_entity

