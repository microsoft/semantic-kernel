// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel;

/// <summary>
/// Base class for process definitions.
/// </summary>
public abstract class ProcessDefinition
{
    /// <summary>
    /// Build the process.
    /// </summary>
    /// <returns></returns>
    public abstract KernelProcess Build();
}
