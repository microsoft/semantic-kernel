// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Linq;
using System.Text;
using System.Text.Json;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Microsoft.SemanticKernel.Diagnostics;

/// <summary>
/// Model diagnostics helper class that provides a set of methods to trace model activities with the OTel semantic conventions.
/// This class contains experimental features and may change in the future.
/// To enable these features, set one of the following switches to true:
///     `Microsoft.SemanticKernel.Experimental.GenAI.EnableOTelDiagnostics`
///     `Microsoft.SemanticKernel.Experimental.GenAI.EnableOTelDiagnosticsSensitive`
/// Or set the following environment variables to true:
///    `SEMANTICKERNEL_EXPERIMENTAL_GENAI_ENABLE_OTEL_DIAGNOSTICS`
///    `SEMANTICKERNEL_EXPERIMENTAL_GENAI_ENABLE_OTEL_DIAGNOSTICS_SENSITIVE`
/// </summary>
[System.Diagnostics.CodeAnalysis.Experimental("SKEXP0001")]
[System.Diagnostics.CodeAnalysis.ExcludeFromCodeCoverage]
internal static class ModelDiagnostics
{
    private static readonly string s_namespace = typeof(ModelDiagnostics).Namespace!;
    private static readonly ActivitySource s_activitySource = new(s_namespace);

    private const string EnableDiagnosticsSwitch = "Microsoft.SemanticKernel.Experimental.GenAI.EnableOTelDiagnostics";
    private const string EnableSensitiveEventsSwitch = "Microsoft.SemanticKernel.Experimental.GenAI.EnableOTelDiagnosticsSensitive";
    private const string EnableDiagnosticsEnvVar = "SEMANTICKERNEL_EXPERIMENTAL_GENAI_ENABLE_OTEL_DIAGNOSTICS";
    private const string EnableSensitiveEventsEnvVar = "SEMANTICKERNEL_EXPERIMENTAL_GENAI_ENABLE_OTEL_DIAGNOSTICS_SENSITIVE";

    private static readonly bool s_enableDiagnostics = AppContextSwitchHelper.GetConfigValue(EnableDiagnosticsSwitch, EnableDiagnosticsEnvVar);
    private static readonly bool s_enableSensitiveEvents = AppContextSwitchHelper.GetConfigValue(EnableSensitiveEventsSwitch, EnableSensitiveEventsEnvVar);

    /// <summary>
    /// Start a text completion activity for a given model.
    /// The activity will be tagged with the a set of attributes specified by the semantic conventions.
    /// </summary>
    internal static Activity? StartCompletionActivity<TPromptExecutionSettings>(
        Uri? endpoint,
        string modelName,
        string modelProvider,
        string prompt,
        TPromptExecutionSettings? executionSettings) where TPromptExecutionSettings : PromptExecutionSettings
    {
        if (!IsModelDiagnosticsEnabled())
        {
            return null;
        }

        const string OperationName = "text.completions";
        var activity = s_activitySource.StartActivityWithTags(
            $"{OperationName} {modelName}",
            [
                new(ModelDiagnosticsTags.Operation, OperationName),
                new(ModelDiagnosticsTags.System, modelProvider),
                new(ModelDiagnosticsTags.Model, modelName),
            ],
            ActivityKind.Client);

        if (endpoint is not null)
        {
            activity?.SetTags([
                // Skip the query string in the uri as it may contain keys
                new(ModelDiagnosticsTags.Address, endpoint.GetLeftPart(UriPartial.Path)),
                new(ModelDiagnosticsTags.Port, endpoint.Port),
            ]);
        }

        AddOptionalTags(activity, executionSettings);

        if (s_enableSensitiveEvents)
        {
            activity?.AttachSensitiveDataAsEvent(
                ModelDiagnosticsTags.UserMessage,
                [
                    new(ModelDiagnosticsTags.EventName, prompt),
                    new(ModelDiagnosticsTags.System, modelProvider),
                ]);
        }

        return activity;
    }

    /// <summary>
    /// Start a chat completion activity for a given model.
    /// The activity will be tagged with the a set of attributes specified by the semantic conventions.
    /// </summary>
    internal static Activity? StartCompletionActivity<TPromptExecutionSettings>(
        Uri? endpoint,
        string modelName,
        string modelProvider,
        ChatHistory chatHistory,
        TPromptExecutionSettings? executionSettings) where TPromptExecutionSettings : PromptExecutionSettings
    {
        if (!IsModelDiagnosticsEnabled())
        {
            return null;
        }

        const string OperationName = "chat.completions";
        var activity = s_activitySource.StartActivityWithTags(
            $"{OperationName} {modelName}",
            [
                new(ModelDiagnosticsTags.Operation, OperationName),
                new(ModelDiagnosticsTags.System, modelProvider),
                new(ModelDiagnosticsTags.Model, modelName),
            ],
            ActivityKind.Client);

        if (endpoint is not null)
        {
            activity?.SetTags([
                // Skip the query string in the uri as it may contain keys
                new(ModelDiagnosticsTags.Address, endpoint.GetLeftPart(UriPartial.Path)),
                new(ModelDiagnosticsTags.Port, endpoint.Port),
            ]);
        }

        AddOptionalTags(activity, executionSettings);

        if (s_enableSensitiveEvents)
        {
            foreach (var message in chatHistory)
            {
                var formattedContent = ToGenAIConventionsFormat(message);
                activity?.AttachSensitiveDataAsEvent(
                    ModelDiagnosticsTags.RoleToEventMap[message.Role],
                    [
                        new(ModelDiagnosticsTags.EventName, formattedContent),
                        new(ModelDiagnosticsTags.System, modelProvider),
                    ]);
            }
        }

        return activity;
    }

    /// <summary>
    /// Start an agent invocation activity and return the activity.
    /// </summary>
    internal static Activity? StartAgentInvocationActivity(
        string agentId,
        string agentName,
        string? agentDescription)
    {
        if (!IsModelDiagnosticsEnabled())
        {
            return null;
        }

        const string OperationName = "invoke_agent";

        var activity = s_activitySource.StartActivityWithTags(
            $"{OperationName} {agentName}",
            [
                new(ModelDiagnosticsTags.Operation, OperationName),
                new(ModelDiagnosticsTags.AgentId, agentId),
                new(ModelDiagnosticsTags.AgentName, agentName)
            ],
            ActivityKind.Internal);

        if (!string.IsNullOrWhiteSpace(agentDescription))
        {
            activity?.SetTag(ModelDiagnosticsTags.AgentDescription, agentDescription);
        }

        return activity;
    }

    /// <summary>
    /// Set the text completion response for a given activity.
    /// The activity will be enriched with the response attributes specified by the semantic conventions.
    /// </summary>
    internal static void SetCompletionResponse(this Activity activity, IEnumerable<TextContent> completions, int? promptTokens = null, int? completionTokens = null)
        => SetCompletionResponse(activity, completions, promptTokens, completionTokens, ToGenAIConventionsChoiceFormat);

    /// <summary>
    /// Set the chat completion response for a given activity.
    /// The activity will be enriched with the response attributes specified by the semantic conventions.
    /// </summary>
    internal static void SetCompletionResponse(this Activity activity, IEnumerable<ChatMessageContent> completions, int? promptTokens = null, int? completionTokens = null)
        => SetCompletionResponse(activity, completions, promptTokens, completionTokens, ToGenAIConventionsChoiceFormat);

    /// <summary>
    /// Notify the end of streaming for a given activity.
    /// </summary>
    internal static void EndStreaming(
        this Activity activity,
        IEnumerable<StreamingKernelContent>? contents,
        IEnumerable<FunctionCallContent>? toolCalls = null,
        int? promptTokens = null,
        int? completionTokens = null)
    {
        if (IsModelDiagnosticsEnabled())
        {
            var choices = OrganizeStreamingContent(contents);
            SetCompletionResponse(activity, choices, toolCalls, promptTokens, completionTokens);
        }
    }

    /// <summary>
    /// Set the response id for a given activity.
    /// </summary>
    /// <param name="activity">The activity to set the response id</param>
    /// <param name="responseId">The response id</param>
    /// <returns>The activity with the response id set for chaining</returns>
    internal static Activity SetResponseId(this Activity activity, string responseId) => activity.SetTag(ModelDiagnosticsTags.ResponseId, responseId);

    /// <summary>
    /// Set the input tokens usage for a given activity.
    /// </summary>
    /// <param name="activity">The activity to set the input tokens usage</param>
    /// <param name="inputTokens">The number of input tokens used</param>
    /// <returns>The activity with the input tokens usage set for chaining</returns>
    internal static Activity SetInputTokensUsage(this Activity activity, int inputTokens) => activity.SetTag(ModelDiagnosticsTags.InputTokens, inputTokens);

    /// <summary>
    /// Set the output tokens usage for a given activity.
    /// </summary>
    /// <param name="activity">The activity to set the output tokens usage</param>
    /// <param name="outputTokens">The number of output tokens used</param>
    /// <returns>The activity with the output tokens usage set for chaining</returns>
    internal static Activity SetOutputTokensUsage(this Activity activity, int outputTokens) => activity.SetTag(ModelDiagnosticsTags.OutputTokens, outputTokens);

    /// <summary>
    /// Check if model diagnostics is enabled
    /// Model diagnostics is enabled if either EnableModelDiagnostics or EnableSensitiveEvents is set to true and there are listeners.
    /// </summary>
    internal static bool IsModelDiagnosticsEnabled()
    {
        return (s_enableDiagnostics || s_enableSensitiveEvents) && s_activitySource.HasListeners();
    }

    /// <summary>
    /// Check if sensitive events are enabled.
    /// Sensitive events are enabled if EnableSensitiveEvents is set to true and there are listeners.
    /// </summary>
    internal static bool IsSensitiveEventsEnabled() => s_enableSensitiveEvents && s_activitySource.HasListeners();

    internal static bool HasListeners() => s_activitySource.HasListeners();

    #region Private
    private static void AddOptionalTags<TPromptExecutionSettings>(Activity? activity, TPromptExecutionSettings? executionSettings)
        where TPromptExecutionSettings : PromptExecutionSettings
    {
        if (activity is null || executionSettings is null)
        {
            return;
        }

        // Serialize and deserialize the execution settings to get the extension data
        var deserializedSettings = JsonSerializer.Deserialize<PromptExecutionSettings>(JsonSerializer.Serialize(executionSettings));
        if (deserializedSettings is null || deserializedSettings.ExtensionData is null)
        {
            return;
        }

        void TryAddTag(string key, string tag)
        {
            if (deserializedSettings.ExtensionData.TryGetValue(key, out var value))
            {
                activity.SetTag(tag, value);
            }
        }

        TryAddTag("max_tokens", ModelDiagnosticsTags.MaxToken);
        TryAddTag("temperature", ModelDiagnosticsTags.Temperature);
        TryAddTag("top_p", ModelDiagnosticsTags.TopP);
    }

    /// <summary>
    /// Convert a chat message to a string aligned with the OTel GenAI Semantic Conventions format
    /// </summary>
    private static string ToGenAIConventionsFormat(ChatMessageContent chatMessage, StringBuilder? sb = null)
    {
        sb ??= new StringBuilder();

        sb.Append("{\"role\": \"");
        sb.Append(chatMessage.Role);
        sb.Append("\", \"content\": ");
        sb.Append(JsonSerializer.Serialize(chatMessage.Content));
        if (chatMessage.Items.OfType<FunctionCallContent>().Any())
        {
            sb.Append(", \"tool_calls\": ");
            ToGenAIConventionsFormat(chatMessage.Items, sb);
        }
        sb.Append('}');

        return sb.ToString();
    }

    /// <summary>
    /// Helper method to convert tool calls to a string aligned with the OTel GenAI Semantic Conventions format
    /// </summary>
    private static void ToGenAIConventionsFormat(ChatMessageContentItemCollection chatMessageContentItems, StringBuilder? sb = null)
    {
        sb ??= new StringBuilder();

        sb.Append('[');
        var isFirst = true;
        foreach (var functionCall in chatMessageContentItems.OfType<FunctionCallContent>())
        {
            if (!isFirst)
            {
                // Append a comma and a newline to separate the elements after the previous one.
                // This can avoid adding an unnecessary comma after the last element.
                sb.Append(", \n");
            }

            sb.Append("{\"id\": \"");
            sb.Append(functionCall.Id);
            sb.Append("\", \"function\": {\"arguments\": ");
            sb.Append(JsonSerializer.Serialize(functionCall.Arguments));
            sb.Append(", \"name\": \"");
            sb.Append(functionCall.FunctionName);
            sb.Append("\"}, \"type\": \"function\"}");

            isFirst = false;
        }
        sb.Append(']');
    }

    /// <summary>
    /// Convert a chat model response to a string aligned with the OTel GenAI Semantic Conventions format
    /// </summary>
    private static string ToGenAIConventionsChoiceFormat(ChatMessageContent chatMessage, int index)
    {
        var sb = new StringBuilder();

        sb.Append("{\"index\": ");
        sb.Append(index);
        sb.Append(", \"message\": ");
        ToGenAIConventionsFormat(chatMessage, sb);
        sb.Append(", \"tool_calls\": ");
        ToGenAIConventionsFormat(chatMessage.Items, sb);
        if (chatMessage.Metadata?.TryGetValue("FinishReason", out var finishReason) == true)
        {
            sb.Append(", \"finish_reason\": ");
            sb.Append(JsonSerializer.Serialize(finishReason));
        }
        sb.Append('}');

        return sb.ToString();
    }

    /// <summary>
    /// Convert a text model response to a string aligned with the OTel GenAI Semantic Conventions format
    /// </summary>
    private static string ToGenAIConventionsChoiceFormat(TextContent textContent, int index)
    {
        var sb = new StringBuilder();

        sb.Append("{\"index\": ");
        sb.Append(index);
        sb.Append(", \"message\": ");
        sb.Append(JsonSerializer.Serialize(textContent.Text));
        if (textContent.Metadata?.TryGetValue("FinishReason", out var finishReason) == true)
        {
            sb.Append(", \"finish_reason\": ");
            sb.Append(JsonSerializer.Serialize(finishReason));
        }
        sb.Append('}');

        return sb.ToString();
    }

    /// <summary>
    /// Set the completion response for a given activity.
    /// The `formatCompletions` delegate won't be invoked if events are disabled.
    /// </summary>
    private static void SetCompletionResponse<T>(
        Activity activity,
        IEnumerable<T> completions,
        int? inputTokens,
        int? outputTokens,
        Func<T, int, string> formatCompletion) where T : KernelContent
    {
        if (!IsModelDiagnosticsEnabled())
        {
            return;
        }

        if (inputTokens != null)
        {
            activity.SetTag(ModelDiagnosticsTags.InputTokens, inputTokens);
        }

        if (outputTokens != null)
        {
            activity.SetTag(ModelDiagnosticsTags.OutputTokens, outputTokens);
        }

        activity.SetFinishReasons(completions);

        if (s_enableSensitiveEvents)
        {
            bool responseIdSet = false;
            int index = 0;
            foreach (var completion in completions)
            {
                if (!responseIdSet)
                {
                    activity.SetResponseId(completion);
                    responseIdSet = true;
                }

                var formattedContent = formatCompletion(completion, index++);
                activity.AttachSensitiveDataAsEvent(
                    ModelDiagnosticsTags.Choice,
                    [
                        new(ModelDiagnosticsTags.EventName, formattedContent),
                    ]);
            }
        }
        else
        {
            activity.SetResponseId(completions.FirstOrDefault());
        }
    }

    /// <summary>
    /// Set the streaming completion response for a given activity.
    /// </summary>
    private static void SetCompletionResponse(
        Activity activity,
        Dictionary<int, List<StreamingKernelContent>> choices,
        IEnumerable<FunctionCallContent>? toolCalls,
        int? promptTokens,
        int? completionTokens)
    {
        if (!IsModelDiagnosticsEnabled() || choices.Count == 0)
        {
            return;
        }

        // Assuming all metadata is in the last chunk of the choice
        switch (choices.FirstOrDefault().Value?.FirstOrDefault())
        {
            case StreamingTextContent:
                var textCompletions = choices.Select(choiceContents =>
                    {
                        var lastContent = (StreamingTextContent)choiceContents.Value.Last();
                        var text = choiceContents.Value.Select(c => c.ToString()).Aggregate((a, b) => a + b);
                        return new TextContent(text, metadata: lastContent.Metadata);
                    }).ToList();
                SetCompletionResponse(activity, textCompletions, promptTokens, completionTokens);
                break;
            case StreamingChatMessageContent:
                var chatCompletions = choices.Select(choiceContents =>
                {
                    var lastContent = (StreamingChatMessageContent)choiceContents.Value.Last();
                    var chatMessage = choiceContents.Value.Select(c => c.ToString()).Aggregate((a, b) => a + b);
                    return new ChatMessageContent(lastContent.Role ?? AuthorRole.Assistant, chatMessage, metadata: lastContent.Metadata);
                }).ToList();
                // It's currently not allowed to request multiple results per prompt while auto-invoke is enabled.
                // Therefore, we can assume that there is only one completion per prompt when tool calls are present.
                foreach (var functionCall in toolCalls ?? [])
                {
                    chatCompletions.FirstOrDefault()?.Items.Add(functionCall);
                }
                SetCompletionResponse(activity, chatCompletions, promptTokens, completionTokens);
                break;
        }
    }

    // Returns an activity for chaining
    private static Activity SetFinishReasons(this Activity activity, IEnumerable<KernelContent> completions)
    {
        var finishReasons = completions.Select(c =>
        {
            if (c.Metadata?.TryGetValue("FinishReason", out var finishReason) == true && !string.IsNullOrEmpty(finishReason as string))
            {
                return finishReason;
            }

            return "N/A";
        });

        if (finishReasons.Any())
        {
            activity.SetTag(ModelDiagnosticsTags.FinishReason, $"[{string.Join(",",
                finishReasons.Select(finishReason => $"\"{finishReason}\""))}]");
        }

        return activity;
    }

    // Returns an activity for chaining
    private static Activity SetResponseId(this Activity activity, KernelContent? completion)
    {
        if (completion?.Metadata?.TryGetValue("Id", out var id) == true && !string.IsNullOrEmpty(id as string))
        {
            activity.SetTag(ModelDiagnosticsTags.ResponseId, id);
        }

        return activity;
    }

    /// <summary>
    /// Organize streaming content by choice index
    /// </summary>
    private static Dictionary<int, List<StreamingKernelContent>> OrganizeStreamingContent(IEnumerable<StreamingKernelContent>? contents)
    {
        Dictionary<int, List<StreamingKernelContent>> choices = [];
        if (contents is null)
        {
            return choices;
        }

        foreach (var content in contents)
        {
            if (!choices.TryGetValue(content.ChoiceIndex, out var choiceContents))
            {
                choiceContents = [];
                choices[content.ChoiceIndex] = choiceContents;
            }

            choiceContents.Add(content);
        }

        return choices;
    }

    /// <summary>
    /// Tags used in model diagnostics
    /// </summary>
    private static class ModelDiagnosticsTags
    {
        // Activity tags
        public const string System = "gen_ai.system";
        public const string Operation = "gen_ai.operation.name";
        public const string Model = "gen_ai.request.model";
        public const string MaxToken = "gen_ai.request.max_tokens";
        public const string Temperature = "gen_ai.request.temperature";
        public const string TopP = "gen_ai.request.top_p";
        public const string ResponseId = "gen_ai.response.id";
        public const string ResponseModel = "gen_ai.response.model";
        public const string FinishReason = "gen_ai.response.finish_reason";
        public const string InputTokens = "gen_ai.usage.input_tokens";
        public const string OutputTokens = "gen_ai.usage.output_tokens";
        public const string Address = "server.address";
        public const string Port = "server.port";
        public const string AgentId = "gen_ai.agent.id";
        public const string AgentName = "gen_ai.agent.name";
        public const string AgentDescription = "gen_ai.agent.description";

        // Activity events
        public const string EventName = "gen_ai.event.content";
        public const string SystemMessage = "gen_ai.system.message";
        public const string UserMessage = "gen_ai.user.message";
        public const string AssistantMessage = "gen_ai.assistant.message";
        public const string ToolMessage = "gen_ai.tool.message";
        public const string Choice = "gen_ai.choice";
        public static readonly Dictionary<AuthorRole, string> RoleToEventMap = new()
            {
                { AuthorRole.System, SystemMessage },
                { AuthorRole.User, UserMessage },
                { AuthorRole.Assistant, AssistantMessage },
                { AuthorRole.Tool, ToolMessage }
            };
    }
    # endregion
}
