// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Concurrent;
using System.Collections.Generic;
using System.ComponentModel;
using System.Globalization;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Represents the result of a <see cref="KernelFunction"/> invocation.
/// </summary>
public sealed class FunctionResult
{
    /// <summary>
    /// Initializes a new instance of the <see cref="FunctionResult"/> class.
    /// </summary>
    /// <param name="functionName">Name of executed function.</param>
    public FunctionResult(string functionName) : this(functionName, null, CultureInfo.InvariantCulture)
    {
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="FunctionResult"/> class.
    /// </summary>
    /// <param name="functionName">Name of executed function.</param>
    /// <param name="value">Function result object.</param>
    /// <param name="culture">The culture configured on the Kernel that executed the function.</param>
    /// <param name="metadata">Metadata associated with the function's execution</param>
    public FunctionResult(string functionName, object? value, CultureInfo culture, IDictionary<string, object?>? metadata = null)
    {
        Verify.NotNullOrWhiteSpace(functionName);
        Verify.NotNull(culture);

        this.FunctionName = functionName;
        this.Value = value;
        this.Culture = culture;
        this.Metadata = metadata;
    }

    /// <summary>
    /// Gets the name of the invoked function.
    /// </summary>
    public string FunctionName { get; }

    /// <summary>
    /// Gets any metadata associated with the function's execution.
    /// </summary>
    public IDictionary<string, object?>? Metadata { get; }

    /// <summary>
    /// Function result type (support inspection).
    /// </summary>
    public Type? ValueType => this.Value?.GetType();

    /// <summary>
    /// Returns function result value.
    /// </summary>
    /// <typeparam name="T">Target type for result value casting.</typeparam>
    /// <exception cref="InvalidCastException">Thrown when it's not possible to cast result value to <typeparamref name="T"/>.</exception>
    public T? GetValue<T>()
    {
        if (this.Value is null)
        {
            return default;
        }

        if (this.Value is T typedResult)
        {
            return typedResult;
        }

        throw new InvalidCastException($"Cannot cast {this.Value.GetType()} to {typeof(T)}");
    }

    /// <inheritdoc/>
    public override string ToString() =>
        ConvertToString(this.Value, this.Culture) ?? string.Empty;

    /// <summary>
    /// Function result object.
    /// </summary>
    internal object? Value { get; }

    /// <summary>
    /// The culture configured on the Kernel that executed the function.
    /// </summary>
    internal CultureInfo Culture { get; }

    private static string? ConvertToString(object? value, CultureInfo culture)
    {
        if (value == null) { return null; }

        var sourceType = value.GetType();

        var converterFunction = GetTypeConverterDelegate(sourceType);

        return converterFunction == null
            ? value.ToString()
            : converterFunction(value, culture);
    }

    private static Func<object?, CultureInfo, string?>? GetTypeConverterDelegate(Type sourceType) =>
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
