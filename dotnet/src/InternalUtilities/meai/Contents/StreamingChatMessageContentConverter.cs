// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Text;
using System.Text.Json;
using System.Text.Json.Serialization.Metadata;
using Microsoft.Extensions.AI;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Converts <see cref="StreamingChatMessageContent"/> instances into <see cref="ChatResponseUpdate"/> instances.
/// </summary>
/// <remarks>
/// Function call arguments are usually streamed as JSON fragments, such as <c>{"</c> followed by <c>location":"Amst</c>,
/// that are not valid JSON on their own. When converting a whole stream through <see cref="ConvertNext"/>, the fragments of
/// each function call are accumulated instead of being parsed, and <see cref="Complete"/> produces a single update with the
/// complete function calls once the stream ends. This follows the approach of the Microsoft.Extensions.AI OpenAI chat client.
/// </remarks>
internal sealed class StreamingChatMessageContentConverter
{
    private static readonly JsonTypeInfo<IDictionary<string, object?>> s_argumentsTypeInfo =
        (JsonTypeInfo<IDictionary<string, object?>>)AIJsonUtilities.DefaultOptions.GetTypeInfo(typeof(IDictionary<string, object?>));

    /// <summary>The function calls being accumulated, in the order they were first seen.</summary>
    private List<FunctionCallState>? _functionCalls;

    /// <summary>The function call currently receiving fragments for each request and function call index.</summary>
    private Dictionary<(int RequestIndex, int FunctionCallIndex), FunctionCallState>? _functionCallsByIndex;

    private AuthorRole? _functionCallRole;
    private string? _functionCallAuthorName;
    private string? _functionCallModelId;

    /// <summary>
    /// Converts a single <see cref="StreamingChatMessageContent"/>, treating each function call update as a complete function call.
    /// </summary>
    /// <param name="content">The content to convert.</param>
    /// <returns>The converted update.</returns>
    /// <remarks>
    /// Arguments that are not valid JSON are reported through <see cref="Microsoft.Extensions.AI.FunctionCallContent.Exception"/>
    /// instead of being thrown. Use <see cref="ConvertNext"/> and <see cref="Complete"/> to convert a stream whose function call
    /// arguments can arrive as fragments.
    /// </remarks>
    internal static ChatResponseUpdate ToChatResponseUpdate(StreamingChatMessageContent content)
    {
        Verify.NotNull(content);

        return Convert(content, functionCallAccumulator: null);
    }

    /// <summary>
    /// Converts the next <see cref="StreamingChatMessageContent"/> of a stream.
    /// </summary>
    /// <param name="content">The content to convert.</param>
    /// <returns>The converted update, without any function call content.</returns>
    /// <remarks>
    /// Function call updates are accumulated rather than converted. Call <see cref="Complete"/> after the stream ends to get them.
    /// </remarks>
    internal ChatResponseUpdate ConvertNext(StreamingChatMessageContent content)
    {
        Verify.NotNull(content);

        return Convert(content, functionCallAccumulator: this);
    }

    /// <summary>
    /// Creates an update with the complete function calls accumulated by <see cref="ConvertNext"/>.
    /// </summary>
    /// <returns>An update with the complete function calls, or <see langword="null"/> when there are none.</returns>
    /// <remarks>
    /// Each function call is parsed once. Arguments that are not valid JSON are reported through
    /// <see cref="Microsoft.Extensions.AI.FunctionCallContent.Exception"/> instead of being thrown.
    /// </remarks>
    internal ChatResponseUpdate? Complete()
    {
        if (this._functionCalls is null)
        {
            return null;
        }

        ChatResponseUpdate update = new()
        {
            AuthorName = this._functionCallAuthorName,
            ModelId = this._functionCallModelId,
            // Function calls are produced by the model, so default to the assistant role when no update carried a role.
            Role = this._functionCallRole is { } role ? new ChatRole(role.Label) : ChatRole.Assistant,
        };

        foreach (FunctionCallState functionCall in this._functionCalls)
        {
            // A function call without a name can't be invoked, so it is dropped like the Microsoft.Extensions.AI OpenAI chat client does.
            if (string.IsNullOrWhiteSpace(functionCall.Name))
            {
                continue;
            }

            update.Contents.Add(CreateFunctionCallContent(functionCall.CallId ?? string.Empty, functionCall.Name!, functionCall.Arguments?.ToString()));
        }

        return update.Contents.Count > 0 ? update : null;
    }

    private static ChatResponseUpdate Convert(StreamingChatMessageContent content, StreamingChatMessageContentConverter? functionCallAccumulator)
    {
        ChatResponseUpdate update = new()
        {
            AdditionalProperties = content.Metadata is not null ? new AdditionalPropertiesDictionary(content.Metadata) : null,
            AuthorName = content.AuthorName,
            ModelId = content.ModelId,
            RawRepresentation = content.InnerContent,
            Role = content.Role is not null ? new ChatRole(content.Role.Value.Label) : null,
        };

        foreach (var item in content.Items)
        {
            AIContent? aiContent = null;
            switch (item)
            {
                case Microsoft.SemanticKernel.StreamingTextContent tc:
                    aiContent = new Microsoft.Extensions.AI.TextContent(tc.Text);
                    break;

                case Microsoft.SemanticKernel.StreamingFunctionCallUpdateContent fcc when functionCallAccumulator is not null:
                    // Fragments are not valid JSON on their own, so they are only parsed once the stream completes.
                    functionCallAccumulator.Append(fcc, content);
                    break;

                case Microsoft.SemanticKernel.StreamingFunctionCallUpdateContent fcc:
                    aiContent = CreateFunctionCallContent(fcc.CallId ?? string.Empty, fcc.Name ?? string.Empty, fcc.Arguments);
                    break;
            }

            if (aiContent is not null)
            {
                aiContent.RawRepresentation = content;

                update.Contents.Add(aiContent);
            }
        }

        return update;
    }

    private static Microsoft.Extensions.AI.FunctionCallContent CreateFunctionCallContent(string callId, string name, string? arguments)
    {
        if (string.IsNullOrWhiteSpace(arguments))
        {
            return new Microsoft.Extensions.AI.FunctionCallContent(callId, name);
        }

        return Microsoft.Extensions.AI.FunctionCallContent.CreateFromParsedArguments(
            arguments!,
            callId,
            name,
            static json => JsonSerializer.Deserialize(json, s_argumentsTypeInfo));
    }

    private void Append(StreamingFunctionCallUpdateContent update, StreamingChatMessageContent content)
    {
#pragma warning disable SKEXP0001 // RequestIndex is experimental.
        var index = (update.RequestIndex, update.FunctionCallIndex);
#pragma warning restore SKEXP0001

        this._functionCalls ??= [];
        this._functionCallsByIndex ??= [];

        // Fragments that omit the call ID continue the function call at their index. A different call ID at an index that is
        // already in use starts a new function call instead: producers that emit each complete call in a single update use the
        // default index for every call, and an agent stream can span several runs whose indexes restart at zero. Merging those
        // calls would concatenate their arguments into invalid JSON.
        if (!this._functionCallsByIndex.TryGetValue(index, out FunctionCallState? functionCall) ||
            (!string.IsNullOrEmpty(update.CallId) && functionCall.CallId is not null && functionCall.CallId != update.CallId))
        {
            functionCall = new FunctionCallState();
            this._functionCallsByIndex[index] = functionCall;
            this._functionCalls.Add(functionCall);
        }

        if (functionCall.CallId is null && !string.IsNullOrEmpty(update.CallId))
        {
            functionCall.CallId = update.CallId;
        }

        if (functionCall.Name is null && !string.IsNullOrEmpty(update.Name))
        {
            functionCall.Name = update.Name;
        }

        if (!string.IsNullOrEmpty(update.Arguments))
        {
            (functionCall.Arguments ??= new()).Append(update.Arguments);
        }

        this._functionCallRole ??= content.Role;
        this._functionCallAuthorName ??= content.AuthorName;
        this._functionCallModelId ??= content.ModelId;
    }

    private sealed class FunctionCallState
    {
        public string? CallId { get; set; }

        public string? Name { get; set; }

        public StringBuilder? Arguments { get; set; }
    }
}
