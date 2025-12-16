// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.Diagnostics;
using System.Linq;
using System.Runtime.CompilerServices;
using System.Text;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Anthropic.Models.Messages;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.FunctionCalling;
using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.SemanticKernel.Text;

namespace Microsoft.SemanticKernel.Connectors.Anthropic.Core;

/// <summary>
/// Partial class for chat completion functionality.
/// Implements function calling loop, streaming, and message conversion.
/// </summary>
internal partial class AnthropicClientCore
{
    #region Private Constants

    /// <summary>
    /// The separator used for Anthropic function names (plugin-function).
    /// </summary>
    private const string AnthropicFunctionNameSeparator = "-";

    #endregion

    #region Initialization

    /// <summary>
    /// Initializes the function calls processor for auto-invocation with SK filters and concurrent execution.
    /// </summary>
    partial void InitializeFunctionCallsProcessor()
    {
        this.FunctionCallsProcessor = new FunctionCallsProcessor(this.Logger);
    }

    #endregion

    #region Private Validation Methods

    /// <summary>
    /// Validates that the chat history is not empty.
    /// Anthropic API requires at least one message in the conversation.
    /// </summary>
    /// <exception cref="ArgumentException">Thrown when chatHistory is null or empty.</exception>
    private static void ValidateChatHistory(ChatHistory chatHistory)
    {
        if (chatHistory == null || chatHistory.Count == 0)
        {
            throw new ArgumentException(
                "ChatHistory must contain at least one message. Anthropic API requires a non-empty conversation.",
                nameof(chatHistory));
        }
    }

    /// <summary>
    /// Validates that the max tokens value is valid if specified.
    /// </summary>
    /// <param name="maxTokens">The max tokens value to validate.</param>
    /// <exception cref="ArgumentException">Thrown when maxTokens is less than 1.</exception>
    private static void ValidateMaxTokens(int? maxTokens)
    {
        if (maxTokens.HasValue && maxTokens < 1)
        {
            throw new ArgumentException($"MaxTokens {maxTokens} is not valid, the value must be greater than zero");
        }
    }

    #endregion

    #region Chat Completion

    /// <summary>
    /// Gets chat message contents with function calling loop support.
    /// </summary>
    /// <exception cref="ArgumentException">Thrown when chatHistory is empty.</exception>
    public async Task<IReadOnlyList<ChatMessageContent>> GetChatMessageContentsAsync(
        string targetModel,
        ChatHistory chatHistory,
        PromptExecutionSettings? executionSettings = null,
        Kernel? kernel = null,
        CancellationToken cancellationToken = default)
    {
        ValidateChatHistory(chatHistory);

        if (this.Logger!.IsEnabled(LogLevel.Trace))
        {
            this.Logger.LogTrace("ChatHistory: {ChatHistory}, Settings: {Settings}",
                JsonSerializer.Serialize(chatHistory, JsonOptionsCache.ChatHistory),
                JsonSerializer.Serialize(executionSettings));
        }

        this.LogActionDetails();

        var settings = AnthropicPromptExecutionSettings.FromExecutionSettings(executionSettings);
        ValidateMaxTokens(settings.MaxTokens);

        var activity = this.StartChatCompletionActivity(chatHistory, settings);

        try
        {
            return await this.ExecuteChatCompletionWithFunctionCallingAsync(
                targetModel, chatHistory, settings, kernel, activity, cancellationToken).ConfigureAwait(false);
        }
        catch (Exception ex)
        {
            activity?.SetStatus(ActivityStatusCode.Error, ex.Message);
            throw;
        }
        finally
        {
            activity?.Dispose();
        }
    }

    /// <summary>
    /// Executes chat completion with function calling loop using SK's FunctionCallsProcessor.
    /// </summary>
    private async Task<IReadOnlyList<ChatMessageContent>> ExecuteChatCompletionWithFunctionCallingAsync(
        string targetModel,
        ChatHistory chatHistory,
        AnthropicPromptExecutionSettings settings,
        Kernel? kernel,
        Activity? activity,
        CancellationToken cancellationToken)
    {
        // Build working copy of chat history for function calling loop
        var workingHistory = new ChatHistory(chatHistory);
        IReadOnlyList<ChatMessageContent>? lastResult = null;
        List<ToolUnion>? tools = null;

        // Text and usage aggregation across function calling iterations
        // Fix: intermediate text content before tool calls was being lost
        StringBuilder? aggregatedText = null;
        long totalInputTokens = 0;
        long totalOutputTokens = 0;

        for (int requestIndex = 0; requestIndex < FunctionCallsProcessor.MaximumAutoInvokeAttempts; requestIndex++)
        {
            // Get function calling configuration using SK's FunctionCallsProcessor
            var functionCallingConfig = this.FunctionCallsProcessor.GetConfiguration(
                settings.FunctionChoiceBehavior, workingHistory, requestIndex, kernel);

            // Build tools and tool choice from configuration
            tools = BuildToolsListFromConfiguration(functionCallingConfig);
            var toolChoice = MapFunctionChoiceToToolChoice(functionCallingConfig);

            // Build and send request
            var request = this.BuildMessageCreateParams(targetModel, workingHistory, settings, tools, toolChoice);
            var response = await RunRequestAsync(() => this.Client.Messages.Create(request, cancellationToken)).ConfigureAwait(false);

            // Convert response to ChatMessageContent
            var result = ConvertResponseToChatMessageContents(response);
            lastResult = result;

            // Record token usage for telemetry and aggregate for final response metadata
            if (response.Usage != null)
            {
                this.RecordTokenUsageMetrics((int)response.Usage.InputTokens, (int)response.Usage.OutputTokens);
                totalInputTokens += response.Usage.InputTokens;
                totalOutputTokens += response.Usage.OutputTokens;
            }

            // Check for function calls
            if (result is not { Count: > 0 })
            {
                throw new KernelException("Anthropic API returned an empty response. Expected at least one message.");
            }

            var firstChoice = result[0];

            // Aggregate text content (fix: intermediate text before tool calls was being lost)
            if (!string.IsNullOrEmpty(firstChoice.Content))
            {
                aggregatedText ??= new StringBuilder();
                if (aggregatedText.Length > 0)
                {
                    aggregatedText.Append("\n\n");
                }
                aggregatedText.Append(firstChoice.Content);
            }

            var functionCalls = FunctionCallContent.GetFunctionCalls(firstChoice).ToArray();

            // If no function calls or auto-invoke disabled, return result
            if (functionCalls.Length == 0 || functionCallingConfig?.AutoInvoke != true)
            {
                // Apply aggregated text and usage from all iterations
                if (aggregatedText is not null)
                {
                    firstChoice.Content = aggregatedText.ToString();
                }
                firstChoice.Metadata = CreateAggregatedUsageMetadata(
                    firstChoice.Metadata, totalInputTokens, totalOutputTokens);

                this.SetCompletionResponse(activity, result, totalInputTokens, totalOutputTokens);
                return result;
            }

            // Process function calls using SK's FunctionCallsProcessor
            // This handles: filters, concurrent invocation, recursion protection, termination
            var lastMessage = await this.FunctionCallsProcessor.ProcessFunctionCallsAsync(
                firstChoice,
                settings,
                workingHistory,
                requestIndex,
                (FunctionCallContent fc) => IsRequestableTool(tools, fc),
                functionCallingConfig.Options ?? new FunctionChoiceBehaviorOptions(),
                kernel,
                isStreaming: false,
                cancellationToken).ConfigureAwait(false);

            // If filter requested termination, return the last message
            if (lastMessage != null)
            {
                // Apply aggregated text and usage to the terminated message
                if (aggregatedText is not null)
                {
                    lastMessage.Content = aggregatedText.ToString();
                }
                lastMessage.Metadata = CreateAggregatedUsageMetadata(
                    lastMessage.Metadata, totalInputTokens, totalOutputTokens);

                this.SetCompletionResponse(activity, [lastMessage], totalInputTokens, totalOutputTokens);
                return [lastMessage];
            }
        }

        this.Logger!.LogWarning("Maximum function call iterations ({MaxIterations}) reached", FunctionCallsProcessor.MaximumAutoInvokeAttempts);

        // Apply aggregated text and usage to the last result
        if (lastResult is { Count: > 0 })
        {
            var finalMessage = lastResult[0];
            if (aggregatedText is not null)
            {
                finalMessage.Content = aggregatedText.ToString();
            }
            finalMessage.Metadata = CreateAggregatedUsageMetadata(
                finalMessage.Metadata, totalInputTokens, totalOutputTokens);
        }

        return lastResult ?? [];
    }

    /// <summary>
    /// Creates metadata with aggregated token usage values.
    /// </summary>
    /// <exception cref="ArgumentOutOfRangeException">Thrown when token counts are negative.</exception>
    private static ReadOnlyDictionary<string, object?> CreateAggregatedUsageMetadata(
        IReadOnlyDictionary<string, object?>? originalMetadata,
        long totalInputTokens,
        long totalOutputTokens)
    {
        // Defensive validation - API responses should never return negative token counts
        if (totalInputTokens < 0)
        {
            throw new ArgumentOutOfRangeException(nameof(totalInputTokens), totalInputTokens, "Token count cannot be negative");
        }
        if (totalOutputTokens < 0)
        {
            throw new ArgumentOutOfRangeException(nameof(totalOutputTokens), totalOutputTokens, "Token count cannot be negative");
        }

        // Copy original metadata (netstandard2.0 Dictionary ctor doesn't accept IReadOnlyDictionary)
        var metadata = new Dictionary<string, object?>();
        if (originalMetadata is not null)
        {
            foreach (var kvp in originalMetadata)
            {
                metadata[kvp.Key] = kvp.Value;
            }
        }

        metadata["InputTokens"] = totalInputTokens;
        metadata["OutputTokens"] = totalOutputTokens;
        metadata["TotalTokens"] = totalInputTokens + totalOutputTokens;

        return new ReadOnlyDictionary<string, object?>(metadata);
    }

    /// <summary>
    /// Checks if a function call is for a function that was advertised to the AI model.
    /// </summary>
    private static bool IsRequestableTool(List<ToolUnion>? tools, FunctionCallContent functionCallContent)
    {
        if (tools == null || tools.Count == 0)
        {
            return false;
        }

        var fullyQualifiedName = FunctionName.ToFullyQualifiedName(
            functionCallContent.FunctionName, functionCallContent.PluginName, AnthropicFunctionNameSeparator);

        foreach (var tool in tools)
        {
            // Tool is a ToolUnion which can be Tool (function) or other types
            // Use Ordinal comparison for consistency with SK kernel function lookup
            if (tool.Value is Tool functionTool &&
                string.Equals(functionTool.Name, fullyQualifiedName, StringComparison.Ordinal))
            {
                return true;
            }
        }

        return false;
    }

    /// <summary>
    /// Builds the tools list from FunctionChoiceBehaviorConfiguration.
    /// For FunctionChoice.None, returns null to prevent sending tools to the API
    /// (Anthropic doesn't support tool_choice=none, so we simply don't send tools).
    /// </summary>
    private static List<ToolUnion>? BuildToolsListFromConfiguration(FunctionChoiceBehaviorConfiguration? config)
    {
        if (config?.Functions == null || !config.Functions.Any())
        {
            return null;
        }

        // FunctionChoice.None means "don't call any functions" - for Anthropic, we achieve this
        // by not sending tools at all (Anthropic API doesn't support tool_choice=none)
        if (config.Choice == FunctionChoice.None)
        {
            return null;
        }

        var tools = new List<ToolUnion>();
        foreach (var function in config.Functions)
        {
            var metadata = function.Metadata;
            var fullyQualifiedName = FunctionName.ToFullyQualifiedName(
                metadata.Name, metadata.PluginName, AnthropicFunctionNameSeparator);
            var inputSchema = BuildInputSchema(metadata);

            tools.Add(new Tool
            {
                Name = fullyQualifiedName,
                Description = metadata.Description ?? string.Empty,
                InputSchema = inputSchema
            });
        }

        return tools;
    }

    /// <summary>
    /// Maps SK's FunctionChoice to Anthropic's ToolChoice.
    /// Auto → auto (model decides), Required → any (must use a tool), None → handled by not sending tools.
    /// </summary>
    private static ToolChoice? MapFunctionChoiceToToolChoice(FunctionChoiceBehaviorConfiguration? config)
    {
        if (config == null)
        {
            return null;
        }

        // Map SK FunctionChoice to Anthropic ToolChoice
        // Note: None is handled by not sending tools, so we return null here
        if (config.Choice == FunctionChoice.Required)
        {
            return new ToolChoiceAny();
        }
        else if (config.Choice == FunctionChoice.Auto)
        {
            return new ToolChoiceAuto();
        }

        // For None or unknown, return null (no tool_choice parameter)
        return null;
    }

    /// <summary>
    /// Gets streaming chat message contents with function calling support using SK's FunctionCallsProcessor.
    /// </summary>
    /// <exception cref="ArgumentException">Thrown when chatHistory is empty.</exception>
    public async IAsyncEnumerable<StreamingChatMessageContent> GetStreamingChatMessageContentsAsync(
        string targetModel,
        ChatHistory chatHistory,
        PromptExecutionSettings? executionSettings = null,
        Kernel? kernel = null,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        ValidateChatHistory(chatHistory);

        if (this.Logger!.IsEnabled(LogLevel.Trace))
        {
            this.Logger.LogTrace("ChatHistory: {ChatHistory}, Settings: {Settings}",
                JsonSerializer.Serialize(chatHistory, JsonOptionsCache.ChatHistory),
                JsonSerializer.Serialize(executionSettings));
        }

        this.LogActionDetails();

        var settings = AnthropicPromptExecutionSettings.FromExecutionSettings(executionSettings);
        ValidateMaxTokens(settings.MaxTokens);

        // Start telemetry activity for distributed tracing
        using var activity = this.StartChatCompletionActivity(chatHistory, settings);
        var streamedContents = activity is not null ? new List<StreamingChatMessageContent>() : null;
        var allFunctionCalls = activity is not null ? new List<FunctionCallContent>() : null;
        int totalInputTokens = 0;
        int totalOutputTokens = 0;

        // Build working copy of chat history for function calling loop
        var workingHistory = new ChatHistory(chatHistory);
        List<ToolUnion>? tools = null;
        var streamingEnded = false;

        // Note: C# does not allow yield return inside a try block with a catch clause (CS1626).
        // We use try-finally only here, and handle errors on specific operations with localized try-catch.
        try
        {
            for (int requestIndex = 0; requestIndex < FunctionCallsProcessor.MaximumAutoInvokeAttempts; requestIndex++)
            {
                // Get function calling configuration using SK's FunctionCallsProcessor
                var functionCallingConfig = this.FunctionCallsProcessor.GetConfiguration(
                    settings.FunctionChoiceBehavior, workingHistory, requestIndex, kernel);

                // Build tools and tool choice from configuration
                tools = BuildToolsListFromConfiguration(functionCallingConfig);
                var toolChoice = MapFunctionChoiceToToolChoice(functionCallingConfig);

                // Local state for tool call buffering (thread-safe, not instance fields)
                var toolCallBuffers = new Dictionary<long, (string id, string name, StringBuilder json)>();
                var textContent = new StringBuilder();
                var hasFunctionCalls = false;
                var functionCallContents = new List<FunctionCallContent>();
                int inputTokens = 0; // Captured from message_start event

                // Build and send streaming request - the CreateStreaming call itself doesn't throw,
                // errors occur during enumeration
                var request = this.BuildMessageCreateParams(targetModel, workingHistory, settings, tools, toolChoice);
                var stream = this.Client.Messages.CreateStreaming(request, cancellationToken);

                // Process the stream using manual enumeration to handle errors properly
                var streamEnumerator = stream.ConfigureAwait(false).GetAsyncEnumerator();
                try
                {
                    while (true)
                    {
                        // Handle errors during stream iteration
                        bool hasNext;
                        try
                        {
                            hasNext = await streamEnumerator.MoveNextAsync();
                        }
                        catch (Exception ex) when (activity is not null)
                        {
                            activity.SetStatus(ActivityStatusCode.Error, ex.Message);
                            throw;
                        }

                        if (!hasNext)
                        {
                            break;
                        }

                        var evt = streamEnumerator.Current;

                        // Handle different event types using TryPick pattern
                        // Capture input tokens from message_start event (sent at beginning of stream)
                        if (evt.TryPickStart(out var messageStart))
                        {
                            if (messageStart.Message?.Usage != null)
                            {
                                inputTokens = (int)messageStart.Message.Usage.InputTokens;
                            }
                        }
                        else if (evt.TryPickContentBlockStart(out var startEvent))
                        {
                            if (startEvent.ContentBlock.TryPickToolUse(out var toolUse))
                            {
                                toolCallBuffers[startEvent.Index] = (toolUse.ID, toolUse.Name, new StringBuilder());
                                hasFunctionCalls = true;
                            }
                        }
                        else if (evt.TryPickContentBlockDelta(out var deltaEvent))
                        {
                            if (deltaEvent.Delta.TryPickText(out var textDelta))
                            {
                                textContent.Append(textDelta.Text);
                                var chunk = new StreamingChatMessageContent(AuthorRole.Assistant, textDelta.Text)
                                {
                                    ModelId = targetModel
                                };
                                streamedContents?.Add(chunk);
                                yield return chunk;
                            }
                            else if (deltaEvent.Delta.TryPickInputJSON(out var jsonDelta))
                            {
                                if (toolCallBuffers.TryGetValue(deltaEvent.Index, out var buffer))
                                {
                                    buffer.json.Append(jsonDelta.PartialJSON);
                                }
                            }
                        }
                        else if (evt.TryPickContentBlockStop(out var stopEvent))
                        {
                            // Emit StreamingFunctionCallUpdateContent when tool call block completes
                            if (toolCallBuffers.TryGetValue(stopEvent.Index, out var buffer))
                            {
                                var argumentsDict = ParseToolArguments(buffer.json.ToString());
                                var kernelArgs = ConvertToKernelArguments(argumentsDict);

                                // Parse the fully-qualified name to extract plugin and function names
                                var parsedName = FunctionName.Parse(buffer.name, AnthropicFunctionNameSeparator);
                                var functionCallContent = new FunctionCallContent(
                                    functionName: parsedName.Name,
                                    pluginName: parsedName.PluginName,
                                    id: buffer.id,
                                    arguments: kernelArgs);
                                functionCallContents.Add(functionCallContent);
                                allFunctionCalls?.Add(functionCallContent);

                                // Create streaming content with function call update
                                var streamingContent = new StreamingChatMessageContent(AuthorRole.Assistant, content: null)
                                {
                                    ModelId = targetModel
                                };
                                streamingContent.Items.Add(new StreamingFunctionCallUpdateContent(
                                    callId: buffer.id,
                                    name: buffer.name,
                                    arguments: buffer.json.ToString()));
                                streamedContents?.Add(streamingContent);
                                yield return streamingContent;
                            }
                        }
                        else if (evt.TryPickDelta(out var messageDelta))
                        {
                            // Record token usage from final message delta (output tokens)
                            // Combined with input tokens captured from message_start event
                            if (messageDelta.Usage != null)
                            {
                                var outputTokens = (int)messageDelta.Usage.OutputTokens;
                                totalInputTokens += inputTokens;
                                totalOutputTokens += outputTokens;
                                this.RecordTokenUsageMetrics(inputTokens, outputTokens);
                            }
                        }
                    }
                }
                finally
                {
                    await streamEnumerator.DisposeAsync();
                }

                // If no function calls or auto-invoke disabled, we're done
                if (!hasFunctionCalls || functionCallingConfig?.AutoInvoke != true)
                {
                    // End streaming activity with telemetry data
                    activity?.EndStreaming(streamedContents, allFunctionCalls, totalInputTokens, totalOutputTokens);
                    streamingEnded = true;
                    yield break;
                }

                // Build assistant message with function calls
                var chatMessageContent = new ChatMessageContent(
                    AuthorRole.Assistant,
                    textContent.Length > 0 ? textContent.ToString() : string.Empty,
                    targetModel);
                foreach (var fc in functionCallContents)
                {
                    chatMessageContent.Items.Add(fc);
                }

                // Process function calls using SK's FunctionCallsProcessor
                // This handles: filters, concurrent invocation, recursion protection, termination
                ChatMessageContent? lastMessage;
                try
                {
                    lastMessage = await this.FunctionCallsProcessor.ProcessFunctionCallsAsync(
                        chatMessageContent,
                        settings,
                        workingHistory,
                        requestIndex,
                        (FunctionCallContent fc) => IsRequestableTool(tools, fc),
                        functionCallingConfig.Options ?? new FunctionChoiceBehaviorOptions(),
                        kernel,
                        isStreaming: true,
                        cancellationToken).ConfigureAwait(false);
                }
                catch (Exception ex) when (activity is not null)
                {
                    activity.SetStatus(ActivityStatusCode.Error, ex.Message);
                    throw;
                }

                // If filter requested termination, yield the last message and exit
                if (lastMessage != null)
                {
                    var terminationChunk = new StreamingChatMessageContent(lastMessage.Role, lastMessage.Content)
                    {
                        ModelId = targetModel
                    };
                    streamedContents?.Add(terminationChunk);
                    // End streaming activity with telemetry data
                    activity?.EndStreaming(streamedContents, allFunctionCalls, totalInputTokens, totalOutputTokens);
                    streamingEnded = true;
                    yield return terminationChunk;
                    yield break;
                }
            }

            // End streaming activity for max iterations case
            activity?.EndStreaming(streamedContents, allFunctionCalls, totalInputTokens, totalOutputTokens);
            streamingEnded = true;
            this.Logger!.LogWarning("Maximum function call iterations ({MaxIterations}) reached in streaming", FunctionCallsProcessor.MaximumAutoInvokeAttempts);
        }
        finally
        {
            if (!streamingEnded)
            {
                activity?.EndStreaming(streamedContents, allFunctionCalls, totalInputTokens, totalOutputTokens);
            }
        }
    }

    #endregion

    #region Text Generation

    /// <summary>
    /// Gets chat message contents as text contents.
    /// </summary>
    public async Task<IReadOnlyList<TextContent>> GetChatAsTextContentsAsync(
        string targetModel,
        string prompt,
        PromptExecutionSettings? executionSettings = null,
        Kernel? kernel = null,
        CancellationToken cancellationToken = default)
    {
        var chatHistory = new ChatHistory();
        chatHistory.AddUserMessage(prompt);

        var results = await this.GetChatMessageContentsAsync(targetModel, chatHistory, executionSettings, kernel, cancellationToken).ConfigureAwait(false);

        return results
            .SelectMany(m => m.Items.OfType<TextContent>())
            .ToList();
    }

    /// <summary>
    /// Gets streaming chat message contents as streaming text contents.
    /// </summary>
    public async IAsyncEnumerable<StreamingTextContent> GetChatAsTextStreamingContentsAsync(
        string targetModel,
        string prompt,
        PromptExecutionSettings? executionSettings = null,
        Kernel? kernel = null,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        var chatHistory = new ChatHistory();
        chatHistory.AddUserMessage(prompt);

        await foreach (var chunk in this.GetStreamingChatMessageContentsAsync(targetModel, chatHistory, executionSettings, kernel, cancellationToken).ConfigureAwait(false))
        {
            if (!string.IsNullOrEmpty(chunk.Content))
            {
                yield return new StreamingTextContent(chunk.Content)
                {
                    ModelId = chunk.ModelId
                };
            }
        }
    }

    #endregion

    #region Private Helper Methods

    /// <summary>
    /// Builds MessageCreateParams from chat history and settings with pre-built tools and tool choice.
    /// </summary>
    /// <param name="targetModel">The model identifier.</param>
    /// <param name="chatHistory">The chat history.</param>
    /// <param name="settings">The execution settings.</param>
    /// <param name="tools">The tools list.</param>
    /// <param name="toolChoice">The tool choice.</param>
    /// <returns>The message create parameters.</returns>
    private MessageCreateParams BuildMessageCreateParams(
        string targetModel,
        ChatHistory chatHistory,
        AnthropicPromptExecutionSettings settings,
        List<ToolUnion>? tools,
        ToolChoice? toolChoice)
    {
        // Extract system messages and concatenate with \n\n
        // Anthropic API only supports a single system message, so we concatenate multiple ones.
        //
        // Note: This differs from the Python SK Anthropic connector which only uses the first
        // system message. The .NET implementation concatenates all system messages to preserve
        // all system instructions, which is more aligned with user expectations when multiple
        // system messages are added to the chat history.
        var systemMessages = chatHistory
            .Where(m => m.Role == AuthorRole.System)
            .Select(m => m.Content ?? string.Empty)
            .Where(c => !string.IsNullOrWhiteSpace(c))
            .ToList();

        if (systemMessages.Count > 1)
        {
            this.Logger!.LogWarning(
                "Multiple system messages detected ({Count}). Anthropic API only supports a single system message; " +
                "concatenating all system messages with paragraph separators.",
                systemMessages.Count);
        }

        var systemPrompt = string.Join("\n\n", systemMessages);

        // Convert non-system messages to Anthropic format with tool message grouping.
        // Anthropic requires that parallel tool result messages are grouped together in a single
        // user message. This is consistent with the Python SK Anthropic connector behavior.
        var messages = ConvertChatHistoryToAnthropicMessages(chatHistory);

        // Anthropic API does not allow both temperature and top_p at the same time
        // If both are set, prefer temperature (more commonly used)
        double? temperature = settings.Temperature;
        double? topP = settings.TopP;
        if (temperature.HasValue && topP.HasValue)
        {
            this.Logger!.LogDebug("Both Temperature and TopP specified; using only Temperature per Anthropic API constraints");
            topP = null;
        }

        // Build request with all properties in object initializer (init-only properties)
        var request = new MessageCreateParams
        {
            Model = targetModel,
            MaxTokens = settings.MaxTokens ?? DefaultMaxTokens,
            Messages = messages,
            System = !string.IsNullOrEmpty(systemPrompt) ? new SystemModel(systemPrompt) : null,
            Temperature = temperature,
            TopP = topP,
            TopK = settings.TopK,
            StopSequences = settings.StopSequences?.Count > 0 ? settings.StopSequences.ToList() : null,
            Tools = tools?.Count > 0 ? tools : null,
            ToolChoice = tools?.Count > 0 ? toolChoice : null  // Only set ToolChoice if tools are present
        };

        return request;
    }

    // Note: Message converters have been moved to AnthropicClientCore.Converters.cs for better organization

    #endregion
}
