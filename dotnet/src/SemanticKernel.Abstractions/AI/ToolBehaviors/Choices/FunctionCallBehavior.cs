// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel.AI.ToolBehaviors;

public abstract class FunctionCallChoice
{
    protected const string FunctionNameSeparator = ".";

    public abstract FunctionCallChoiceConfiguration Configure(FunctionCallChoiceContext context);
}
