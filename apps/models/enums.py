# -*- coding:utf-8 -*-
from enum import IntEnum, StrEnum, Enum


class UserEnum(IntEnum):
    USER = 1
    MANAGER = 2


class RelevantType(StrEnum):
    """
    数据的相关性
    """
    relevant = 'relevant'
    irrelevant = 'irrelevant'
    neutral = 'neutral'
    unlabeled = 'unlabeled'


class Language(StrEnum):
    ENGLISH = 'english'
    CHINESE = 'chinese'
    JAPANESE = 'japanese'
    KOREAN = 'korean'
    VIETNAMESE = 'vietnamese'

