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

    /// <summary>Adds a function to the plugin.</summary>
    /// <param name="function">The function to add.</param>
    /// <exception cref="ArgumentNullException"><paramref name="function"/> is null.</exception>
    /// <exception cref="ArgumentNullException"><paramref name="function"/>'s <see cref="KernelFunction.Name"/> is null.</exception>
    /// <exception cref="ArgumentException">A function with the same <see cref="KernelFunction.Name"/> already exists in this plugin.</exception>
    public void AddFunction(KernelFunction function)
    {
        Verify.NotNull(function);
        this._functions.Add(function.Name, function);
    }

    /// <summary>Adds all of the functions in the specified <paramref name="functions"/> collection to this plugin.</summary>
    /// <param name="functions">The functions to add.</param>
    /// <exception cref="ArgumentNullException"><paramref name="functions"/> is null.</exception>
    /// <exception cref="ArgumentNullException">A function in <paramref name="functions"/>'s has a null <see cref="KernelFunction.Name"/>.</exception>
    /// <exception cref="ArgumentException">A function with the same <see cref="KernelFunction.Name"/> already exists in this plugin.</exception>
    public void AddFunctions(IEnumerable<KernelFunction> functions)
    {
        Verify.NotNull(functions);

        foreach (KernelFunction function in functions)
        {
            this.AddFunction(function);
        }
    }

    /// <inheritdoc/>
    public override IEnumerator<KernelFunction> GetEnumerator() => this._functions.Values.GetEnumerator();
}
