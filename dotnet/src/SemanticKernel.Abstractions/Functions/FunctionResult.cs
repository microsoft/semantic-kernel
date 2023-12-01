// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Concurrent;
using System.Collections.Generic;
using System.ComponentModel;
using System.Globalization;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Function result after execution.
/// </summary>
public sealed class FunctionResult
{
    internal Dictionary<string, object>? _metadata;

    /// <summary>
    /// Name of executed function.
    /// </summary>
    public string FunctionName { get; internal set; }

    /// <summary>
    /// Return true if the function result is for a function that was cancelled.
    /// </summary>
    public bool IsCancellationRequested { get; internal set; }

    /// <summary>
    /// Return true if the function should be skipped.
    /// </summary>
    public bool IsSkipRequested { get; internal set; }

    /// <summary>
    /// Return true if the function should be repeated.
    /// </summary>
    public bool IsRepeatRequested { get; internal set; }

    /// <summary>
    /// Metadata for storing additional information about function execution result.
    /// </summary>
    public Dictionary<string, object> Metadata
    {
        get => this._metadata ??= new();
        internal set => this._metadata = value;
    }

    /// <summary>
    /// Function result object.
    /// </summary>
    internal object? Value { get; private set; } = null;

    /// <summary>
    /// The culture configured on the Kernel that executed the function.
    /// </summary>
    internal CultureInfo Culture { get; set; }

    /// <summary>
    /// Initializes a new instance of the <see cref="FunctionResult"/> class.
    /// </summary>
    /// <param name="functionName">Name of executed function.</param>
    public FunctionResult(string functionName)
    {
        this.FunctionName = functionName;
        this.Culture = CultureInfo.InvariantCulture;
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="FunctionResult"/> class.
    /// </summary>
    /// <param name="functionName">Name of executed function.</param>
    /// <param name="value">Function result object.</param>
    /// <param name="culture">The culture configured on the Kernel that executed the function.</param>
    public FunctionResult(string functionName, object? value, CultureInfo culture)
        : this(functionName)
    {
        this.Value = value;
        this.Culture = culture;
    }

    /// <summary>
    /// Returns function result value.
    /// </summary>
    /// <typeparam name="T">Target type for result value casting.</typeparam>
    /// <exception cref="InvalidCastException">Thrown when it's not possible to cast result value to <typeparamref name="T"/>.</exception>
    public T? GetValue<T>()
    {
        if (this.IsCancellationRequested)
        {
            throw new OperationCanceledException("Cannot get result value from a cancelled function.");
        }

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

    /// <summary>
    /// Get typed value from metadata.
    /// </summary>
    public bool TryGetMetadataValue<T>(string key, out T value)
    {
        if (this._metadata is { } metadata &&
            metadata.TryGetValue(key, out object? valueObject) &&
            valueObject is T typedValue)
        {
            value = typedValue;
            return true;
        }

        value = default!;
        return false;
    }

    /// <inheritdoc/>
    public override string ToString()
    {
        return ConvertToString(this.Value, this.Culture) ?? string.Empty;
    }

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
