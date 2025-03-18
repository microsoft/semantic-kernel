// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Diagnostics.CodeAnalysis;

namespace Microsoft.SemanticKernel.Agents;

/// <summary>
/// Provides extension methods for <see cref="AgentDefinition"/>.
/// </summary>
[Experimental("SKEXP0110")]
public static class AgentToolDefinitionExtensions
{
    /// <summary>
    /// Get the configuration value for the specified key.
    /// </summary>
    /// <typeparam name="T">Expected type for the configuration value.</typeparam>
    /// <param name="agentToolDefinition">Agent definition instance.</param>
    /// <param name="key">Key of the configuration value.</param>
    /// <exception cref="InvalidCastException"></exception>
    public static T? GetConfiguration<T>(this AgentToolDefinition agentToolDefinition, string key)
    {
        Verify.NotNull(agentToolDefinition);
        Verify.NotNull(key);

        if (agentToolDefinition.Configuration?.TryGetValue(key, out var value) ?? false)
        {
            if (value == null)
            {
                return default;
            }

            try
            {
                return (T?)Convert.ChangeType(value, typeof(T));
            }
            catch (InvalidCastException)
            {
                throw new InvalidCastException($"The configuration key '{key}' value must be of type '{typeof(T?)}' but is '{value.GetType()}'.");
            }
        }

        return default;
    }


}
