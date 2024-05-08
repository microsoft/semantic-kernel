// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;

namespace Microsoft.SemanticKernel;

public class FunctionChoiceBehaviorConfiguration
{
    public IEnumerable<KernelFunctionMetadata>? AvailableFunctions { get; init; }

    public IEnumerable<KernelFunctionMetadata>? RequiredFunctions { get; init; }

    public int? MaximumAutoInvokeAttempts { get; init; }

    public int? MaximumUseAttempts { get; init; }
}
