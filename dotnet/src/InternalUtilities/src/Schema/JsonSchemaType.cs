// Copyright (c) Microsoft. All rights reserved.

#if !NET9_0_OR_GREATER && !SYSTEM_TEXT_JSON_V9
using System;

namespace JsonSchemaMapper;

[Flags]
internal enum JsonSchemaType
{
    Any = 0, // No type declared on the schema
    Null = 1,
    Boolean = 2,
    Integer = 4,
    Number = 8,
    String = 16,
    Array = 32,
    Object = 64,
}
#endif
