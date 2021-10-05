"""
test integrating Camelot entities with plain SQLAlchemy defined classes
"""

from . import TestMetaData

from camelot.core.orm import ( Field, ManyToMany, ManyToOne, OneToMany, using_options,
                               has_field, has_many, belongs_to, options,
                               has_and_belongs_to_many )

from sqlalchemy import orm, schema
from sqlalchemy.types import String, Unicode, Integer

class TestSQLAlchemyToCamelot( TestMetaData ):

    def test_simple( self ):
        
        class A( self.Entity ):
            name = Field(String(60))

        self.create_all()

        b_table = schema.Table('b', self.metadata,
            schema.Column('id', Integer, primary_key=True),
            schema.Column('name', String(60)),
            schema.Column('a_id', Integer, schema.ForeignKey(A.id))
        )
        b_table.create()

        class B(object):
            pass

        orm.mapper(B, b_table, properties={
            'a': orm.relation(A)
        })

        with self.session.begin():
            b1 = B()
            b1.name = 'b1'
            b1.a = A(name='a1')

            self.session.add( b1 )
            
        self.session.expire_all()
        b = self.session.query(B).one()
        assert b.a.name == 'a1'
        
    def test_existing_table( self ):
        
        a_table = schema.Table('a', self.metadata,
            schema.Column('id', Integer, primary_key=True),
            schema.Column('name', String(60)),
        )
        a_table.create()
        
        class A( self.Entity ):
            __table__ = a_table
            
        with self.session.begin():
            a = A(name='a1')
        
    def test_single_table_inheritance( self ):
        
        class A( self.Entity ):
            
            __tablename__ = 'a'
            
            name = schema.Column( String(50) )
            discriminator = schema.Column( 'type', String(50) )
            __mapper_args__ = {'polymorphic_on': discriminator,
                               'polymorphic_identity': 'A'}  
            
        class B( A ):    
            
            __tablename__ = None
            
            language = schema.Column( String(50) )  
            __mapper_args__ = {'polymorphic_identity': 'B'}
            
        self.create_all()
        
        self.assertEqual( A.__table__, B.__table__ )
        b = B( name = 'b', language = 'English' )
        self.session.flush()
        a = A.get( b.id )
        self.assertEqual( b, a )
        
class TestCamelotToSQLAlchemy( TestMetaData ):

    def test_m2o( self ):
        
        a_table = schema.Table('a', self.metadata,
            schema.Column('id', Integer, primary_key=True),
            schema.Column('name', String(60)),
        )
        a_table.create()

        class A(object):
            pass

        orm.mapper(A, a_table)

        class B( self.Entity ):
            name = Field(String(60))
            a = ManyToOne(A)

        self.create_all()

        with self.session.begin():
            a1 = A()
            a1.name = 'a1'
            b1 = B(name='b1', a=a1)
            self.session.add(b1)
            
        self.session.expire_all()
        b = B.query.one()
        assert b.a.name == 'a1'

    def test_m2o_non_pk_target( self ):
        
        a_table = schema.Table('a', self.metadata,
            schema.Column('id', Integer, primary_key=True),
            schema.Column('name', String(60), unique=True)
        )
        a_table.create()

        class A(object):
            pass

        orm.mapper(A, a_table)

        class B( self.Entity ):
            name = Field(String(60))
            a = ManyToOne(A, target_column=['name'])

        self.create_all()
        
        with self.session.begin():
            a1 = A()
            a1.name = 'a1'
            b1 = B(name='b1', a=a1)

        self.session.expire_all()

        b = B.query.one()

        assert b.a.name == 'a1'
