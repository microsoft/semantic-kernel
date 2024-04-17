// Copyright (c) Microsoft. All rights reserved.
using System;
using System.ComponentModel;
using System.Text.Json;

namespace Microsoft.SemanticKernel.Agents.Chat;

/// <summary>
/// Responsible for processing a <see cref="FunctionResult"/> and returning a strongly
/// typed result for either a <see cref="KernelFunctionSelectionStrategy"/> or
/// <see cref="KernelFunctionTerminationStrategy"/>.
/// </summary>
/// <typeparam name="TResult">The target type of the <see cref="FunctionResult"/>.</typeparam>
public class FunctionResultProcessor<TResult>
{
    /// <summary>
    /// Responsible for translating the provided text result to the requested type.
    /// </summary>
    /// <param name="result">The text content from the function result.</param>
    /// <returns>A translated result.</returns>
    protected virtual TResult? ProcessTextResult(string result)
        => this.ConvertResult(result);

    /// <summary>
    /// Process a <see cref="FunctionResult"/> and translate to the requested type.
    /// </summary>
    /// <param name="result">The result from a <see cref="KernelFunction"/>.</param>
    /// <returns>A translated result of the requested type.</returns>
    public TResult? InterpretResult(FunctionResult result)
    {
        // Is result already of the requested type?
        if (result.ValueType == typeof(TResult))
        {
            return result.GetValue<TResult>();
        }

        string? rawContent = result.GetValue<string>();

        if (!string.IsNullOrEmpty(rawContent))
        {
            return this.ProcessTextResult(rawContent!);
        }

        return default;
    }

    /// <summary>
    /// Convert the provided text to the processor type.
    /// </summary>
    /// <param name="result">A text result</param>
    /// <returns>A result converted to the requested type.</returns>
    protected TResult? ConvertResult(string result)
    {
        TResult? parsedResult = default;

        if (typeof(string) == typeof(TResult))
        {
            parsedResult = (TResult?)(object?)result;
        }
        else
        {
            TypeConverter? converter = TypeConverterFactory.GetTypeConverter(typeof(TResult));
            try
            {
                if (converter != null)
                {
                    parsedResult = (TResult?)converter.ConvertFrom(result);
                }
                else
                {
                    parsedResult = JsonSerializer.Deserialize<TResult>(result);
                }
            }
            catch (Exception exception) when (!exception.IsCriticalException())
            {
                // Allow default fall-through.
            }
        }

        return parsedResult;
    }

    internal static FunctionResultProcessor<TResult> CreateDefaultInstance(TResult defaultValue)
        => new DefaultFunctionResultProcessor(defaultValue);

    /// <summary>
    /// Used as default for the specified type.
    /// </summary>
    private sealed class DefaultFunctionResultProcessor(TResult defaultValue) : FunctionResultProcessor<TResult>
    {
        /// <inheritdoc/>
        protected override TResult? ProcessTextResult(string result)
            => this.ConvertResult(result) ?? defaultValue;
    }
}
