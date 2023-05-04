// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;

namespace Microsoft.SemanticKernel.SkillDefinition;

internal class NullReadOnlySkillCollection : IReadOnlySkillCollection
{
    public static NullReadOnlySkillCollection Instance = new();

    public ISKFunction GetFunction(string functionName)
        => ThrowFunctionNotAvailable(functionName);

    public ISKFunction GetFunction(string skillName, string functionName)
        => ThrowFunctionNotAvailable(skillName, functionName);

    public bool TryGetFunction(string functionName, [NotNullWhen(true)] out ISKFunction? functionInstance)
    {
        functionInstance = null;
        return false;
    }

    public bool TryGetFunction(string skillName, string functionName, [NotNullWhen(true)] out ISKFunction? functionInstance)
    {
        functionInstance = null;
        return false;
    }

    public ISKFunction GetSemanticFunction(string functionName)
        => ThrowFunctionNotAvailable(functionName);

    public ISKFunction GetSemanticFunction(string skillName, string functionName)
        => ThrowFunctionNotAvailable(skillName, functionName);

    public bool TryGetSemanticFunction(string functionName, [NotNullWhen(true)] out ISKFunction? functionInstance)
    {
        functionInstance = null;
        return false;
    }

    public bool TryGetSemanticFunction(string skillName, string functionName, [NotNullWhen(true)] out ISKFunction? functionInstance)
    {
        functionInstance = null;
        return false;
    }

    public ISKFunction GetNativeFunction(string skillName, string functionName)
        => ThrowFunctionNotAvailable(skillName, functionName);

    public ISKFunction GetNativeFunction(string functionName)
        => ThrowFunctionNotAvailable(functionName);


    public bool TryGetNativeFunction(string functionName, [NotNullWhen(true)] out ISKFunction? functionInstance)
    {
        functionInstance = null;
        return false;
    }

    public bool TryGetNativeFunction(string skillName, string functionName, [NotNullWhen(true)] out ISKFunction? functionInstance)
    {
        functionInstance = null;
        return false;
    }

    public FunctionsView GetFunctionsView(bool includeSemantic = true, bool includeNative = true)
        => new FunctionsView();

    private NullReadOnlySkillCollection()
    {
    }

    [DoesNotReturn]
    private static ISKFunction ThrowFunctionNotAvailable(string skillName, string functionName)
        => throw new KernelException(
                KernelException.ErrorCodes.FunctionNotAvailable,
                $"Function not available: {skillName}.{functionName}");

    [DoesNotReturn]
    private static ISKFunction ThrowFunctionNotAvailable(string functionName)
        => throw new KernelException(
                KernelException.ErrorCodes.FunctionNotAvailable,
                $"Function not available: {functionName}");
}
