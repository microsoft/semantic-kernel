// Copyright (c) Microsoft. All rights reserved.
using System;
using System.Text.Json;

namespace Microsoft.SemanticKernel.Process.Serialization;

/// <summary>
/// Extension methods for capturing and restoring an object's type.
/// </summary>
internal static class TypeInfo
{
    /// <summary>
    /// Retrieves the assembly qualified type-name of the provided value (null when null).
    /// </summary>
    public static string? GetAssemblyQualifiedType(object? value)
    {
        if (value == null)
        {
            return null;
        }

        return value.GetType().AssemblyQualifiedName;
    }

    /// <summary>
    /// Restore the object's type from the provided assembly qualified type-name, but
    /// only if it is a <see cref="JsonElement"/>. Otherwise, return the original value.
    /// </summary>
    public static object? ConvertValue(string? assemblyQualifiedTypeName, object? value)
    {
        if (value == null || value.GetType() != typeof(JsonElement))
        {
            return value;
        }

        if (assemblyQualifiedTypeName == null)
        {
            throw new KernelException("Data persisted without type information.");
        }

        Type? valueType = Type.GetType(assemblyQualifiedTypeName);
        return ((JsonElement)value).Deserialize(valueType!);
    }
}
