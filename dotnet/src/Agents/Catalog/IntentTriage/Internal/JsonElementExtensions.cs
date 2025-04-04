// Copyright (c) Microsoft. All rights reserved.

using System.Linq;
using System.Text.Json;

namespace Microsoft.SemanticKernel.Agents.IntentTriage;

/// <summary>
/// Extension methods for <see cref="JsonElement"/>
/// </summary>
internal static class JsonElementExtensions
{
    public static JsonElement? GetProperty(this JsonElement element, params string[] propertyNames)
        => GetProperty((JsonElement?)element, propertyNames);

    public static JsonElement? GetProperty(this JsonElement? element, params string[] propertyNames)
    {
        if (element == null)
        {
            return null;
        }

        foreach (string propertyName in propertyNames)
        {
            if (!element.Value.TryGetProperty(propertyName, out JsonElement childElement))
            {
                return null;
            }

            element = childElement;
        }

        return element;
    }

    public static JsonElement? GetFirstArrayElement(this JsonElement? element)
    {
        if (element == null)
        {
            return null;
        }

        if (element.Value.ValueKind != JsonValueKind.Array ||
            element.Value.GetArrayLength() == 0)
        {
            return null;
        }

        return element.Value.EnumerateArray().First();
    }

    public static string? GetStringValue(this JsonElement? element, string propertyName)
    {
        if (element == null)
        {
            return null;
        }

        if (!element.Value.TryGetProperty(propertyName, out JsonElement childElement))
        {
            return null;
        }

        return childElement.GetString();
    }

    public static decimal? GetDecimalValue(this JsonElement? element, string propertyName)
    {
        if (element == null)
        {
            return default;
        }

        if (!element.Value.TryGetProperty(propertyName, out JsonElement childElement))
        {
            return null;
        }

        return childElement.GetDecimal();
    }
}
