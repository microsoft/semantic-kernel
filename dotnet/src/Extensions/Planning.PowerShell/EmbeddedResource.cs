// Copyright (c) Microsoft. All rights reserved.

using System.IO;
using System.Reflection;
using Microsoft.SemanticKernel.Diagnostics;

namespace Microsoft.SemanticKernel.Planning.PowerShell;

internal static class EmbeddedResource
{
    private static readonly string? s_namespace = typeof(EmbeddedResource).Namespace;

    internal static string Read(string name)
    {
        var assembly = typeof(EmbeddedResource).GetTypeInfo().Assembly;
        // The null check for 'assembly' is redundant and can be removed

        using Stream? resource = assembly.GetManifestResourceStream($"{s_namespace}." + name);
        if (resource == null) { throw new SKException($"[{s_namespace}] {name} resource not found"); }

        using var reader = new StreamReader(resource);
        return reader.ReadToEnd();
    }
}
