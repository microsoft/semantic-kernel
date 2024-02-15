# Copyright (c) Microsoft. All rights reserved.

from enum import Enum


class DelegateTypes(Enum):
    Unknown = 0
    Void = 1
    OutString = 2
    OutTaskString = 3
    InKernelContext = 4
    InKernelContextOutString = 5
    InKernelContextOutTaskString = 6
    ContextSwitchInKernelContextOutTaskKernelContext = 7
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
    OutAsyncGenerator = 19
    InStringOutAsyncGenerator = 20
    InContextOutAsyncGenerator = 21
    InStringAndContextOutAsyncGenerator = 22
