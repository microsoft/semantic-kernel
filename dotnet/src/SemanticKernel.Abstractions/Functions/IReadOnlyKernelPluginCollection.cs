// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;

namespace Microsoft.SemanticKernel;

/// <summary>Provides a read-only collection of <see cref="IKernelPlugin"/>s.</summary>
public interface IReadOnlyKernelPluginCollection : IReadOnlyCollection<IKernelPlugin>
{
    /// <summary>Gets a plugin from the collection by name.</summary>
    /// <param name="name">The name of the plugin.</param>
    /// <returns>The plugin.</returns>
    IKernelPlugin this[string name] { get; }

    /// <summary>Gets a plugin from the collection by name.</summary>
    /// <param name="name">The name of the plugin.</param>
    /// <param name="plugin">The plugin if found in the collection.</param>
    /// <returns>true if the collection contains the plugin; otherwise, false.</returns>
    bool TryGetPlugin(string name, [NotNullWhen(true)] out IKernelPlugin? plugin);
}
