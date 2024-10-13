// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Reflection;
using Microsoft.SemanticKernel.Experimental.Orchestration.Execution;

<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
namespace Microsoft.SemanticKernel.Experimental.Orchestration;
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
namespace Microsoft.SemanticKernel.Experimental.Orchestration;
=======
=======
<<<<<<< HEAD
namespace Microsoft.SemanticKernel.Experimental.Orchestration;
=======
<<<<<<< div
>>>>>>> main
=======
>>>>>>> origin/main
=======
<<<<<<< HEAD
namespace Microsoft.SemanticKernel.Experimental.Orchestration;
=======
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
namespace Microsoft.SemanticKernel.Experimental.Orchestration;
=======
>>>>>>> Stashed changes
>>>>>>> head
#pragma warning disable IDE0130
namespace Microsoft.SemanticKernel.Experimental.Orchestration;
#pragma warning restore IDE0130
>>>>>>> 9cfcc609b1cbe6e1d6975df1d665fa0b064c5624
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< div
>>>>>>> main
=======
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> head

/// <summary>
/// Step within a <see cref="Flow"/> which defines the step goal, available plugins, required and provided variables.
/// </summary>
public class FlowStep
{
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< Updated upstream
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
    private readonly List<string> _requires = [];
=======
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
<<<<<<< div
>>>>>>> main
=======
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> head
    private readonly List<string> _requires = [];

    private readonly List<string> _provides = [];

    private readonly List<string> _passthrough = [];

    private Dictionary<string, Type?> _pluginTypes = [];
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head

    private Func<Kernel, Dictionary<object, string?>, IEnumerable<object>>? _pluginsFactory;
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< Updated upstream

    private Func<Kernel, Dictionary<object, string?>, IEnumerable<object>>? _pluginsFactory;
>>>>>>> Stashed changes
=======

    private Func<Kernel, Dictionary<object, string?>, IEnumerable<object>>? _pluginsFactory;
=======
>>>>>>> Stashed changes
>>>>>>> Stashed changes
=======
    private readonly List<string> _requires = new();
>>>>>>> origin/main

    private readonly List<string> _provides = [];

    private readonly List<string> _passthrough = [];

    private Dictionary<string, Type?> _pluginTypes = [];

    private Func<IKernel, Dictionary<object, string?>, IEnumerable<object>>? _pluginsFactory;
>>>>>>> 9cfcc609b1cbe6e1d6975df1d665fa0b064c5624
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
=======
>>>>>>> Stashed changes
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======

    private Func<Kernel, Dictionary<object, string?>, IEnumerable<object>>? _pluginsFactory;
=======
    private readonly List<string> _requires = new();

    private readonly List<string> _provides = new();

    private readonly List<string> _passthrough = new();

    private Dictionary<string, Type?> _pluginTypes = new();

    private Func<IKernel, Dictionary<object, string?>, IEnumerable<object>>? _pluginsFactory;
>>>>>>> 9cfcc609b1cbe6e1d6975df1d665fa0b064c5624
<<<<<<< div
>>>>>>> main
=======
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> head

    /// <summary>
    /// Initializes a new instance of the <see cref="FlowStep"/> class.
    /// </summary>
    /// <param name="goal">The goal of step</param>
    /// <param name="pluginsFactory">The factory to get plugins</param>
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
    public FlowStep(string goal, Func<Kernel, Dictionary<object, string?>, IEnumerable<object>>? pluginsFactory = null)
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
    public FlowStep(string goal, Func<Kernel, Dictionary<object, string?>, IEnumerable<object>>? pluginsFactory = null)
=======
    public FlowStep(string goal, Func<IKernel, Dictionary<object, string?>, IEnumerable<object>>? pluginsFactory = null)
>>>>>>> 9cfcc609b1cbe6e1d6975df1d665fa0b064c5624
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
=======
>>>>>>> Stashed changes
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
    public FlowStep(string goal, Func<Kernel, Dictionary<object, string?>, IEnumerable<object>>? pluginsFactory = null)
=======
    public FlowStep(string goal, Func<IKernel, Dictionary<object, string?>, IEnumerable<object>>? pluginsFactory = null)
>>>>>>> 9cfcc609b1cbe6e1d6975df1d665fa0b064c5624
<<<<<<< Updated upstream
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< div
=======
<<<<<<< HEAD
    public FlowStep(string goal, Func<Kernel, Dictionary<object, string?>, IEnumerable<object>>? pluginsFactory = null)
=======
    public FlowStep(string goal, Func<IKernel, Dictionary<object, string?>, IEnumerable<object>>? pluginsFactory = null)
>>>>>>> 9cfcc609b1cbe6e1d6975df1d665fa0b064c5624
>>>>>>> main
=======
>>>>>>> head
    {
        this.Goal = goal;
        this._pluginsFactory = pluginsFactory;
    }

    /// <summary>
    /// Goal of the step
    /// </summary>
    public string Goal { get; set; }

    /// <summary>
    /// <see cref="CompletionType"/> of the step
    /// </summary>
    public CompletionType CompletionType { get; set; } = CompletionType.Once;

    /// <summary>
    /// If the CompletionType is CompletionType.ZeroOrMore, this message will be used to ask the user if they want to execute the current step or skip it.
    /// </summary>
    public string? StartingMessage { get; set; }

    /// <summary>
    /// If the CompletionType is CompletionType.AtLeastOnce or CompletionType.ZeroOrMore, this message will be used to ask the user if they want to try the step again.
    /// </summary>
    public string? TransitionMessage { get; set; } = "Did you want to try the previous step again?";

    /// <summary>
    /// Parameters required for executing the step
    /// </summary>
    public virtual IEnumerable<string> Requires => this._requires;

    /// <summary>
    /// Variables to be provided by the step
    /// </summary>
    public IEnumerable<string> Provides => this._provides;

    /// <summary>
    /// Variables to be passed through on iterations of the step
    /// </summary>
    public IEnumerable<string> Passthrough => this._passthrough;

    /// <summary>
    /// Gets or sets the plugin available for the current step
    /// </summary>
    public List<string>? Plugins
    {
        get => this._pluginTypes.Keys.ToList();
        set
        {
            Dictionary<string, Type?> plugins = GetPluginTypes(value);

            this._pluginTypes = plugins;
            this._pluginsFactory = (kernel, globalPlugins) => this.GetPlugins(globalPlugins, kernel);
        }
    }

<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
    private List<object> GetPlugins(Dictionary<object, string?> globalPlugins, Kernel kernel)
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< Updated upstream
<<<<<<< div
>>>>>>> main
=======
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> head
=======
>>>>>>> Stashed changes
>>>>>>> Stashed changes
<<<<<<< HEAD
    private List<object> GetPlugins(Dictionary<object, string?> globalPlugins, Kernel kernel)
=======
    private List<object> GetPlugins(Dictionary<object, string?> globalPlugins, IKernel kernel)
>>>>>>> 9cfcc609b1cbe6e1d6975df1d665fa0b064c5624
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
=======
>>>>>>> Stashed changes
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< div
>>>>>>> main
=======
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> head
    {
        return this._pluginTypes.Select(kvp =>
        {
            var pluginName = kvp.Key;
            var globalPlugin = globalPlugins.FirstOrDefault(_ => _.Key.GetType().Name.Contains(pluginName)).Key;
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
            if (globalPlugin is not null)
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
            if (globalPlugin is not null)
=======
=======
<<<<<<< div
>>>>>>> main
=======
>>>>>>> origin/main
=======
<<<<<<< main
            if (globalPlugin is not null)
=======
>>>>>>> Stashed changes
=======
<<<<<<< main
            if (globalPlugin is not null)
=======
>>>>>>> Stashed changes
>>>>>>> head
<<<<<<< HEAD
            if (globalPlugin is not null)
=======
            if (globalPlugin != null)
>>>>>>> 9cfcc609b1cbe6e1d6975df1d665fa0b064c5624
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< div
>>>>>>> main
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> origin/main
>>>>>>> head
            {
                return globalPlugin;
            }

            var type = kvp.Value;
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
            if (type is not null)
            {
                try
                {
                    return Activator.CreateInstance(type, BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance, null, [kernel], null);
=======
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
<<<<<<< div
>>>>>>> main
=======
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> head
            if (type is not null)
            {
                try
                {
                    return Activator.CreateInstance(type, BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance, null, [kernel], null);
<<<<<<< div
<<<<<<< div
=======
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< div
=======
>>>>>>> main
=======
>>>>>>> head
=======
>>>>>>> Stashed changes
=======
            if (type != null)
            {
                try
                {
                    return Activator.CreateInstance(type, BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance, null, new object[] { kernel }, null);
>>>>>>> 9cfcc609b1cbe6e1d6975df1d665fa0b064c5624
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< div
>>>>>>> main
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> origin/main
>>>>>>> head
                }
                catch (MissingMethodException)
                {
                    try
                    {
                        return Activator.CreateInstance(type, true);
                    }
                    catch (MissingMethodException)
                    {
                    }
                }
            }

            return null;
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
        }).Where(plugin => plugin is not null).ToList()!;
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
        }).Where(plugin => plugin is not null).ToList()!;
=======
=======
<<<<<<< div
>>>>>>> main
=======
>>>>>>> origin/main
=======
<<<<<<< main
        }).Where(plugin => plugin is not null).ToList()!;
=======
>>>>>>> Stashed changes
=======
<<<<<<< main
        }).Where(plugin => plugin is not null).ToList()!;
=======
>>>>>>> Stashed changes
>>>>>>> head
<<<<<<< HEAD
        }).Where(plugin => plugin is not null).ToList()!;
=======
        }).Where(plugin => plugin != null).ToList()!;
>>>>>>> 9cfcc609b1cbe6e1d6975df1d665fa0b064c5624
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< div
>>>>>>> main
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> origin/main
>>>>>>> head
    }

    private static Dictionary<string, Type?> GetPluginTypes(List<string>? value)
    {
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
        Dictionary<string, Type?> plugins = [];
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
        Dictionary<string, Type?> plugins = [];
=======
=======
<<<<<<< div
>>>>>>> main
=======
>>>>>>> origin/main
=======
<<<<<<< main
        Dictionary<string, Type?> plugins = [];
=======
>>>>>>> Stashed changes
=======
<<<<<<< main
        Dictionary<string, Type?> plugins = [];
=======
>>>>>>> Stashed changes
>>>>>>> head
<<<<<<< HEAD
        Dictionary<string, Type?> plugins = [];
=======
        Dictionary<string, Type?> plugins = new();
>>>>>>> 9cfcc609b1cbe6e1d6975df1d665fa0b064c5624
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< div
>>>>>>> main
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> origin/main
>>>>>>> head

        if (value is not null)
        {
            var types = AppDomain.CurrentDomain.GetAssemblies()
                .Where(a => !a.IsDynamic)
                .SelectMany(a => a.GetTypes())
                .ToList();

            foreach (var pluginName in value)
            {
                if (pluginName is null)
                {
                    continue;
                }

                var type = types.FirstOrDefault(predicate: t => t.FullName?.Equals(pluginName, StringComparison.OrdinalIgnoreCase) ?? false);
                if (type is null)
                {
                    type = types.FirstOrDefault(t => t.FullName?.Contains(pluginName) ?? false);

                    if (type is null)
                    {
                        // If not found, assume the plugin would be loaded separately.
                        plugins.Add(pluginName, null);
                        continue;
                    }
                }

                plugins.Add(pluginName, type);
            }
        }

        return plugins;
    }

    /// <summary>
    /// Register the required arguments for the step
    /// </summary>
    /// <param name="requiredArguments">Array of required arguments</param>
    public void AddRequires(params string[] requiredArguments)
    {
        this.ValidateArguments(requiredArguments);
        this._requires.AddRange(requiredArguments);
    }

    /// <summary>
    /// Register the arguments provided by the step
    /// </summary>
    /// <param name="providedArguments">Array of provided arguments</param>
    public void AddProvides(params string[] providedArguments)
    {
        this.ValidateArguments(providedArguments);
        this._provides.AddRange(providedArguments);
    }

    /// <summary>
    /// Register the arguments passed through by the step
    /// </summary>
    /// <param name="passthroughArguments">Array of passthrough arguments</param>
    /// <param name="isReferencedFlow">Is referenced flow</param>
    public void AddPassthrough(string[] passthroughArguments, bool isReferencedFlow = false)
    {
        // A referenced flow is allowed to have steps that have passthrough arguments even if the completion type is not AtLeastOnce or ZeroOrMore. This is so the step can pass arguments to the outer flow.
        if (!isReferencedFlow
            && passthroughArguments.Length != 0
            && this.CompletionType != CompletionType.AtLeastOnce
            && this.CompletionType != CompletionType.ZeroOrMore)
        {
            throw new ArgumentException("Passthrough arguments can only be set for the AtLeastOnce or ZeroOrMore completion type");
        }

        this.ValidateArguments(passthroughArguments);
        this._passthrough.AddRange(passthroughArguments);
    }

    /// <summary>
    /// Get the plugin instances registered with the step
    /// </summary>
    /// <param name="kernel">The semantic kernel</param>
    /// <param name="globalPlugins">The global plugins available</param>
    /// <returns></returns>
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
    public IEnumerable<object> LoadPlugins(Kernel kernel, Dictionary<object, string?> globalPlugins)
    {
        if (this._pluginsFactory is not null)
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< Updated upstream
<<<<<<< div
>>>>>>> main
=======
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> head
=======
>>>>>>> Stashed changes
>>>>>>> Stashed changes
<<<<<<< HEAD
    public IEnumerable<object> LoadPlugins(Kernel kernel, Dictionary<object, string?> globalPlugins)
    {
        if (this._pluginsFactory is not null)
<<<<<<< div
<<<<<<< div
<<<<<<< main
=======
=======
>>>>>>> main
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< main
=======
>>>>>>> head
=======
>>>>>>> origin/main
=======
=======
<<<<<<< main
=======
=======
>>>>>>> Stashed changes
=======
<<<<<<< main
=======
=======
>>>>>>> Stashed changes
    public IEnumerable<object> LoadPlugins(IKernel kernel, Dictionary<object, string?> globalPlugins)
    {
        if (this._pluginsFactory != null)
>>>>>>> 9cfcc609b1cbe6e1d6975df1d665fa0b064c5624
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< div
>>>>>>> main
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> origin/main
>>>>>>> head
        {
            return this._pluginsFactory(kernel, globalPlugins);
        }

<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
        return [];
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
        return [];
=======
=======
<<<<<<< div
>>>>>>> main
=======
>>>>>>> origin/main
=======
<<<<<<< main
        return [];
=======
>>>>>>> Stashed changes
=======
<<<<<<< main
        return [];
=======
>>>>>>> Stashed changes
>>>>>>> head
<<<<<<< HEAD
        return [];
=======
        return Enumerable.Empty<object>();
>>>>>>> 9cfcc609b1cbe6e1d6975df1d665fa0b064c5624
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< div
>>>>>>> main
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> origin/main
>>>>>>> head
    }

    /// <summary>
    /// Check if the step depends on another step
    /// </summary>
    /// <param name="otherStep">The other step</param>
    /// <returns>true if the step depends on the other step, false otherwise</returns>
    public bool DependsOn(FlowStep otherStep)
    {
        return this.Requires.Intersect(otherStep.Provides).Any();
    }

    private void ValidateArguments(string[] arguments)
    {
        var invalidArguments = arguments.Intersect(Constants.ActionVariableNames.All).ToArray();

        if (invalidArguments.Length != 0)
        {
            throw new ArgumentException($"Invalid arguments: {string.Join(",", invalidArguments)}");
        }
    }
}
