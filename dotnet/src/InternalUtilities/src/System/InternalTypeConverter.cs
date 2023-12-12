// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Concurrent;
using System.ComponentModel;
using System.Globalization;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Provides internal utility methods for converting types to strings with consideration for CultureInfo.
/// </summary>
internal static class InternalTypeConverter
{
    /// <summary>
    /// Converts the given object value to a string representation using the appropriate CultureInfo.
    /// </summary>
    /// <param name="value">The object to convert.</param>
    /// <param name="culture">The CultureInfo to consider during conversion.</param>
    /// <returns>A string representation of the object value, considering the specified CultureInfo.</returns>
    public static string? ConvertToString(object? value, CultureInfo culture)
    {
        if (value == null) { return null; }

        var sourceType = value.GetType();

        var converterDelegate = GetTypeToStringConverterDelegate(sourceType);

        return converterDelegate == null
            ? value.ToString()
            : converterDelegate(value, culture);
    }

    /// <summary>
    /// Retrieves a type-to-string converter delegate for the specified source type.
    /// </summary>
    /// <param name="sourceType">The source Type for which to retrieve the type-to-string converter delegate.</param>
    /// <returns>A Func delegate for converting the source type to a string, considering CultureInfo, or null if no suitable converter is found.</returns>
    private static Func<object?, CultureInfo, string?>? GetTypeToStringConverterDelegate(Type sourceType) =>
        s_converters.GetOrAdd(sourceType, static sourceType =>
        {
            // Strings just render as themselves.
            if (sourceType == typeof(string))
            {
                return (input, cultureInfo) => (string)input!;
            }

            // Look up and use a type converter.
            if (TypeConverterFactory.GetTypeConverter(sourceType) is TypeConverter converter && converter.CanConvertTo(typeof(string)))
            {
                return (input, cultureInfo) =>
                {
                    return converter.ConvertToString(context: null, cultureInfo, input);
                };
            }

            return null;
        });

    /// <summary>Converter functions for converting types to strings.</summary>
    private static readonly ConcurrentDictionary<Type, Func<object?, CultureInfo, string?>?> s_converters = new();
}
