// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Context for the <see cref="FunctionNamePolicy.ParseFunctionFqn"/> method.
/// </summary>
/// <param name="functionFqn">The function fully qualified name.</param>
[Experimental("SKEXP0001")]
public class ParseFunctionFqnContext(string functionFqn)
{
    /// <summary>
    /// Gets or sets the function name.
    /// </summary>
    public string FunctionFqn { get; set; } = functionFqn;

    /// <summary>
    /// Gets or sets the kernel.
    /// </summary>
    public Kernel? Kernel { get; set; }
}
