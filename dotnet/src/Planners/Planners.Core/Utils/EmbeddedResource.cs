// Copyright (c) Microsoft. All rights reserved.

using System.IO;
using System.Reflection;
using Microsoft.SemanticKernel.Diagnostics;

#pragma warning disable IDE0130
namespace Microsoft.SemanticKernel.Planners;
#pragma warning restore IDE0130

internal static class EmbeddedResource
{
    private static readonly string? s_namespace = typeof(EmbeddedResource).Namespace;

    internal static string Read(string name)
    {
        var assembly = typeof(EmbeddedResource).GetTypeInfo().Assembly;
        if (assembly == null) { throw new SKException($"[{s_namespace}] {name} assembly not found"); }

        using Stream? resource = assembly.GetManifestResourceStream($"{s_namespace}." + name);
        if (resource == null) { throw new SKException($"[{s_namespace}] {name} resource not found"); }

        using var reader = new StreamReader(resource);
        return reader.ReadToEnd();
    }
}
