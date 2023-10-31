// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Diagnostics.CodeAnalysis;
using Microsoft.SemanticKernel.Diagnostics;

#pragma warning disable IDE0130
// ReSharper disable once CheckNamespace - Using the main namespace
namespace Microsoft.SemanticKernel;
#pragma warning restore IDE0130

[DebuggerDisplay("Count = 0")]
internal sealed class NullReadOnlyFunctionCollection : IReadOnlyFunctionCollection
{
    public static readonly NullReadOnlyFunctionCollection Instance = new();

    /// <inheritdoc/>
    public ISKFunction GetFunction(string functionName)
    {
        throw new SKException($"Function not available: {functionName}");
    }

    /// <inheritdoc/>
    public ISKFunction GetFunction(string pluginName, string functionName)
    {
        throw new SKException($"Function not available: {pluginName}.{functionName}");
    }

    /// <inheritdoc/>
    public bool TryGetFunction(string functionName, [NotNullWhen(true)] out ISKFunction? availableFunction)
    {
        availableFunction = null;
        return false;
    }

    /// <inheritdoc/>
    public bool TryGetFunction(string pluginName, string functionName, [NotNullWhen(true)] out ISKFunction? availableFunction)
    {
        availableFunction = null;
        return false;
    }

    /// <inheritdoc/>
    public IReadOnlyList<FunctionView> GetFunctionViews()
    {
        return Array.Empty<FunctionView>();
    }

    private NullReadOnlyFunctionCollection()
    {
    }
}
