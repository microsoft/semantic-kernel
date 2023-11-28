// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections;
using System.Collections.Generic;
using System.Diagnostics;
using System.Diagnostics.CodeAnalysis;
using System.Linq;

#pragma warning disable RCS1168 // Parameter name differs from base name.
#pragma warning disable CA1725 // Parameter names should match base declaration
#pragma warning disable IDE0130 // Namespace does not match folder structure

namespace Microsoft.SemanticKernel;

/// <summary>Provides a collection of <see cref="IKernelPlugin"/>s.</summary>
/// <remarks>
/// All plugins stored in the collection must have a unique, ordinal case-insensitive name.
/// All name lookups are performed using ordinal case-insensitive comparisons.
/// </remarks>
[DebuggerDisplay("Count = {Count}")]
[DebuggerTypeProxy(typeof(KernelPluginCollection.TypeProxy))]
public sealed class KernelPluginCollection : ICollection<IKernelPlugin>, IReadOnlyKernelPluginCollection
{
    /// <summary>The underlying dictionary of plugins.</summary>
    private readonly Dictionary<string, IKernelPlugin> _plugins;

    /// <summary>Initializes a collection of plugins.</summary>
    public KernelPluginCollection() => this._plugins = new(StringComparer.OrdinalIgnoreCase);

    /// <summary>Initializes a collection of plugins that contains all of the plugins from the provided collection.</summary>
    /// <param name="plugins">The initial collection of plugins to populate this collection.</param>
    /// <exception cref="ArgumentNullException"><paramref name="plugins"/> is null.</exception>
    /// <exception cref="ArgumentException"><paramref name="plugins"/> contains multiple plugins with the same name.</exception>
    public KernelPluginCollection(IEnumerable<IKernelPlugin> plugins)
    {
        Verify.NotNull(plugins);

        if (plugins is KernelPluginCollection existing)
        {
            this._plugins = new(existing._plugins, StringComparer.OrdinalIgnoreCase);
        }
        else
        {
            this._plugins = new(plugins is ICollection<IKernelPlugin> c ? c.Count : 0, StringComparer.OrdinalIgnoreCase);
            this.AddRange(plugins);
        }
    }

    /// <summary>Gets the number of plugins in the collection.</summary>
    public int Count => this._plugins.Count;

    /// <summary>Adds the plugin to the plugin collection.</summary>
    /// <param name="plugin">The plugin to add.</param>
    /// <exception cref="ArgumentNullException"><paramref name="plugin"/> is null.</exception>
    /// <exception cref="ArgumentNullException"><paramref name="plugin"/>.<see cref="IKernelPlugin.Name"/> is null.</exception>
    /// <exception cref="ArgumentException">A plugin with the same name already exists in the collection.</exception>
    public void Add(IKernelPlugin plugin)
    {
        Verify.NotNull(plugin);

        string name = plugin.Name;
        Verify.NotNull(name, "plugin.Name");

        this._plugins.Add(name, plugin);
    }

    /// <summary>Adds a collection of plugins to this plugin collection.</summary>
    /// <param name="plugins">The plugins to add.</param>
    /// <exception cref="ArgumentNullException"><paramref name="plugins"/> is null.</exception>
    /// <exception cref="ArgumentNullException"><paramref name="plugins"/> contains a null plugin.</exception>
    /// <exception cref="ArgumentNullException">A plugin in <paramref name="plugins"/> has a null <see cref="IKernelPlugin.Name"/>.</exception>
    /// <exception cref="ArgumentException">A plugin with the same name as a plugin in <paramref name="plugins"/> already exists in the collection.</exception>
    public void AddRange(IEnumerable<IKernelPlugin> plugins)
    {
        Verify.NotNull(plugins);

        foreach (IKernelPlugin plugin in plugins)
        {
            this.Add(plugin);
        }
    }

    /// <summary>Removes the specified plugin from the collection.</summary>
    /// <param name="plugin">The plugin to remove.</param>
    /// <returns>true if <paramref name="plugin"/> was in the collection and could be removed; otherwise, false.</returns>
    public bool Remove(IKernelPlugin plugin)
    {
        Verify.NotNull(plugin);

        if (this._plugins.TryGetValue(plugin.Name, out IKernelPlugin? existing) && existing == plugin)
        {
            return this._plugins.Remove(plugin.Name);
        }

        return false;
    }

    /// <summary>Removes all plugins from the collection.</summary>
    public void Clear() => this._plugins.Clear();

    /// <summary>Gets an enumerable of all plugins stored in this collection.</summary>
    public IEnumerator<IKernelPlugin> GetEnumerator() => this._plugins.Values.GetEnumerator();

    /// <summary>Gets an enumerable of all plugins stored in this collection.</summary>
    IEnumerator IEnumerable.GetEnumerator() => this.GetEnumerator();

    /// <summary>Gets whether the collection contains the specified plugin.</summary>
    /// <param name="plugin">The plugin.</param>
    /// <returns>true if the collection contains the plugin; otherwise, false.</returns>
    public bool Contains(IKernelPlugin plugin)
    {
        Verify.NotNull(plugin);

        return this._plugins.TryGetValue(plugin.Name, out IKernelPlugin? existing) && plugin == existing;
    }

    /// <inheritdoc/>
    public IKernelPlugin this[string name]
    {
        get
        {
            if (!this.TryGetPlugin(name, out IKernelPlugin? plugin))
            {
                throw new KeyNotFoundException($"Plugin {name} not found.");
            }

            return plugin;
        }
    }

    /// <summary>Gets a plugin from the collection by name.</summary>
    /// <param name="name">The name of the plugin.</param>
    /// <param name="plugin">The plugin if found in the collection.</param>
    /// <returns>true if the collection contains the plugin; otherwise, false.</returns>
    public bool TryGetPlugin(string name, [NotNullWhen(true)] out IKernelPlugin? plugin) =>
        this._plugins.TryGetValue(name, out plugin);

    void ICollection<IKernelPlugin>.CopyTo(IKernelPlugin[] array, int arrayIndex) =>
        ((IDictionary<string, IKernelPlugin>)this._plugins).Values.CopyTo(array, arrayIndex);

    bool ICollection<IKernelPlugin>.IsReadOnly => false;

    /// <summary>Debugger type proxy for nicer interaction with the collection in a debugger.</summary>
    private sealed class TypeProxy
    {
        private readonly KernelPluginCollection _collection;

        public TypeProxy(KernelPluginCollection collection) => this._collection = collection;

        [DebuggerBrowsable(DebuggerBrowsableState.RootHidden)]
        public IKernelPlugin[] Plugins => this._collection._plugins.Values.ToArray();
    }
}
