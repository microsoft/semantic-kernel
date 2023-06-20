// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.templateengine.blocks;

public enum BlockTypes {
    Undefined(0),
    Text(1),
    Code(2),
    Variable(3),
    Value(4),
    FunctionId(5);

    BlockTypes(int i) {}
}
