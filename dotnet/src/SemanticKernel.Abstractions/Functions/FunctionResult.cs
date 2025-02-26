// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Globalization;
using System.Linq;
using Microsoft.Extensions.AI;
using Microsoft.SemanticKernel.AI.ChatCompletion;
using Microsoft.SemanticKernel.ChatCompletion;
using MEAI = Microsoft.Extensions.AI;

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

            // Attempting to use the new MEAI Chat types will trigger automatic conversion of SK chat contents.

            // ChatMessageContent as ChatMessage
            if (typeof(ChatMessage).IsAssignableFrom(typeof(T))
                && content is ChatMessageContent chatMessageContent)
            {
                return (T?)(object)chatMessageContent.ToChatMessage();
            }

            // ChatMessageContent as ChatResponse
            if (typeof(ChatResponse).IsAssignableFrom(typeof(T))
                && content is ChatMessageContent singleChoiceMessageContent)
            {
                return (T?)(object)(new MEAI.ChatResponse(singleChoiceMessageContent.ToChatMessage()));
            }

            // List of ChatMessageContent as ChatResponse
            if (typeof(ChatResponse).IsAssignableFrom(typeof(T))
                && content is IReadOnlyList<ChatMessageContent> multipleChoiceMessageList)
            {
                return (T?)(object)(new MEAI.ChatResponse(
                    multipleChoiceMessageList
                        .Select(m => m.ToChatMessage())
                        .ToList()));
            }
        }

        if (this.Value is MEAI.ChatMessage chatMessage)
        {
            if (typeof(T) == typeof(string))
            {
                return (T?)(object?)chatMessage.ToString();
            }

            if (typeof(MEAI.AIContent).IsAssignableFrom(typeof(T)))
            {
                // Return the first matching content type of a message if any
                var updateContent = chatMessage.Contents.FirstOrDefault(c => c is T);
                if (updateContent is not null)
                {
                    return (T)(object)updateContent;
                }
            }

            if (chatMessage.Contents is T contentsList)
            {
                return contentsList;
            }

            if (chatMessage.RawRepresentation is T rawRepresentation)
            {
                return rawRepresentation;
            }

            // Avoid breaking changes this transformation will be dropped once we migrate fully to MEAI abstractions.
            if (typeof(ChatMessageContent).IsAssignableFrom(typeof(T)))
            {
                return (T)(object)chatMessage.ToChatMessageContent();
            }
        }

        if (this.Value is IList<MEAI.ChatMessage> chatMessageList && chatMessageList.Count != 0)
        {
            var firstMessage = chatMessageList[0];

            if (typeof(T) == typeof(string))
            {
                return (T?)(object?)firstMessage.ToString();
            }

            if (typeof(T) == typeof(MEAI.ChatMessage))
            {
                return (T)(object)firstMessage;
            }

            if (typeof(MEAI.AIContent).IsAssignableFrom(typeof(T)))
            {
                // Return the first matching content type of a message if any
                var updateContent = firstMessage.Contents.FirstOrDefault(c => c is T);
                if (updateContent is not null)
                {
                    return (T)(object)updateContent;
                }
            }

            if (firstMessage.RawRepresentation is T rawRepresentation)
            {
                return rawRepresentation;
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
