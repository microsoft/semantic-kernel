// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.Extensions.Configuration;

namespace Microsoft.SemanticKernel.Agents.Service;

/// <summary>
/// Extension methods associated with an <see cref="IConfiguration"/> object.
/// </summary>
public static class ConfigurationExtensions
{
    /// <summary>
    /// Retrieve a configuration value that must be defined.
    /// </summary>
    /// <param name="configuration">The active configuration.</param>
    /// <param name="key">The configuration key.</param>
    /// <returns>The configuration value (never null or empty).</returns>
    /// <exception cref="InvalidOperationException"></exception>
    public static string GetRequiredValue(this IConfiguration configuration, string key)
    {
        string? value = configuration[key];

        if (string.IsNullOrWhiteSpace(value))
        {
            throw new InvalidOperationException($"Missing expected configuration value: {key}");
        }

        return value!;
    }

    /// <summary>
    /// Retrieve a configuration value as a decimal number.
    /// </summary>
    /// <param name="configuration">The active configuration.</param>
    /// <param name="key">The configuration key.</param>
    /// <param name="defaultValue">The default value if the configuration is not defined or is invalid.</param>
    /// <returns>The configuration value (never null or empty).</returns>
    public static decimal GetDecimalValue(this IConfiguration configuration, string key, decimal defaultValue)
    {
        string? value = configuration[key];

        if (decimal.TryParse(value, out decimal result))
        {
            return result;
        }

        return defaultValue;
    }
}
