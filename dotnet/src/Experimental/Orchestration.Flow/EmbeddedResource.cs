// Copyright (c) Microsoft. All rights reserved.

using System.IO;
using System.Reflection;
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
using Microsoft.SemanticKernel.Diagnostics;
>>>>>>> 9cfcc609b1cbe6e1d6975df1d665fa0b064c5624
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> origin/main
=======
>>>>>>> Stashed changes

namespace Microsoft.SemanticKernel.Experimental.Orchestration;

internal static class EmbeddedResource
{
    private static readonly string? s_namespace = typeof(EmbeddedResource).Namespace;

    internal static string? Read(string name, bool throwIfNotFound = true)
    {
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
        var assembly = typeof(EmbeddedResource).GetTypeInfo().Assembly ??
            throw new KernelException($"[{s_namespace}] {name} assembly not found");
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
        var assembly = typeof(EmbeddedResource).GetTypeInfo().Assembly ??
            throw new KernelException($"[{s_namespace}] {name} assembly not found");
=======
<<<<<<< Updated upstream
=======
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
        var assembly = typeof(EmbeddedResource).GetTypeInfo().Assembly ??
            throw new KernelException($"[{s_namespace}] {name} assembly not found");
=======
        var assembly = typeof(EmbeddedResource).GetTypeInfo().Assembly;
        if (assembly is null) { throw new SKException($"[{s_namespace}] {name} assembly not found"); }
>>>>>>> 9cfcc609b1cbe6e1d6975df1d665fa0b064c5624
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
=======
>>>>>>> Stashed changes
>>>>>>> origin/main

        using Stream? resource = assembly.GetManifestResourceStream($"{s_namespace}." + name);
        if (resource is null)
        {
            if (!throwIfNotFound)
            {
                return null;
            }

<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
            throw new KernelException($"[{s_namespace}] {name} resource not found");
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
            throw new KernelException($"[{s_namespace}] {name} resource not found");
=======
            throw new SKException($"[{s_namespace}] {name} resource not found");
>>>>>>> 9cfcc609b1cbe6e1d6975df1d665fa0b064c5624
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
            throw new KernelException($"[{s_namespace}] {name} resource not found");
=======
            throw new SKException($"[{s_namespace}] {name} resource not found");
>>>>>>> 9cfcc609b1cbe6e1d6975df1d665fa0b064c5624
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
        }

        using var reader = new StreamReader(resource);
        return reader.ReadToEnd();
    }
}
