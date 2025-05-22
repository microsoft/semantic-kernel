// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.AI;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Represents a kernel function that provides the plugin name as part of the original function name.
/// </summary>
public abstract class FullyQualifiedAIFunction : AIFunction
{
    /// <summary>
    /// Initializes a new instance of the <see cref="FullyQualifiedAIFunction"/> class.
    /// </summary>
    /// <param name="metadata">The metadata describing the function.</param>
    internal FullyQualifiedAIFunction(KernelFunctionMetadata metadata)
    {
        this.Metadata = metadata;
    }

    /// <summary>
    /// Gets the metadata describing the function.
    /// </summary>
    /// <returns>An instance of <see cref="KernelFunctionMetadata"/> describing the function</returns>
    public KernelFunctionMetadata Metadata { get; init; }

    /// <summary>
    /// Gets the name of the function.
    /// </summary>
    /// <remarks>
    /// The fully qualified name (including the plugin name) is used anywhere the function needs to be identified, such as in plans describing what functions
    /// should be invoked when, or as part of lookups in a plugin's function collection. Function names are generally
    /// handled in an ordinal case-insensitive manner.
    /// </remarks>
    public override string Name
        => !string.IsNullOrWhiteSpace(this.Metadata.PluginName)
            ? $"{this.Metadata.PluginName}_{this.Metadata.Name}"
            : this.Metadata.Name;
}
