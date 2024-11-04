// Copyright (c) Microsoft. All rights reserved.
using System;
using System.Reflection;

namespace Microsoft.SemanticKernel.Process.Serialization;

/// <summary>
///  %%% COMMENT
/// </summary>
/// <param name="TypeName"></param>
/// <param name="AssemblyName"></param>
/// <param name="AssemblyVersion"></param>
internal sealed record TypeInfo(string TypeName, string AssemblyName, string? AssemblyVersion)
{
    /// <summary>
    /// %%% COMMENT
    /// </summary>
    /// <param name="obj"></param>
    /// <returns></returns>
    public static TypeInfo? FromObject(object? obj)
    {
        if (obj == null)
        {
            return null;
        }

        Type type = obj.GetType();
        AssemblyName assemblyName = type.Assembly.GetName();
        return new(type.FullName!, assemblyName.Name!, assemblyName.Version?.ToString());
    }

    /// <summary>
    /// %%% COMMENT
    /// </summary>
    /// <param name="typeInfo"></param>
    /// <returns></returns>
    /// <exception cref="TypeLoadException"></exception>
    public static Type Resolve(TypeInfo typeInfo)
    {
        Type? dataType = Type.GetType(typeInfo.TypeName);

        if (dataType == null)
        {
            Assembly assembly = Assembly.Load(typeInfo.AssemblyName);
            dataType = assembly.GetType(typeInfo.TypeName);
        }

        if (dataType == null)
        {
            throw new TypeLoadException($"Could not resolve type {typeInfo.TypeName} from assembly {typeInfo.AssemblyName}");
        }

        return dataType;
    }
}
