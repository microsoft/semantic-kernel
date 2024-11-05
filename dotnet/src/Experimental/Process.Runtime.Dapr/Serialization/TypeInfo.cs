// Copyright (c) Microsoft. All rights reserved.
using System;
using System.Text.Json;

namespace Microsoft.SemanticKernel.Process.Serialization;

/// <summary>
/// %%% COMMENT
/// </summary>
internal static class TypeInfo
{
    /// <summary>
    /// %%% COMMENT
    /// </summary>
    /// <param name="value"></param>
    /// <returns></returns>
    public static string? GetAssemblyQualifiedType(object? value)
    {
        if (value == null)
        {
            return null;
        }

        return value.GetType().AssemblyQualifiedName;
    }

    /// <summary>
    /// %%% COMMENT
    /// </summary>
    /// <param name="assemblyQuailfiedTypeName"></param>
    /// <param name="value"></param>
    /// <returns></returns>
    /// <exception cref="KernelException"></exception>
    public static object? ConvertValue(string? assemblyQuailfiedTypeName, object? value)
    {
        if (value == null)
        {
            return null;
        }

        if (value.GetType() != typeof(JsonElement))
        {
            return value;
        }

        if (assemblyQuailfiedTypeName == null)
        {
            throw new KernelException("Data persisted without type information.");
        }

        Type? valueType = Type.GetType(assemblyQuailfiedTypeName);
        return ((JsonElement)value).Deserialize(valueType!);
    }
}
