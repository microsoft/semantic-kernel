// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using Microsoft.SemanticKernel.AI;

#pragma warning disable IDE0130
namespace Microsoft.SemanticKernel;
#pragma warning restore IDE0130

/// <summary>
/// Represents arguments of <see cref="KernelFunction.InvokeAsync"/> and "Kernel.InvokeAsync" methods.
/// </summary>
public sealed class KernelFunctionArguments : Dictionary<string, string>
{
    /// <summary>
    /// Initializes a new instance of the <see cref="KernelFunctionArguments"/> class.
    /// </summary>
    /// <param name="requestSettings">The AI request settings.</param>
    public KernelFunctionArguments(AIRequestSettings? requestSettings = null)
    {
        this.RequestSettings = requestSettings;
    }

    /// <summary>
    /// Gets or sets the AI request settings.
    /// </summary>
    public AIRequestSettings? RequestSettings { get; set; }
}
