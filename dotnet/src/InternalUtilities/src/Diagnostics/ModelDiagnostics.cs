using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Diagnostics.CodeAnalysis;
using System.Linq;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Diagnostics;

namespace Microsoft.SemanticKernel;

[ExcludeFromCodeCoverage]
internal static class ModelDiagnostics
{
    private static readonly string s_namespace = typeof(ModelDiagnostics).Namespace;
    private static readonly ActivitySource s_activitySource = new(s_namespace);

    private const string EnableModelDiagnosticsSettingName = "Microsoft.SemanticKernel.Experimental.EnableModelDiagnostics";
    private const string EnableSensitiveEventsSettingName = "Microsoft.SemanticKernel.Experimental.EnableModelDiagnosticsWithSensitiveData";

    private static readonly bool s_enableModelDiagnostics = AppContextSwitchHelper.GetConfigValue(EnableModelDiagnosticsSettingName);
    private static readonly bool s_enableSensitiveEvents = AppContextSwitchHelper.GetConfigValue(EnableSensitiveEventsSettingName);

    /// <summary>
    /// Start a text completion activity for a given model.
    /// The activity will be tagged with the a set of attributes specified by the semantic conventions.
    /// </summary>
    public static Activity? StartCompletionActivity(string modelName, string modelProvider, string prompt, PromptExecutionSettings? executionSettings)
        => StartCompletionActivity(modelName, modelProvider, prompt, executionSettings, prompt => prompt);

    /// <summary>
    /// Start a chat completion activity for a given model.
    /// The activity will be tagged with the a set of attributes specified by the semantic conventions.
    /// </summary>
    public static Activity? StartCompletionActivity(string modelName, string modelProvider, ChatHistory chatHistory, PromptExecutionSettings? executionSettings)
        => StartCompletionActivity(modelName, modelProvider, chatHistory, executionSettings, chatHistory => ToOpenAIFormat(chatHistory.AsEnumerable()));

    /// <summary>
    /// Set the text completion response for a given activity.
    /// The activity will be enriched with the response attributes specified by the semantic conventions.
    /// </summary>
    public static void SetCompletionResponse(this Activity activity, IEnumerable<TextContent> completions, int promptTokens, int completionTokens)
        => SetCompletionResponse(activity, completions, promptTokens, completionTokens, completions => $"[{string.Join(", ", completions)}]");

    /// <summary>
    /// Set the chat completion response for a given activity.
    /// The activity will be enriched with the response attributes specified by the semantic conventions.
    /// </summary>
    public static void SetCompletionResponse(this Activity activity, IEnumerable<ChatMessageContent> completions, int promptTokens, int completionTokens)
        => SetCompletionResponse(activity, completions, promptTokens, completionTokens, ToOpenAIFormat);

    # region Private
    /// <summary>
    /// Check if model diagnostics is enabled
    /// Model diagnostics is enabled if either EnableModelDiagnostics or EnableSensitiveEvents is set to true.
    /// </summary>
    private static bool IsModelDiagnosticsEnabled()
    {
        return s_enableModelDiagnostics || s_enableSensitiveEvents;
    }

    private static void AddOptionalTags(Activity? activity, PromptExecutionSettings? executionSettings)
    {
        if (activity is null || executionSettings?.ExtensionData is null)
        {
            return;
        }

        void TryAddTag(string key, string tag)
        {
            if (executionSettings.ExtensionData.TryGetValue(key, out var value))
            {
                activity.AddTag(tag, value);
            }
        }

        TryAddTag("max_tokens", ModelDiagnosticsTags.MaxToken);
        TryAddTag("temperature", ModelDiagnosticsTags.Temperature);
        TryAddTag("top_p", ModelDiagnosticsTags.TopP);
    }

    /// <summary>
    /// Convert chat history to a string aligned with the OpenAI format
    /// </summary>
    private static string ToOpenAIFormat(IEnumerable<ChatMessageContent> chatHistory)
    {
        return $"[{string.Join(
            ", \n",
            chatHistory.Select(m => $"{{\"role:\" {m.Role}, \"content:\" {m.Content}}}"))}]";
    }

    /// <summary>
    /// Start a completion activity and return the activity.
    /// The `formatPrompt` delegate won't be invoked if events are disabled.
    /// </summary>
    private static Activity? StartCompletionActivity<T>(
        string modelName,
        string modelProvider,
        T prompt,
        PromptExecutionSettings? executionSettings,
        Func<T, string> formatPrompt)
    {
        if (!IsModelDiagnosticsEnabled())
        {
            return null;
        }

        string operationName = prompt is ChatHistory ? "chat.completions" : "text.completions";
        var activity = s_activitySource.StartActivityWithTags(
            $"{operationName} {modelName}",
            [
                new(ModelDiagnosticsTags.Operation, operationName),
                new(ModelDiagnosticsTags.System, modelProvider),
                new(ModelDiagnosticsTags.Model, modelName),
            ]);

        AddOptionalTags(activity, executionSettings);

        if (s_enableSensitiveEvents)
        {
            var formattedContent = formatPrompt(prompt);
            activity?.AttachSensitiveDataAsEvent(
                ModelDiagnosticsTags.PromptEvent,
                [
                    new(ModelDiagnosticsTags.PromptEventPrompt, formattedContent),
                ]);
        }

        return activity;
    }

    /// <summary>
    /// Set the completion response for a given activity.
    /// The `formatCompletions` delegate won't be invoked if events are disabled.
    /// </summary>
    private static void SetCompletionResponse<T>(
        Activity activity,
        T completions,
        int promptTokens,
        int completionTokens,
        Func<T, string> formatCompletions) where T : IEnumerable<KernelContent>
    {
        if (!IsModelDiagnosticsEnabled())
        {
            return;
        }

        activity.AddTags(
            [
                new(ModelDiagnosticsTags.FinishReason, GetFinishReasons(completions)),
                new(ModelDiagnosticsTags.PromptToken, promptTokens),
                new(ModelDiagnosticsTags.CompletionToken, completionTokens),
            ]);

        if (s_enableSensitiveEvents)
        {
            activity.AttachSensitiveDataAsEvent(
                ModelDiagnosticsTags.CompletionEvent,
                [
                    new(ModelDiagnosticsTags.CompletionEventCompletion, formatCompletions(completions)),
                ]);
        }
    }

    private static string GetFinishReasons(IEnumerable<KernelContent> completions)
    {
        var finishReasons = completions.Select(c =>
        {
            if (c.Metadata?.TryGetValue("FinishReason", out var finishReason) == true)
            {
                return finishReason;
            }

            return null;
        });

        return $"[{string.Join(", ", finishReasons)}]";
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
        public const string MaxToken = "gen_ai.request.max_token";
        public const string Temperature = "gen_ai.request.temperature";
        public const string TopP = "gen_ai.request.top_p";
        public const string ResponseId = "gen_ai.response.id";
        public const string ResponseModel = "gen_ai.response.model";
        public const string FinishReason = "gen_ai.response.finish_reason";
        public const string PromptToken = "gen_ai.response.prompt_tokens";
        public const string CompletionToken = "gen_ai.response.completion_tokens";
        public const string Prompt = "gen_ai.content.prompt";
        public const string Completion = "gen_ai.content.completion";

        // Activity events
        public const string PromptEvent = "gen_ai.content.prompt";
        public const string PromptEventPrompt = "gen_ai.prompt";
        public const string CompletionEvent = "gen_ai.content.completion";
        public const string CompletionEventCompletion = "gen_ai.completion";
    }
    # endregion
}
