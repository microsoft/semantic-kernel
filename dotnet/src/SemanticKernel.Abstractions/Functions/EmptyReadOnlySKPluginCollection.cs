// Copyright (c) Microsoft. All rights reserved.

using System.Collections;
using System.Collections.Generic;
using System.Diagnostics;
using System.Diagnostics.CodeAnalysis;
using System.Linq;

#pragma warning disable IDE0130

// ReSharper disable once CheckNamespace - Using the main namespace
namespace Microsoft.SemanticKernel;

[DebuggerDisplay("Count = 0")]
internal sealed class EmptyReadOnlyPluginCollection : IReadOnlySKPluginCollection
{
    public static EmptyReadOnlyPluginCollection Instance { get; } = new();

    public int Count => 0;

    public IEnumerator<ISKPlugin> GetEnumerator() => Enumerable.Empty<ISKPlugin>().GetEnumerator();

    public bool TryGetPlugin(string name, [NotNullWhen(true)] out ISKPlugin? plugin)
    {
        plugin = null;
        return false;
    }

    public ISKPlugin this[string name] => throw new KeyNotFoundException();

    IEnumerator IEnumerable.GetEnumerator() => this.GetEnumerator();
}
