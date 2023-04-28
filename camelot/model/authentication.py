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

"""Set of classes to store authentication and permissions
"""
import base64
import datetime
import threading

from sqlalchemy import types, orm, schema, sql
from sqlalchemy.schema import Column, ForeignKey

import camelot.types

from ..core.exception import UserException
from ..core.qt import QtCore, QtGui
from ..core.orm import Entity
from ..core.sql import metadata

END_OF_TIMES = datetime.date( year = 2400, month = 12, day = 31 )

#
# Enumeration of the types of authentication supported
#
authentication_types = [
    (1, 'operating_system'),
    (2, 'database')
]

def end_of_times():
    return END_OF_TIMES


#
# Enumeration for the roles in an application
#
roles = []


class Authentication(threading.local):

    def __init__(self):
        self.clear()

    def has_role(self, role_name):
        """
        :param role_name: a string with the name of the role
        :return; `True` if the user is associated to this role, otherwise 
            `False`.
        """
        assert role_name in [r[1] for r in roles]
        return role_name in self.roles

    def clear(self):
        self.authentication_type = None
        self.username = None
        self.authentication_mechanism_id = None
        self.roles = []

    def __str__(self):
        if self.username is not None:
            return self.username
        return ''

_current_authentication_ = Authentication()

class AuthenticationMechanism( Entity ):
    
    __tablename__ = 'authentication_mechanism'
    
    authentication_type = Column(
        camelot.types.Enumeration(authentication_types),
        nullable = False, index = True , default = authentication_types[0][1]
    )
    username = Column( types.Unicode( 40 ), nullable = False, index = True, unique = True )
    password = Column( types.Unicode( 200 ), nullable = True, index = False, default = None )
    from_date = Column( types.Date(), default = datetime.date.today, nullable = False, index = True )
    thru_date = Column( types.Date(), default = end_of_times, nullable = False, index = True )
    last_login = Column( types.DateTime() )
    representation = orm.deferred(Column(types.Text(), nullable=True))

    @classmethod
    def get_current_authentication(cls) -> Authentication:
        """
        Get the currently logged in :class:'AuthenticationMechanism', within
        a specific session.
        """
        if _current_authentication_.authentication_mechanism_id is None:
            raise UserException("Current user is not authenticated")
        return _current_authentication_

    @classmethod
    def authenticate(cls, session, authenication_type, username, groups):
        """
        Authenticate a user and set the current authentication
        """
        assert session is not None
        authentication_mechanism = cls.get_or_create(session, username)
        _current_authentication_.username = username
        _current_authentication_.authentication_mechanism_id = authentication_mechanism.id
        authentication_mechanism.last_login = sql.func.now()
        role_ids = set()
        for group in session.query(AuthenticationGroup).filter(AuthenticationGroup.name.in_(groups)).all():
            for group_role in group.roles:
                role_ids.add(group_role.role_id)
        for role_id, role_name in roles:
            if role_id in role_ids:
                _current_authentication_.roles.append(role_name)
        session.flush()

    @classmethod
    def clear_authentication(cls):
        _current_authentication_.clear()

    @classmethod
    def set_current_authentication(cls, session):
        """
        Get the currently logged in :class:'AuthenticationMechanism', within
        a specific session.
        """
        global _current_authentication_

    @classmethod
    def get_or_create(cls, session, username):
        authentication_mechanism = session.query(cls).filter_by(username = username).first()
        if not authentication_mechanism:
            authentication_mechanism = cls(username = username, _session=session)
            session.flush()
        return authentication_mechanism

    def get_representation(self):
        """
        :return: a :class:`QtGui.QImage` object with the avatar of the user,
            or `None`.
        """
        if self.representation is None:
            return self.representation
        return QtGui.QImage.fromData(base64.b64decode(self.representation))
    
    def set_representation(self, image):
        """
        :param image: a :class:`QtGui.QImage` object with the avatar of the user,
            or `None`.
        """
        if image is None:
            self.representation=None
        qbyte_array = QtCore.QByteArray()
        qbuffer = QtCore.QBuffer( qbyte_array )
        image.save( qbuffer, 'PNG' )
        self.representation=qbyte_array.toBase64().data().decode()
        
    def __str__(self):
        return self.username or ''


class AuthenticationGroup( Entity ):
    """A group of users (defined by their :class:`AuthenticationMechanism`).
    Different roles can be assigned to a group.
    """
    
    __tablename__ = 'authentication_group'
    
    name = Column( types.Unicode(256), nullable=False )
    
    def __getattr__( self, name ):
        for role_id, role_name in roles:
            if role_name == name:
                for role in self.roles:
                    if role.role_id == role_id:
                        return True
                return False
        raise AttributeError( name )
                
    def __setattr__( self, name, value ):
        for role_id, role_name in roles:
            if role_name == name:
                current_value = getattr( self, name )
                if value==True and current_value==False:
                    group_role = AuthenticationGroupRole( role_id = role_id )
                    self.roles.append( group_role )
                elif value==False and current_value==True:
                    for group_role in self.roles:
                        if group_role.role_id == role_id:
                            self.roles.remove( group_role )
                            break
                break
        return super( AuthenticationGroup, self ).__setattr__( name, value )
        
    def __str__( self ):
        return self.name or ''
    


authentication_group_member_table = schema.Table('authentication_group_member', metadata,
                            schema.Column('authentication_group_id', types.Integer(),
                                          schema.ForeignKey(AuthenticationGroup.id, name='authentication_group_members_fk'),
                                          nullable=False, primary_key=True),
                            schema.Column('authentication_mechanism_id', types.Integer(),
                                          schema.ForeignKey(AuthenticationMechanism.id, name='authentication_group_members_inverse_fk'),
                                          nullable=False, primary_key=True)
                            )

AuthenticationGroup.members = orm.relationship(AuthenticationMechanism, backref='groups', secondary=authentication_group_member_table,
                                               foreign_keys=[
                                                   authentication_group_member_table.c.authentication_group_id,
                                                   authentication_group_member_table.c.authentication_mechanism_id])

class AuthenticationGroupRole( Entity ):
    """Table with the different roles associated with an
    :class:`AuthenticationGroup`
    """
    
    __tablename__ = 'authentication_group_role'
    
    role_id = Column( camelot.types.PrimaryKey(), 
                      nullable = False,
                      primary_key = True,
                      autoincrement = False )
    group_id = Column( camelot.types.PrimaryKey(), 
                       ForeignKey( 'authentication_group.id',
                                   onupdate = 'cascade',
                                   ondelete = 'cascade' ),
                       nullable = False,
                       primary_key = True,
                       autoincrement = False )

AuthenticationGroup.roles = orm.relationship( AuthenticationGroupRole,
                                              cascade = 'all, delete, delete-orphan')
