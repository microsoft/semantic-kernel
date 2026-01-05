// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Linq;
#if !UNITY
using Microsoft.Extensions.AI;
#endif

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

                var cloned = f.Clone(name);
                this._functions.Add(cloned.Name, cloned);
            }
        }
    }

    /// <inheritdoc/>
    public override int FunctionCount => this._functions.Count;

    /// <inheritdoc/>
    public override bool TryGetFunction(string name, [NotNullWhen(true)] out KernelFunction? function)
    {
        if (this._functions.TryGetValue(name, out function))
        {
            return true;
        }

        if (this._functions.Count == 0 || name.Length <= this.Name.Length)
        {
            // The function name is too short to have the plugin name aborting the search.
            function = null;
            return false;
        }

#if !UNITY
        // When a kernel function is used as an ai function by IChatClients it needs to be discoverable by the FQN.
        function = (KernelFunction?)this._functions.Values
            .Select(f => f as AIFunction)
            .FirstOrDefault(aiFunction => aiFunction.Name == name);

        return function is not null;
#else
        function = null;
        return false;
#endif
    }

    /// <inheritdoc/>
    public override IEnumerator<KernelFunction> GetEnumerator() => this._functions.Values.GetEnumerator();
}
