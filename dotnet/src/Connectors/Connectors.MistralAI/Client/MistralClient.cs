// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Net.Http;
using System.Net.Http.Headers;
using System.Runtime.CompilerServices;
using System.Text;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Http;

namespace Microsoft.SemanticKernel.Connectors.MistralAI.Client;

/// <summary>
/// The Mistral client.
/// </summary>
internal sealed class MistralClient
{
    internal MistralClient(
        string modelId,
        HttpClient httpClient,
        string apiKey,
        Uri? endpoint = null,
        ILogger? logger = null)
    {
        Verify.NotNullOrWhiteSpace(modelId);
        Verify.NotNullOrWhiteSpace(apiKey);
        Verify.NotNull(httpClient);

        this._endpoint = endpoint;
        this._modelId = modelId;
        this._apiKey = apiKey;
        this._httpClient = httpClient;
        this._logger = logger ?? NullLogger.Instance;
    }

    internal async Task<IReadOnlyList<ChatMessageContent>> GetChatMessageContentsAsync(ChatHistory chatHistory, CancellationToken cancellationToken, PromptExecutionSettings? executionSettings = null, Kernel? kernel = null)
    {
        this.ValidateChatHistory(chatHistory);

        string modelId = executionSettings?.ModelId ?? this._modelId;
        var mistralExecutionSettings = MistralAIPromptExecutionSettings.FromExecutionSettings(executionSettings);
        var chatRequest = this.CreateChatCompletionRequest(modelId, stream: false, chatHistory, mistralExecutionSettings, kernel);
        var endpoint = this.GetEndpoint(mistralExecutionSettings, path: "chat/completions");
        bool autoInvoke = kernel is not null && mistralExecutionSettings.ToolCallBehavior?.MaximumAutoInvokeAttempts > 0 && s_inflightAutoInvokes.Value < MaxInflightAutoInvokes;

        for (int iteration = 1; ; iteration++)
        {
            using var httpRequestMessage = this.CreatePost(chatRequest, endpoint, this._apiKey, stream: false);
            var responseData = await this.SendRequestAsync<ChatCompletionResponse>(httpRequestMessage, cancellationToken).ConfigureAwait(false);
            if (responseData is null || responseData.Choices is null || responseData.Choices.Count == 0)
            {
                throw new KernelException("Chat completions not found");
            }

            // If we don't want to attempt to invoke any functions, just return the result.
            // Or if we are auto-invoking but we somehow end up with other than 1 choice even though only 1 was requested, similarly bail.
            if (!autoInvoke || responseData.Choices.Count != 1)
            {
                return ToChatMessageContent(modelId, responseData);
            }

            // Get our single result and extract the function call information. If this isn't a function call, or if it is
            // but we're unable to find the function or extract the relevant information, just return the single result.
            // Note that we don't check the FinishReason and instead check whether there are any tool calls, as the service
            // may return a FinishReason of "stop" even if there are tool calls to be made, in particular if a required tool
            // is specified.
            MistralChatChoice chatChoice = responseData.Choices[0];
            if (!chatChoice.IsToolCall)
            {
                return ToChatMessageContent(modelId, responseData);
            }

            if (this._logger.IsEnabled(LogLevel.Debug))
            {
                this._logger.LogDebug("Tool requests: {Requests}", chatChoice.ToolCallCount);
            }
            if (this._logger.IsEnabled(LogLevel.Trace))
            {
                this._logger.LogTrace("Function call requests: {Requests}", string.Join(", ", chatChoice.ToolCalls.Select(tc => $"{tc.Function?.Name}({tc.Function?.Parameters})")));
            }

            Debug.Assert(kernel is not null);

            // Add the original assistant message to the chatOptions; this is required for the service
            // to understand the tool call responses. Also add the result message to the caller's chat
            // history: if they don't want it, they can remove it, but this makes the data available,
            // including metadata like usage.
            chatRequest.AddMessage(chatChoice.Message!);
            chatHistory.Add(ToChatMessageContent(modelId, responseData, chatChoice));

            // We must send back a response for every tool call, regardless of whether we successfully executed it or not.
            // If we successfully execute it, we'll add the result. If we don't, we'll add an error.
            for (int i = 0; i < chatChoice.ToolCallCount; i++)
            {
                var toolCall = chatChoice.ToolCalls![i];

                // We currently only know about function tool calls. If it's anything else, we'll respond with an error.
                if (toolCall.Function is null)
                {
                    this.AddResponseMessage(chatRequest, chatHistory, toolCall, result: null, "Error: Tool call was not a function call.");
                    continue;
                }

                // Make sure the requested function is one we requested. If we're permitting any kernel function to be invoked,
                // then we don't need to check this, as it'll be handled when we look up the function in the kernel to be able
                // to invoke it. If we're permitting only a specific list of functions, though, then we need to explicitly check.
                if (mistralExecutionSettings.ToolCallBehavior?.AllowAnyRequestedKernelFunction is not true &&
                    !IsRequestableTool(chatRequest, toolCall.Function!))
                {
                    this.AddResponseMessage(chatRequest, chatHistory, toolCall, result: null, "Error: Function call chatRequest for a function that wasn't defined.");
                    continue;
                }

                // Find the function in the kernel and populate the arguments.
                if (!kernel!.Plugins.TryGetFunctionAndArguments(kernel, toolCall.Function, out KernelFunction? function, out KernelArguments? functionArgs))
                {
                    this.AddResponseMessage(chatRequest, chatHistory, toolCall, result: null, "Error: Requested function could not be found.");
                    continue;
                }

                // Now, invoke the function, and add the resulting tool call message to the chat options.
                s_inflightAutoInvokes.Value++;
                object? functionResult;
                try
                {
                    // Note that we explicitly do not use executionSettings here; those pertain to the all-up operation and not necessarily to any
                    // further calls made as part of this function invocation. In particular, we must not use function calling settings naively here,
                    // as the called function could in turn telling the model about itself as a possible candidate for invocation.
                    functionResult = (await function.InvokeAsync(kernel, functionArgs, cancellationToken: cancellationToken).ConfigureAwait(false)).GetValue<object>() ?? string.Empty;
                }
#pragma warning disable CA1031 // Do not catch general exception types
                catch (Exception e)
#pragma warning restore CA1031
                {
                    this.AddResponseMessage(chatRequest, chatHistory, toolCall, result: null, $"Error: Exception while invoking function. {e.Message}");
                    continue;
                }
                finally
                {
                    s_inflightAutoInvokes.Value--;
                }

                var stringResult = ProcessFunctionResult(functionResult, mistralExecutionSettings.ToolCallBehavior);

                this.AddResponseMessage(chatRequest, chatHistory, toolCall, result: stringResult, errorMessage: null);
            }

            // Update tool use information for the next go-around based on having completed another iteration.
            Debug.Assert(mistralExecutionSettings.ToolCallBehavior is not null);

            // Set the tool choice to none. If we end up wanting to use tools, we'll reset it to the desired value.
            chatRequest.ToolChoice = "none";
            chatRequest.Tools?.Clear();

            if (iteration >= mistralExecutionSettings.ToolCallBehavior!.MaximumUseAttempts)
            {
                // Don't add any tools as we've reached the maximum attempts limit.
                if (this._logger.IsEnabled(LogLevel.Debug))
                {
                    this._logger.LogDebug("Maximum use ({MaximumUse}) reached; removing the tool.", mistralExecutionSettings.ToolCallBehavior!.MaximumUseAttempts);
                }
            }
            else
            {
                // Regenerate the tool list as necessary. The invocation of the function(s) could have augmented
                // what functions are available in the kernel.
                mistralExecutionSettings.ToolCallBehavior.ConfigureRequest(kernel, chatRequest);
            }

            // Disable auto invocation if we've exceeded the allowed limit.
            if (iteration >= mistralExecutionSettings.ToolCallBehavior!.MaximumAutoInvokeAttempts)
            {
                autoInvoke = false;
                if (this._logger.IsEnabled(LogLevel.Debug))
                {
                    this._logger.LogDebug("Maximum auto-invoke ({MaximumAutoInvoke}) reached.", mistralExecutionSettings.ToolCallBehavior!.MaximumAutoInvokeAttempts);
                }
            }
        }
    }

    internal async IAsyncEnumerable<StreamingChatMessageContent> GetStreamingChatMessageContentsAsync(ChatHistory chatHistory, [EnumeratorCancellation] CancellationToken cancellationToken, PromptExecutionSettings? executionSettings = null, Kernel? kernel = null)
    {
        this.ValidateChatHistory(chatHistory);

        string modelId = executionSettings?.ModelId ?? this._modelId;
        var mistralExecutionSettings = MistralAIPromptExecutionSettings.FromExecutionSettings(executionSettings);
        var request = this.CreateChatCompletionRequest(modelId, stream: true, chatHistory, mistralExecutionSettings);
        var endpoint = this.GetEndpoint(mistralExecutionSettings, path: "chat/completions");

        using var httpRequestMessage = this.CreatePost(request, endpoint, this._apiKey, stream: true);

        using var response = await this.SendStreamingRequestAsync(httpRequestMessage, cancellationToken).ConfigureAwait(false);

        using var responseStream = await response.Content.ReadAsStreamAndTranslateExceptionAsync().ConfigureAwait(false);
        using var reader = new StreamReader(responseStream);
        string line;
        string? rawChunk = null;
        AuthorRole? currentRole = null;
        while ((line = await reader.ReadLineAsync().ConfigureAwait(false)) != null)
        {
            if (!string.IsNullOrEmpty(line))
            {
                rawChunk = line.Substring(SseDataLength).Trim();
            }
            else if (rawChunk is not null)
            {
                if (rawChunk is "[DONE]")
                {
                    continue;
                }
                var chunk = JsonSerializer.Deserialize<MistralChatCompletionChunk>(rawChunk);
                rawChunk = null;

                if (chunk is null)
                {
                    throw new KernelException("Unexpected chunk response from model")
                    {
                        Data = { { "ResponseData", rawChunk } },
                    };
                }

                for (int i = 0; i < chunk.GetChoiceCount(); i++)
                {
                    currentRole ??= chunk.GetRole(i);

                    yield return new(role: currentRole,
                        content: chunk.GetContent(i),
                        choiceIndex: i,
                        modelId: modelId,
                        encoding: chunk.GetEncoding(),
                        innerContent: chunk,
                        metadata: chunk.GetMetadata());
                }
            }
        }
    }

    internal async Task<IList<ReadOnlyMemory<float>>> GenerateEmbeddingsAsync(IList<string> data, CancellationToken cancellationToken, PromptExecutionSettings? executionSettings = null, Kernel? kernel = null)
    {
        var request = new TextEmbeddingRequest(this._modelId, data);
        var mistralExecutionSettings = MistralAIPromptExecutionSettings.FromExecutionSettings(executionSettings);
        var endpoint = this.GetEndpoint(mistralExecutionSettings, path: "embeddings");
        using var httpRequestMessage = this.CreatePost(request, endpoint, this._apiKey, false);

        var response = await this.SendRequestAsync<TextEmbeddingResponse>(httpRequestMessage, cancellationToken).ConfigureAwait(false);

        return response.Data.Select(item => new ReadOnlyMemory<float>(item.Embedding.ToArray())).ToList();
    }

    #region private
    private readonly string _modelId;
    private readonly string _apiKey;
    private readonly Uri? _endpoint;
    private readonly HttpClient _httpClient;
    private readonly ILogger _logger;

    private const int SseDataLength = 5;

    /// <summary>
    /// The maximum number of auto-invokes that can be in-flight at any given time as part of the current
    /// asynchronous chain of execution.
    /// </summary>
    /// <remarks>
    /// This is a fail-safe mechanism. If someone accidentally manages to set up execution settings in such a way that
    /// auto-invocation is invoked recursively, and in particular where a prompt function is able to auto-invoke itself,
    /// we could end up in an infinite loop. This const is a backstop against that happening. We should never come close
    /// to this limit, but if we do, auto-invoke will be disabled for the current flow in order to prevent runaway execution.
    /// With the current setup, the way this could possibly happen is if a prompt function is configured with built-in
    /// execution settings that opt-in to auto-invocation of everything in the kernel, in which case the invocation of that
    /// prompt function could advertize itself as a candidate for auto-invocation. We don't want to outright block that,
    /// if that's something a developer has asked to do (e.g. it might be invoked with different arguments than its parent
    /// was invoked with), but we do want to limit it. This limit is arbitrary and can be tweaked in the future and/or made
    /// configurable should need arise.
    /// </remarks>
    private const int MaxInflightAutoInvokes = 5;

    /// <summary>Tracking <see cref="AsyncLocal{Int32}"/> for <see cref="MaxInflightAutoInvokes"/>.</summary>
    private static readonly AsyncLocal<int> s_inflightAutoInvokes = new();

    /// <summary>
    /// Messages are required and the first prompt role should be user or system.
    /// </summary>
    private void ValidateChatHistory(ChatHistory chatHistory)
    {
        Verify.NotNull(chatHistory);

        if (chatHistory.Count == 0)
        {
            throw new ArgumentException("Chat history must contain at least one message", nameof(chatHistory));
        }
        var firstRole = chatHistory[0].Role.ToString();
        if (firstRole is not "system" && firstRole is not "user")
        {
            throw new ArgumentException("First message in chat history should have system or user role", nameof(chatHistory));
        }
    }

    private ChatCompletionRequest CreateChatCompletionRequest(string modelId, bool stream, ChatHistory chatHistory, MistralAIPromptExecutionSettings? executionSettings, Kernel? kernel = null)
    {
        var request = new ChatCompletionRequest(modelId)
        {
            Stream = stream,
            Messages = chatHistory.Select(chatMessage => new MistralChatMessage(chatMessage.Role.ToString(), chatMessage.Content!)).ToList(),
        };

        if (executionSettings is not null)
        {
            request.Temperature = executionSettings.Temperature;
            request.TopP = executionSettings.TopP;
            request.MaxTokens = executionSettings.MaxTokens;
            request.SafePrompt = executionSettings.SafePrompt;
            request.RandomSeed = executionSettings.RandomSeed;

            if (executionSettings.ToolCallBehavior is not null)
            {
                executionSettings.ToolCallBehavior.ConfigureRequest(kernel, request);
            }
        }

        return request;
    }

    private HttpRequestMessage CreatePost(object requestData, Uri endpoint, string apiKey, bool stream)
    {
        var httpRequestMessage = HttpRequest.CreatePostRequest(endpoint, requestData);
        this.SetRequestHeaders(httpRequestMessage, apiKey, stream);

        return httpRequestMessage;
    }

    private void SetRequestHeaders(HttpRequestMessage request, string apiKey, bool stream)
    {
        request.Headers.Add("User-Agent", HttpHeaderConstant.Values.UserAgent);
        request.Headers.Add(HttpHeaderConstant.Names.SemanticKernelVersion, HttpHeaderConstant.Values.GetAssemblyVersion(this.GetType()));
        request.Headers.Add("Accept", stream ? "text/event-stream" : "application/json");
        request.Headers.Add("Authorization", $"Bearer {this._apiKey}");
        request.Content!.Headers.ContentType = new MediaTypeHeaderValue("application/json");
    }

    private async Task<T> SendRequestAsync<T>(HttpRequestMessage httpRequestMessage, CancellationToken cancellationToken)
    {
        using var response = await this._httpClient.SendWithSuccessCheckAsync(httpRequestMessage, cancellationToken).ConfigureAwait(false);

        var body = await response.Content.ReadAsStringWithExceptionMappingAsync().ConfigureAwait(false);

        return DeserializeResponse<T>(body);
    }

    private async Task<HttpResponseMessage> SendStreamingRequestAsync(HttpRequestMessage httpRequestMessage, CancellationToken cancellationToken)
    {
        return await this._httpClient.SendWithSuccessCheckAsync(httpRequestMessage, HttpCompletionOption.ResponseHeadersRead, cancellationToken).ConfigureAwait(false);
    }

    private Uri GetEndpoint(MistralAIPromptExecutionSettings executionSettings, string path)
    {
        var endpoint = this._endpoint ?? new Uri($"https://api.mistral.ai/{executionSettings.ApiVersion}");
        var separator = endpoint.AbsolutePath.EndsWith("/", StringComparison.InvariantCulture) ? string.Empty : "/";
        return new Uri($"{endpoint}{separator}{path}");
    }

    /// <summary>Checks if a tool call is for a function that was defined.</summary>
    private static bool IsRequestableTool(ChatCompletionRequest request, MistralFunction func)
    {
        var tools = request.Tools;
        for (int i = 0; i < tools?.Count; i++)
        {
            if (string.Equals(tools[i].Function.Name, func.Name, StringComparison.OrdinalIgnoreCase))
            {
                return true;
            }
        }

        return false;
    }

    private static T DeserializeResponse<T>(string body)
    {
        try
        {
            T? deserializedResponse = JsonSerializer.Deserialize<T>(body);
            if (deserializedResponse is null)
            {
                throw new JsonException("Response is null");
            }

            return deserializedResponse;
        }
        catch (JsonException exc)
        {
            throw new KernelException("Unexpected response from model", exc)
            {
                Data = { { "ResponseData", body } },
            };
        }
    }

    private static List<ChatMessageContent> ToChatMessageContent(string modelId, ChatCompletionResponse response)
    {
        return response.Choices.Select(chatChoice => ToChatMessageContent(modelId, response, chatChoice)).ToList();
    }

    private void AddResponseMessage(ChatCompletionRequest chatRequest, ChatHistory chat, MistralToolCall toolCall, string? result, string? errorMessage)
    {
        // Log any error
        if (errorMessage is not null && this._logger.IsEnabled(LogLevel.Debug))
        {
            Debug.Assert(result is null);
            this._logger.LogDebug("Failed to handle tool request ({ToolId}). {Error}", toolCall.Function?.Name, errorMessage);
        }

        // Add the tool response message to both the chat options and to the chat history.
        result ??= errorMessage ?? string.Empty;
        chatRequest.AddMessage(new MistralChatMessage(AuthorRole.Tool.ToString(), result));
        chat.AddMessage(AuthorRole.Tool, result, metadata: new Dictionary<string, object?> { { nameof(MistralToolCall.Function), toolCall.Function } });
    }

    private static ChatMessageContent ToChatMessageContent(string modelId, ChatCompletionResponse response, MistralChatChoice chatChoice)
    {
        return new ChatMessageContent(new AuthorRole(chatChoice.Message!.Role!), chatChoice.Message!.Content, modelId, chatChoice, Encoding.UTF8, GetChatChoiceMetadata(response, chatChoice));
    }

    private static Dictionary<string, object?> GetChatChoiceMetadata(ChatCompletionResponse completionResponse, MistralChatChoice chatChoice)
    {
        return new Dictionary<string, object?>(6)
        {
            { nameof(completionResponse.Id), completionResponse.Id },
            { nameof(completionResponse.Object), completionResponse.Object },
            { nameof(completionResponse.Model), completionResponse.Model },
            { nameof(completionResponse.Usage), completionResponse.Usage },
            { nameof(completionResponse.Created), completionResponse.Created },
            { nameof(chatChoice.Index), chatChoice.Index },
            { nameof(chatChoice.FinishReason), chatChoice.FinishReason },
        };
    }

    /// <summary>
    /// Processes the function result.
    /// </summary>
    /// <param name="functionResult">The result of the function call.</param>
    /// <param name="toolCallBehavior">The ToolCallBehavior object containing optional settings like JsonSerializerOptions.TypeInfoResolver.</param>
    /// <returns>A string representation of the function result.</returns>
    private static string? ProcessFunctionResult(object functionResult, MistralAIToolCallBehavior? toolCallBehavior)
    {
        if (functionResult is string stringResult)
        {
            return stringResult;
        }

        // This is an optimization to use ChatMessageContent content directly  
        // without unnecessary serialization of the whole message content class.  
        if (functionResult is ChatMessageContent chatMessageContent)
        {
            return chatMessageContent.ToString();
        }

        // For polymorphic serialization of unknown in advance child classes of the KernelContent class,  
        // a corresponding JsonTypeInfoResolver should be provided via the JsonSerializerOptions.TypeInfoResolver property.  
        // For more details about the polymorphic serialization, see the article at:  
        // https://learn.microsoft.com/en-us/dotnet/standard/serialization/system-text-json/polymorphism?pivots=dotnet-8-0
        return JsonSerializer.Serialize(functionResult, toolCallBehavior?.ToolCallResultSerializerOptions);
    }

    #endregion
}
