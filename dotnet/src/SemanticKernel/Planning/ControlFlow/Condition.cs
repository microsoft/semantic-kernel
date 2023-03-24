// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.Orchestration;

namespace Microsoft.SemanticKernel.Planning.ControlFlow;

public abstract class Condition
{
    public abstract string Type { get; }

    public abstract bool Evaluate(SKContext context);
}
