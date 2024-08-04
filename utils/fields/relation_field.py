# -*- coding: utf-8 -*-
"""
外键字段
"""
import six
from mongoengine.fields import BaseField, RECURSIVE_REFERENCE_CONSTANT
from mongoengine.base import get_document
from mongoengine.queryset.visitor import Q


class LazyRelation(object):
    __slots__ = ('_cached_doc', 'passthrough', 'document_type', 'relation_type', 'query', '_target_field','instance')

    @property
    def target_field(self):
        if self._target_field:
            return self._target_field
        else:
            return self.instance._class_name.lower()
    
    @target_field.setter
    def target_field(self, value):
        self._target_field = value

    def fetch(self, **filter_query):
        if not self._cached_doc:
            if self.relation_type == 'has_one':
                self._cached_doc = self.objects(**filter_query).first()
            else:
                self._cached_doc = list(self.objects(**filter_query))
        return self._cached_doc

    def objects(self, **filter_query):
        # if not self._cached_doc or force:
        q_query = Q(**filter_query)
        if self.target_field:
            q_query &= Q(**{self.target_field: self.instance.id})
        else:
            q_query &= Q(**self.query)
        if self.relation_type == 'has_one':
            return self.document_type.objects(q_query).order_by('-id')
        elif self.relation_type == 'has_many':
            return self.document_type.objects(q_query)
        else:
            raise SystemError('Wrong Relation Type')

    def __init__(self, document_type, relation_type,target_field, instance, passthrough=False, cached_doc=None):
        self.document_type = document_type
        self.relation_type = relation_type
        self.passthrough = passthrough
        self._cached_doc = cached_doc
        self._target_field = target_field
        self.instance = instance

    def __getitem__(self, name):
        if not self.passthrough:
            raise KeyError()
        document = self.fetch()
        return document[name]

    def __getattr__(self, name):
        if not object.__getattribute__(self, 'passthrough'):
            raise AttributeError()
        document = self.fetch()
        try:
            return document[name]
        except KeyError:
            raise AttributeError()

    def __repr__(self):
        return "<LazyRelation(%s)>" % (self.document_type)


class RelationField(BaseField):
    """
    RelationField:
        * relation_type: has_one, has_many
    """
    def __init__(self, relation_type, document_type, target_field=None, passthrough=False, **kwargs):
        self.relation_type = relation_type
        self.passthrough = passthrough
        self.document_type_obj = document_type
        self.target_field = target_field
        super(RelationField, self).__init__(**kwargs)

    @property
    def document_type(self):
        if isinstance(self.document_type_obj, six.string_types):
            if self.document_type_obj == RECURSIVE_REFERENCE_CONSTANT:
                self.document_type_obj = self.owner_document
            else:
                self.document_type_obj = get_document(self.document_type_obj)
        return self.document_type_obj

    def __get__(self, instance, owner):
        """Descriptor to allow lazy dereferencing."""
        if instance is None:
            # Document class being used rather than a document object
            return self

        value = LazyRelation(self.document_type, relation_type=self.relation_type, target_field=self.target_field, instance=instance, passthrough=self.passthrough)
        instance._data[self.name] = value
        return super(RelationField, self).__get__(instance, owner)

    def to_python(self, value):
        return None

    def to_mongo(self, value):
        return None

    def validate(self, value):
        return True

    def _validate(self, value, **kwargs):
        return True

    def lookup_member(self, member_name):
        return self.document_type._fields.get(member_name)
