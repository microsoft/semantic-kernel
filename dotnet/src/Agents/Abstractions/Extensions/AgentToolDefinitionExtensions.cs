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
    /// Get the option value for the specified key.
    /// </summary>
    /// <typeparam name="T">Expected type for the option value.</typeparam>
    /// <param name="agentToolDefinition">Agent definition instance.</param>
    /// <param name="key">Key of the option value.</param>
    /// <exception cref="InvalidCastException"></exception>
    public static T? GetOption<T>(this AgentToolDefinition agentToolDefinition, string key)
    {
        Verify.NotNull(agentToolDefinition);
        Verify.NotNull(key);

        if (agentToolDefinition.Options?.TryGetValue(key, out var value) ?? false)
        {
            if (value == null)
            {
                return default;
            }

            try
            {
                return (T?)Convert.ChangeType(value, typeof(T));
            }
            catch (InvalidCastException ex)
            {
                throw new InvalidCastException($"The option key '{key}' value must be of type '{typeof(T?)}' but is '{value.GetType()}'.", ex);
            }
        }

        return default;
    }
}
