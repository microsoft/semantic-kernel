// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Diagnostics;
using System.Linq;

#pragma warning disable IDE0130
// ReSharper disable once CheckNamespace - Using the main namespace
namespace Microsoft.SemanticKernel;
#pragma warning restore IDE0130

/// <summary>
/// Debugger type proxy for <see cref="IReadOnlyFunctionCollection"/>.
/// </summary>
// ReSharper disable once InconsistentNaming
internal sealed class IReadOnlyFunctionCollectionTypeProxy
{
    private readonly IReadOnlyFunctionCollection _collection;

    public IReadOnlyFunctionCollectionTypeProxy(IReadOnlyFunctionCollection collection) => this._collection = collection;

    [DebuggerBrowsable(DebuggerBrowsableState.RootHidden)]
    public FunctionsProxy[] Functions
    {
        get
        {
            return this._collection.GetFunctionViews()
                .GroupBy(f => f.PluginName)
                .Select(g => new FunctionsProxy(g) { Name = g.Key })
                .ToArray();
        }
    }

    [DebuggerDisplay("{Name}")]
    public sealed class FunctionsProxy : List<FunctionView>
    {
        [DebuggerBrowsable(DebuggerBrowsableState.Never)]
        public string? Name;

        public FunctionsProxy(IEnumerable<FunctionView> functions) : base(functions) { }
    }
}
