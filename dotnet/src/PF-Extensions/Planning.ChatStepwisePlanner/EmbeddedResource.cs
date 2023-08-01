// Copyright (c) Microsoft. All rights reserved.

using System.IO;
using System.Reflection;

#pragma warning disable IDE0130
// ReSharper disable once CheckNamespace - Using NS of Plan
namespace Microsoft.SemanticKernel.Planning.ChatStepwise;

public static class EmbeddedResource
{
    internal static string Read(string resourceName)
    {
        Assembly assembly = Assembly.GetExecutingAssembly();

        using Stream stream = assembly.GetManifestResourceStream(resourceName);
        using StreamReader reader = new StreamReader(stream);
        return reader.ReadToEnd();
    }
}
