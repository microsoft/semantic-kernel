// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;

#pragma warning disable IDE0130
// ReSharper disable once CheckNamespace - Using the main namespace
namespace Microsoft.SemanticKernel;
#pragma warning restore IDE0130

/// <summary>
/// Function collection interface.
/// </summary>
[SuppressMessage("Naming", "CA1711:Identifiers should not have incorrect suffix")]
public interface IFunctionCollection : IReadOnlyFunctionCollection
{
    /// <summary>
    /// Add a function to the collection
    /// </summary>
    /// <param name="functionInstance">Function delegate</param>
    /// <returns>Self instance</returns>
    IFunctionCollection AddFunction(ISKFunction functionInstance);
}
