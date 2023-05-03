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

    public FunctionsView GetFunctionsView(bool includeSemantic = true, bool includeNative = true)
        => new FunctionsView();

    public ISKFunction GetNativeFunction(string skillName, string functionName)
        => ThrowFunctionNotAvailable(skillName, functionName);

    public ISKFunction GetNativeFunction(string functionName)
        => ThrowFunctionNotAvailable(functionName);

    public ISKFunction GetSemanticFunction(string functionName)
        => ThrowFunctionNotAvailable(functionName);

    public ISKFunction GetSemanticFunction(string skillName, string functionName)
        => ThrowFunctionNotAvailable(skillName, functionName);

    public bool HasFunction(string skillName, string functionName) => false;

    public bool HasFunction(string functionName) => false;

    public bool HasNativeFunction(string skillName, string functionName) => false;

    public bool HasNativeFunction(string functionName) => false;

    public bool HasSemanticFunction(string skillName, string functionName) => false;

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
