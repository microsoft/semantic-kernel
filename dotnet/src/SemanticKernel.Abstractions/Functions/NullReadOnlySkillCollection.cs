// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Diagnostics;
using System.Diagnostics.CodeAnalysis;
using Microsoft.SemanticKernel.Diagnostics;

namespace Microsoft.SemanticKernel.Functions;

[DebuggerDisplay("Count = 0")]
internal sealed class NullReadOnlySkillCollection : IReadOnlySkillCollection
{
    public static readonly NullReadOnlySkillCollection Instance = new();

    /// <inheritdoc/>
    public ISKFunction GetFunction(string functionName)
    {
        return ThrowFunctionNotAvailable(functionName);
    }

    /// <inheritdoc/>
    public ISKFunction GetFunction(string pluginName, string functionName)
    {
        return ThrowFunctionNotAvailable(pluginName, functionName);
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
        return new List<FunctionView>();
    }

    private NullReadOnlySkillCollection()
    {
    }

    [DoesNotReturn]
    private static ISKFunction ThrowFunctionNotAvailable(string pluginName, string functionName)
    {
        throw new SKException($"Function not available: {pluginName}.{functionName}");
    }

    [DoesNotReturn]
    private static ISKFunction ThrowFunctionNotAvailable(string functionName)
    {
        throw new SKException($"Function not available: {functionName}");
    }
}
