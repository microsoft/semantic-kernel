// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
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
    /// <param name="function">The <see cref="KernelFunction"/> whose result is represented by this instance.</param>
    /// <param name="value">The resulting object of the function's invocation.</param>
    /// <param name="culture">The culture configured on the <see cref="Kernel"/> that executed the function.</param>
    /// <param name="metadata">Metadata associated with the function's execution</param>
    public FunctionResult(KernelFunction function, object? value = null, CultureInfo? culture = null, IReadOnlyDictionary<string, object?>? metadata = null)
    {
        Verify.NotNull(function);

        this.Function = function;
        this.Value = value;
        this.Culture = culture ?? CultureInfo.InvariantCulture;
        this.Metadata = metadata;
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="FunctionResult"/> class.
    /// </summary>
    /// <param name="result">Instance of <see cref="FunctionResult"/> with result data to copy.</param>
    /// <param name="value">The resulting object of the function's invocation.</param>
    public FunctionResult(FunctionResult result, object? value = null)
    {
        Verify.NotNull(result);

        this.Function = result.Function;
        this.Value = value ?? result.Value;
        this.Culture = result.Culture;
        this.Metadata = result.Metadata;
        this.RenderedPrompt = result.RenderedPrompt;
    }

    /// <summary>
    /// Gets the <see cref="KernelFunction"/> whose result is represented by this instance.
    /// </summary>
    public KernelFunction Function { get; init; }

    /// <summary>
    /// Gets any metadata associated with the function's execution.
    /// </summary>
    public IReadOnlyDictionary<string, object?>? Metadata { get; init; }

    /// <summary>
    /// The culture configured on the Kernel that executed the function.
    /// </summary>
    public CultureInfo Culture { get; init; }

    /// <summary>
    /// Gets the <see cref="Type"/> of the function's result.
    /// </summary>
    /// <remarks>
    /// This or a base type is the type expected to be passed as the generic
    /// argument to <see cref="GetValue{T}"/>.
    /// </remarks>
    public Type? ValueType => this.Value?.GetType();

    /// <summary>
    /// Gets the prompt used during function invocation if any was rendered.
    /// </summary>
    public string? RenderedPrompt { get; internal set; }

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

        if (this.Value is KernelContent content)
        {
            if (typeof(T) == typeof(string))
            {
                return (T?)(object?)content.ToString();
            }

            if (content.InnerContent is T innerContent)
            {
                return innerContent;
            }
        }

        throw new InvalidCastException($"Cannot cast {this.Value.GetType()} to {typeof(T)}");
    }

    /// <inheritdoc/>
    public override string ToString() =>
        InternalTypeConverter.ConvertToString(this.Value, this.Culture) ?? string.Empty;

    /// <summary>
    /// Function result object.
    /// </summary>
    internal object? Value { get; }
}
