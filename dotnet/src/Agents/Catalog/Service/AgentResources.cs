// Copyright (c) Microsoft. All rights reserved.

using System;
using System.IO;
using System.Reflection;

namespace Microsoft.SemanticKernel.Agents.Service;

/// <summary>
/// Convenience methods for accessing assembly resources.
/// </summary>
public static class AgentResources
{
    /// <summary>
    /// Loads the specified resource from an assembly.
    /// </summary>
    /// <param name="resourceName">he case-sensitive identifier of the requested resource.</param>
    /// <param name="assembly">The target assembly where the resource resides.  Default to the calling assembly.</param>
    /// <returns></returns>
    public static Stream OpenStream(string resourceName, Assembly? assembly = null)
    {
        assembly ??=
            Assembly.GetCallingAssembly() ??
            throw new InvalidOperationException("Unable to resolve resource assembly.");

        return
            assembly.GetManifestResourceStream($"{assembly.GetName().Name}.{resourceName}") ??
            throw new InvalidOperationException($"Resource not found: {resourceName}");
    }
}
