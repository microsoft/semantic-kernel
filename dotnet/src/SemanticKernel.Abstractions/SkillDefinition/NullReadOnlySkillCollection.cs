// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics;
using System.Diagnostics.CodeAnalysis;
using Microsoft.SemanticKernel.Diagnostics;

namespace Microsoft.SemanticKernel.SkillDefinition;

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
    public ISKFunction GetFunction(string skillName, string functionName)
    {
        return ThrowFunctionNotAvailable(skillName, functionName);
    }

    /// <inheritdoc/>
    public bool TryGetFunction(string functionName, [NotNullWhen(true)] out ISKFunction? availableFunction)
    {
        availableFunction = null;
        return false;
    }

    /// <inheritdoc/>
    public bool TryGetFunction(string skillName, string functionName, [NotNullWhen(true)] out ISKFunction? availableFunction)
    {
        availableFunction = null;
        return false;
    }

    /// <inheritdoc/>
    public FunctionsView GetFunctionsView(bool includeSemantic = true, bool includeNative = true)
    {
        return new();
    }

    private NullReadOnlySkillCollection()
    {
    }

    [DoesNotReturn]
    private static ISKFunction ThrowFunctionNotAvailable(string skillName, string functionName)
    {
        throw new SKException($"Function not available: {skillName}.{functionName}");
    }

    [DoesNotReturn]
    private static ISKFunction ThrowFunctionNotAvailable(string functionName)
    {
        throw new SKException($"Function not available: {functionName}");
    }
}
