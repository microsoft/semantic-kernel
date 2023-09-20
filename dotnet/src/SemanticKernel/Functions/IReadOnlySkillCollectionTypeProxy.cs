// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Diagnostics;
using System.Linq;

#pragma warning disable IDE0130
// ReSharper disable once CheckNamespace - Using the main namespace
namespace Microsoft.SemanticKernel;
#pragma warning restore IDE0130

/// <summary>
/// Debugger type proxy for <see cref="SkillCollection"/>.
/// </summary>
// ReSharper disable once InconsistentNaming
internal sealed class IReadOnlySkillCollectionTypeProxy
{
    private readonly IReadOnlySkillCollection _collection;

    public IReadOnlySkillCollectionTypeProxy(IReadOnlySkillCollection collection) => this._collection = collection;

    [DebuggerBrowsable(DebuggerBrowsableState.RootHidden)]
    public SkillProxy[] Items
    {
        get
        {
            return this._collection.GetFunctionViews()
                .GroupBy(f => f.PluginName)
                .Select(g => new SkillProxy(g) { Name = g.Key })
                .ToArray();
        }
    }

    [DebuggerDisplay("{Name}")]
    public sealed class SkillProxy : List<FunctionView>
    {
        [DebuggerBrowsable(DebuggerBrowsableState.Never)]
        public string? Name;

        public SkillProxy(IEnumerable<FunctionView> functions) : base(functions) { }
    }
}
