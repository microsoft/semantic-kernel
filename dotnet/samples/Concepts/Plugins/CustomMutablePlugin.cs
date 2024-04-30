// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;
using Microsoft.SemanticKernel;

namespace Plugins;

/// <summary>
/// This example shows how to create a mutable <see cref="KernelPlugin"/>.
/// </summary>
public class CustomMutablePlugin(ITestOutputHelper output) : BaseTest(output)
{
    [Fact]
    public async Task RunAsync()
    {
        var plugin = new MutableKernelPlugin("Plugin");
        plugin.AddFunction(KernelFunctionFactory.CreateFromMethod(() => "Plugin.Function", "Function"));

        var kernel = new Kernel();
        kernel.Plugins.Add(plugin);

        var result = await kernel.InvokeAsync(kernel.Plugins["Plugin"]["Function"]);

        Console.WriteLine($"Result: {result}");
    }

    /// <summary>
    /// Provides an <see cref="KernelPlugin"/> implementation around a collection of functions.
    /// </summary>
    public class MutableKernelPlugin : KernelPlugin
    {
        /// <summary>The collection of functions associated with this plugin.</summary>
        private readonly Dictionary<string, KernelFunction> _functions;

        /// <summary>Initializes the new plugin from the provided name, description, and function collection.</summary>
        /// <param name="name">The name for the plugin.</param>
        /// <param name="description">A description of the plugin.</param>
        /// <param name="functions">The initial functions to be available as part of the plugin.</param>
        /// <exception cref="ArgumentNullException"><paramref name="functions"/> contains a null function.</exception>
        /// <exception cref="ArgumentException"><paramref name="functions"/> contains two functions with the same name.</exception>
        public MutableKernelPlugin(string name, string? description = null, IEnumerable<KernelFunction>? functions = null) : base(name, description)
        {
            this._functions = new Dictionary<string, KernelFunction>(StringComparer.OrdinalIgnoreCase);
            if (functions is not null)
            {
                foreach (KernelFunction f in functions)
                {
                    ArgumentNullException.ThrowIfNull(f);

                    var cloned = f.Clone(name);
                    this._functions.Add(cloned.Name, cloned);
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
            ArgumentNullException.ThrowIfNull(function);

            var cloned = function.Clone(this.Name);
            this._functions.Add(cloned.Name, cloned);
        }

        /// <inheritdoc/>
        public override IEnumerator<KernelFunction> GetEnumerator() => this._functions.Values.GetEnumerator();
    }
}
