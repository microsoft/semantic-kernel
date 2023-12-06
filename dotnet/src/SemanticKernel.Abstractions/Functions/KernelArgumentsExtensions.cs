// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel;

/// <summary>Provides extension methods for working with <see cref="KernelArguments"/> string values.</summary>
public static class KernelArgumentsExtensions
{
    /// <inheritdoc cref="KernelArguments.TryGetValue"/>
    public static bool TryGetStringValue(this KernelArguments arguments, string name, out string? value)
    {
        bool result = arguments.TryGetValue(name, out object? objectValue);
        value = objectValue as string;

        return result;
    }

    /// <summary>
    /// Gets the value associated with the <see cref="KernelArguments.InputParameterName"/> argument name as a string.
    /// </summary>
    public static string? GetStringInput(this KernelArguments arguments)
    {
        arguments.TryGetStringValue(KernelArguments.InputParameterName, out string? input);
        return input;
    }
}