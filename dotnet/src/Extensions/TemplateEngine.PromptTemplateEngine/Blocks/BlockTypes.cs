// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel.TemplateEngine.Prompt.Blocks;

internal enum BlockTypes
{
    Undefined = 0,
    Text = 1,
    Code = 2,
    Variable = 3,
    Value = 4,
    FunctionId = 5,
    NamedArg = 6,
}
