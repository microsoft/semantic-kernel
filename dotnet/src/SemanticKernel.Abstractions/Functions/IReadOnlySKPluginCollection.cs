// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;

#pragma warning disable IDE0130

// ReSharper disable once CheckNamespace - Using the main namespace
namespace Microsoft.SemanticKernel;

/// <summary>Provides a read-only collection of <see cref="ISKPlugin"/>s.</summary>
public interface IReadOnlySKPluginCollection : IReadOnlyCollection<ISKPlugin>
{
    /// <summary>Gets a plugin from the collection by name.</summary>
    /// <param name="name">The name of the plugin.</param>
    /// <returns>The plugin.</returns>
    ISKPlugin this[string name] { get; }

    /// <summary>Gets a plugin from the collection by name.</summary>
    /// <param name="name">The name of the plugin.</param>
    /// <param name="plugin">The plugin if found in the collection.</param>
    /// <returns>true if the collection contains the plugin; otherwise, false.</returns>
    bool TryGetPlugin(string name, [NotNullWhen(true)] out ISKPlugin? plugin);
}
