// Copyright (c) Microsoft. All rights reserved.

using System.IO;
using System.Reflection;

namespace Microsoft.SemanticKernel.Planning.Stepwise;

internal static class EmbeddedResource
{
    private static readonly string? s_namespace = typeof(EmbeddedResource).Namespace;

    internal static string Read(string name)
    {
        var assembly = typeof(EmbeddedResource).GetTypeInfo().Assembly;
        if (assembly == null) { throw new PlanningException(PlanningException.ErrorCodes.InvalidConfiguration, $"[{s_namespace}] {name} assembly not found"); }

        using Stream? resource = assembly.GetManifestResourceStream($"{s_namespace}." + name);
        if (resource == null) { throw new PlanningException(PlanningException.ErrorCodes.InvalidConfiguration, $"[{s_namespace}] {name} resource not found"); }

        using var reader = new StreamReader(resource);
        return reader.ReadToEnd();
    }
}
