// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Text.Json.Serialization;
#if !UNITY
using Microsoft.Extensions.AI;
#endif

#pragma warning disable CA1710 // Identifiers should have correct suffix

namespace Microsoft.SemanticKernel;

/// <summary>
/// Provides a collection of arguments for operations such as <see cref="KernelFunction"/>'s InvokeAsync
/// and <see cref="IPromptTemplate"/>'s RenderAsync.
/// </summary>
/// <remarks>
/// A <see cref="KernelArguments"/> is a dictionary of argument names and values. It also carries a
/// <see cref="PromptExecutionSettings"/>, accessible via the <see cref="ExecutionSettings"/> property.
/// </remarks>
#if !UNITY
public sealed class KernelArguments : AIFunctionArguments
#else
public sealed class KernelArguments : Dictionary<string, object?>
#endif
{
    private IReadOnlyDictionary<string, PromptExecutionSettings>? _executionSettings;

    /// <summary>
    /// Initializes a new instance of the <see cref="KernelArguments"/> class with the specified AI execution settings.
    /// </summary>
    [JsonConstructor]
    public KernelArguments()
        : base(StringComparer.OrdinalIgnoreCase)
    {
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="KernelArguments"/> class with the specified AI execution settings.
    /// </summary>
    /// <param name="executionSettings">The prompt execution settings.</param>
    public KernelArguments(PromptExecutionSettings? executionSettings)
        : this(executionSettings: executionSettings is null ? null : [executionSettings])
    {
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="KernelArguments"/> class with the specified AI execution settings.
    /// </summary>
    /// <param name="executionSettings">The prompt execution settings.</param>
    public KernelArguments(IEnumerable<PromptExecutionSettings>? executionSettings)
        : base(StringComparer.OrdinalIgnoreCase)
    {
        if (executionSettings is not null)
        {
            var newExecutionSettings = new Dictionary<string, PromptExecutionSettings>();
            foreach (var settings in executionSettings)
            {
                var targetServiceId = settings.ServiceId ?? PromptExecutionSettings.DefaultServiceId;
                if (newExecutionSettings.ContainsKey(targetServiceId))
                {
                    var exceptionMessage = (targetServiceId == PromptExecutionSettings.DefaultServiceId)
                        ? $"Multiple prompt execution settings with the default service id '{PromptExecutionSettings.DefaultServiceId}' or no service id have been provided. Specify a single default prompt execution settings and provide a unique service id for all other instances."
                        : $"Multiple prompt execution settings with the service id '{targetServiceId}' have been provided. Provide a unique service id for all instances.";

                    throw new ArgumentException(exceptionMessage, nameof(executionSettings));
                }

                newExecutionSettings[targetServiceId] = settings;
            }

            this.ExecutionSettings = newExecutionSettings;
        }
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="KernelArguments"/> class that contains elements copied from the specified <see cref="IDictionary{TKey, TValue}"/>.
    /// </summary>
    /// <param name="source">The <see cref="IDictionary{TKey, TValue}"/> whose elements are copied the new <see cref="KernelArguments"/>.</param>
    /// <param name="executionSettings">The prompt execution settings.</param>
    /// <remarks>
    /// If <paramref name="executionSettings"/> is non-null, it is used as the <see cref="ExecutionSettings"/> for this new instance.
    /// Otherwise, if the source is a <see cref="KernelArguments"/>, its <see cref="ExecutionSettings"/> are used.
    /// </remarks>
    public KernelArguments(IDictionary<string, object?> source, Dictionary<string, PromptExecutionSettings>? executionSettings = null)
        : base(source, StringComparer.OrdinalIgnoreCase)
    {
        this.ExecutionSettings = executionSettings ?? (source as KernelArguments)?.ExecutionSettings;
    }

    /// <summary>
    /// Gets or sets the prompt execution settings.
    /// </summary>
    /// <remarks>
    /// The settings dictionary is keyed by the service ID, or <see cref="PromptExecutionSettings.DefaultServiceId"/> for the default execution settings.
    /// When setting, the service id of each <see cref="PromptExecutionSettings"/> must match the key in the dictionary.
    /// </remarks>
    public IReadOnlyDictionary<string, PromptExecutionSettings>? ExecutionSettings
    {
        get => this._executionSettings;
        set
        {
            if (value is { Count: > 0 })
            {
                foreach (var kv in value!)
                {
                    // Ensures that if a service id is specified it needs to match to the current key in the dictionary.
                    if (!string.IsNullOrWhiteSpace(kv.Value.ServiceId) && kv.Key != kv.Value.ServiceId)
                    {
                        throw new ArgumentException($"Service id '{kv.Value.ServiceId}' must match the key '{kv.Key}'.", nameof(this.ExecutionSettings));
                    }
                }
            }

            this._executionSettings = value;
        }
    }

    /// <summary>Determines whether the <see cref="KernelArguments"/> contains an argument with the specified name.</summary>
    /// <param name="name">The name of the argument to locate.</param>
    /// <returns>true if the arguments contains an argument with the specified named; otherwise, false.</returns>
    /// <exception cref="ArgumentNullException"><paramref name="name"/> is null.</exception>
    public bool ContainsName(string name)
    {
        Verify.NotNull(name);
        return base.ContainsKey(name);
    }

    /// <summary>Gets an <see cref="ICollection{String}"/> of all of the arguments names.</summary>
    public ICollection<string> Names => this.Keys;
}
