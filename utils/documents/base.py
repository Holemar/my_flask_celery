# -*- coding: utf-8 -*-

"""
Document abstract class
"""
import logging
from abc import ABC, abstractmethod
from utils.import_util import parse_csv_content

logger = logging.getLogger(__name__)


class IDocument(object):

    @classmethod
    @abstractmethod
    def import_csv(cls, data):
      import_options = {}

      # TBD
      if hasattr(cls, 'meta'):
        import_options = cls.meta.get('import_options') or {}
      elif hasattr(cls, '_meta'):
        import_options = cls._meta.get('import_options') or {}

      value = {}
      form = import_options['form']
      fields = import_options['fields']

      for field in form:
          key = field
          value[key] = data.get(key)

      content = data.get('content', '')
      result = parse_csv_content(content, fields)
      result = list(map(lambda x: {**value, **x}, result))
      items = cls.batch_insert(result)
      return items

    @classmethod
    @abstractmethod
    def is_valid_id(cls, _id):
      raise NotImplementedError

    @classmethod
    @abstractmethod
    def batch_insert(cls, items):
      raise NotImplementedError

    @classmethod
    @abstractmethod
    def build_object(cls, data):
      raise NotImplementedError

    @classmethod
    @abstractmethod
    def find_one(cls, condition):
      raise NotImplementedError

    @classmethod
    @abstractmethod
    def find_one_by_id(cls, id):
      raise NotImplementedError

    @classmethod
    @abstractmethod
    def find_by_ids(cls, ids):
      raise NotImplementedError

    @classmethod
    @abstractmethod
    def get_fields(cls):
      raise NotImplementedError

    @classmethod
    @abstractmethod
    def get_schema_mapping(cls):
      raise NotImplementedError

    @classmethod
    @abstractmethod
    def get_schema(cls):
      schema_mapping = cls.get_schema_mapping()
      properties = []
      for name, field in cls.get_fields().items():
        if field.__class__ in schema_mapping:
          properties.append({
            'name': name,
            'type': schema_mapping[field.__class__]
          })
      return {
        'properties': properties
      }
