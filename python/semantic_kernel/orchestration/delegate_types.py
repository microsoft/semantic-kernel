# Copyright (c) Microsoft. All rights reserved.

from enum import Enum


class DelegateTypes(Enum):
    Unknown = 0
    Void = 1
    OutString = 2
    OutTaskString = 3
    InSKContext = 4
    InSKContextOutString = 5
    InSKContextOutTaskString = 6
    ContextSwitchInSKContextOutTaskSKContext = 7
    InString = 8
    InStringOutString = 9
    InStringOutTaskString = 10
    InStringAndContext = 11
    InStringAndContextOutString = 12
    InStringAndContextOutTaskString = 13
    ContextSwitchInStringAndContextOutTaskContext = 14
    InStringOutTask = 15
    InContextOutTask = 16
    InStringAndContextOutTask = 17
    OutTask = 18
