// Copyright (c) Microsoft. All rights reserved.

using System;
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
    /// Initializes a new instance of the <see cref="KernelFunctionArguments"/> class with the specified AI request settings.
    /// </summary>
    /// <param name="executionSettings">The prompt execution settings.</param>
    public KernelFunctionArguments(PromptExecutionSettings? executionSettings = null) : base(StringComparer.OrdinalIgnoreCase)
    {
        this.ExecutionSettings = executionSettings;
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="KernelFunctionArguments"/> class that contains elements copied from the specified <see cref="IDictionary{TKey, TValue}"/>
    /// </summary>
    /// <param name="source">The <see cref="IDictionary{TKey, TValue}"/> whose elements are copied the new <see cref="KernelFunctionArguments"/>.</param>
    public KernelFunctionArguments(IDictionary<string, string> source) : this()
    {
        foreach (var x in source) { this[x.Key] = x.Value; }
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="KernelFunctionArguments"/> class that contains AI request settings and elements copied from the specified <see cref="KernelFunctionArguments"/>
    /// </summary>
    /// <param name="other">The <see cref="KernelFunctionArguments"/> whose AI request setting and elements are copied to the new <see cref="KernelFunctionArguments"/>.</param>
    public KernelFunctionArguments(KernelFunctionArguments other) : this(other as IDictionary<string, string>)
    {
        this.ExecutionSettings = other.ExecutionSettings;
    }

    /// <summary>
    /// Gets or sets the prompt execution settings
    /// </summary>
    public PromptExecutionSettings? ExecutionSettings { get; set; }
}
