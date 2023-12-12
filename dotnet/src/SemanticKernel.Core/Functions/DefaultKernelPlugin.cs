// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Provides an <see cref="KernelPlugin"/> implementation around a collection of functions.
/// </summary>
internal sealed class DefaultKernelPlugin : KernelPlugin
{
    /// <summary>The collection of functions associated with this plugin.</summary>
    private readonly Dictionary<string, KernelFunction> _functions;

    /// <summary>Initializes the new plugin from the provided name, description, and function collection.</summary>
    /// <param name="name">The name for the plugin.</param>
    /// <param name="description">A description of the plugin.</param>
    /// <param name="functions">The initial functions to be available as part of the plugin.</param>
    /// <exception cref="ArgumentException"><paramref name="name"/> is null.</exception>
    /// <exception cref="ArgumentException"><paramref name="name"/> is an invalid plugin name.</exception>
    /// <exception cref="ArgumentNullException"><paramref name="functions"/> contains a null function.</exception>
    /// <exception cref="ArgumentException"><paramref name="functions"/> contains two functions with the same name.</exception>
    internal DefaultKernelPlugin(string name, string? description, IEnumerable<KernelFunction>? functions = null) : base(name, description)
    {
        this._functions = new Dictionary<string, KernelFunction>(StringComparer.OrdinalIgnoreCase);
        if (functions is not null)
        {
            foreach (KernelFunction f in functions)
            {
                Verify.NotNull(f, nameof(functions));
                this._functions.Add(f.Name, f);
            }
        }
    }

    /// <inheritdoc/>
    public override int FunctionCount => this._functions.Count;

    /// <inheritdoc/>
    public override bool TryGetFunction(string name, [NotNullWhen(true)] out KernelFunction? function) =>
        this._functions.TryGetValue(name, out function);

    /// <inheritdoc/>
    public override IEnumerator<KernelFunction> GetEnumerator() => this._functions.Values.GetEnumerator();
}
