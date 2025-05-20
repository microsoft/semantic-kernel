// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Reflection;

namespace Microsoft.SemanticKernel.Agents.Magentic.Internal;

/// <summary>
/// Extension methods for <see cref="PromptExecutionSettings"/> to support response format operations.
/// </summary>
public static class PromptExecutionSettingsExtensions
{
    private const string ResponseFormatPropertyName = "ResponseFormat";

    /// <summary>
    /// Determines whether the <paramref name="settings"/> object supports a "ResponseFormat" property of type <see cref="object"/>.
    /// </summary>
    /// <param name="settings">The <see cref="PromptExecutionSettings"/> instance to check.</param>
    /// <returns><c>true</c> if the "ResponseFormat" property exists and is of type <see cref="object"/>; otherwise, <c>false</c>.</returns>
    public static bool SupportsResponseFormat(this PromptExecutionSettings settings)
    {
        Type settingsType = settings.GetType();
        PropertyInfo? property = settingsType.GetProperty(ResponseFormatPropertyName);
        return property != null && property.PropertyType == typeof(object);
    }

    /// <summary>
    /// Sets the "ResponseFormat" property of the <paramref name="settings"/> object to the specified response type.
    /// </summary>
    /// <typeparam name="TResponse">The type to set as the response format.</typeparam>
    /// <param name="settings">The <see cref="PromptExecutionSettings"/> instance to update.</param>
    public static void SetResponseFormat<TResponse>(this PromptExecutionSettings settings)
    {
        Type settingsType = settings.GetType();
        PropertyInfo? property = settingsType.GetProperty(ResponseFormatPropertyName);
        property?.SetValue(settings, typeof(TResponse));
    }
}
