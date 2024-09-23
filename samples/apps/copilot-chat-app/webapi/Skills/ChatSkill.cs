// Copyright (c) Microsoft. All rights reserved.

using System.Globalization;
using System.Text.Json;
using System.Text.Json.Nodes;
using System.Text.RegularExpressions;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.AI.TextCompletion;
using Microsoft.SemanticKernel.Memory;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.Planning;
using Microsoft.SemanticKernel.SkillDefinition;
using SemanticKernel.Service.Config;
using SemanticKernel.Service.Model;
using SemanticKernel.Service.Skills.OpenApiSkills.GitHubSkill.Model;
using SemanticKernel.Service.Skills.OpenApiSkills.JiraSkill.Model;
using SemanticKernel.Service.Storage;

namespace SemanticKernel.Service.Skills;

/// <summary>
/// ChatSkill offers a more coherent chat experience by using memories
/// to extract conversation history and user intentions.
/// </summary>
public class ChatSkill
{
    /// <summary>
    /// Logger
    /// </summary>
    private readonly ILogger _logger;

    /// <summary>
    /// A kernel instance to create a completion function since each invocation
    /// of the <see cref="ChatAsync"/> function will generate a new prompt dynamically.
    /// </summary>
    private readonly IKernel _kernel;

    /// <summary>
    /// A repository to save and retrieve chat messages.
    /// </summary>
    private readonly ChatMessageRepository _chatMessageRepository;

    /// <summary>
    /// A repository to save and retrieve chat sessions.
    /// </summary>
    private readonly ChatSessionRepository _chatSessionRepository;

    /// <summary>
    /// Settings containing prompt texts.
    /// </summary>
    private readonly PromptSettings _promptSettings;

    /// <summary>
    /// CopilotChat's planner to gather additional information for the chat context.
    /// </summary>
    private readonly CopilotChatPlanner _planner;

    /// <summary>
    /// Options for the planner.
    /// </summary>
    private readonly PlannerOptions _plannerOptions;

    /// <summary>
    /// Create a new instance of <see cref="ChatSkill"/>.
    /// </summary>
    public ChatSkill(
        IKernel kernel,
        ChatMessageRepository chatMessageRepository,
        ChatSessionRepository chatSessionRepository,
        PromptSettings promptSettings,
        CopilotChatPlanner planner,
        PlannerOptions plannerOptions,
        ILogger logger)
    {
        this._logger = logger;
        this._kernel = kernel;
        this._chatMessageRepository = chatMessageRepository;
        this._chatSessionRepository = chatSessionRepository;
        this._promptSettings = promptSettings;
        this._planner = planner;
        this._plannerOptions = plannerOptions;
    }

    /// <summary>
    /// Extract user intent from the conversation history.
    /// </summary>
    /// <param name="context">Contains the 'audience' indicating the name of the user.</param>
    [SKFunction("Extract user intent")]
    [SKFunctionName("ExtractUserIntent")]
    [SKFunctionContextParameter(Name = "chatId", Description = "Chat ID to extract history from")]
    [SKFunctionContextParameter(Name = "audience", Description = "The audience the chat bot is interacting with.")]
    public async Task<string> ExtractUserIntentAsync(SKContext context)
    {
        var tokenLimit = this._promptSettings.CompletionTokenLimit;
        var historyTokenBudget =
            tokenLimit -
            this._promptSettings.ResponseTokenLimit -
            Utilities.TokenCount(string.Join("\n", new string[]
                {
                    this._promptSettings.SystemDescriptionPrompt,
                    this._promptSettings.SystemIntentPrompt,
                    this._promptSettings.SystemIntentContinuationPrompt
                })
            );

        // Clone the context to avoid modifying the original context variables.
        var intentExtractionContext = Utilities.CopyContextWithVariablesClone(context);
        intentExtractionContext.Variables.Set("tokenLimit", historyTokenBudget.ToString(new NumberFormatInfo()));
        intentExtractionContext.Variables.Set("knowledgeCutoff", this._promptSettings.KnowledgeCutoffDate);

        var completionFunction = this._kernel.CreateSemanticFunction(
            this._promptSettings.SystemIntentExtractionPrompt,
            skillName: nameof(ChatSkill),
            description: "Complete the prompt.");

        var result = await completionFunction.InvokeAsync(
            intentExtractionContext,
            settings: this.CreateIntentCompletionSettings()
        );

        if (result.ErrorOccurred)
        {
            context.Log.LogError("{0}: {1}", result.LastErrorDescription, result.LastException);
            context.Fail(result.LastErrorDescription);
            return string.Empty;
        }

        return $"User intent: {result}";
    }

    /// <summary>
    /// Extract relevant memories based on the latest message.
    /// </summary>
    /// <param name="context">Contains the 'tokenLimit' and the 'contextTokenLimit' controlling the length of the prompt.</param>
    [SKFunction("Extract user memories")]
    [SKFunctionName("ExtractUserMemories")]
    [SKFunctionContextParameter(Name = "chatId", Description = "Chat ID to extract history from")]
    [SKFunctionContextParameter(Name = "tokenLimit", Description = "Maximum number of tokens")]
    [SKFunctionContextParameter(Name = "contextTokenLimit", Description = "Maximum number of context tokens")]
    public async Task<string> ExtractUserMemoriesAsync(SKContext context)
    {
        var chatId = context["chatId"];
        var tokenLimit = int.Parse(context["tokenLimit"], new NumberFormatInfo());
        var contextTokenLimit = int.Parse(context["contextTokenLimit"], new NumberFormatInfo());
        var remainingToken = Math.Min(
            tokenLimit,
            Math.Floor(contextTokenLimit * this._promptSettings.MemoriesResponseContextWeight)
        );

        // Find the most recent message.
        var latestMessage = await this._chatMessageRepository.FindLastByChatIdAsync(chatId);

        // Search for relevant memories.
        List<MemoryQueryResult> relevantMemories = new();
        foreach (var memoryName in this._promptSettings.MemoryMap.Keys)
        {
            var results = context.Memory.SearchAsync(
                SemanticMemoryExtractor.MemoryCollectionName(chatId, memoryName),
                latestMessage.ToString(),
                limit: 100,
                minRelevanceScore: this._promptSettings.SemanticMemoryMinRelevance);
            await foreach (var memory in results)
            {
                relevantMemories.Add(memory);
            }
        }

        relevantMemories = relevantMemories.OrderByDescending(m => m.Relevance).ToList();

        string memoryText = "";
        foreach (var memory in relevantMemories)
        {
            var tokenCount = Utilities.TokenCount(memory.Metadata.Text);
            if (remainingToken - tokenCount > 0)
            {
                memoryText += $"\n[{memory.Metadata.Description}] {memory.Metadata.Text}";
                remainingToken -= tokenCount;
            }
            else
            {
                break;
            }
        }

        // Update the token limit.
        memoryText = $"Past memories (format: [memory type] <label>: <details>):\n{memoryText.Trim()}";
        tokenLimit -= Utilities.TokenCount(memoryText);
        context.Variables.Set("tokenLimit", tokenLimit.ToString(new NumberFormatInfo()));

        return memoryText;
    }

    /// <summary>
    /// Extract relevant additional knowledge using a planner.
    /// </summary>
    [SKFunction("Acquire external information")]
    [SKFunctionName("AcquireExternalInformation")]
    [SKFunctionContextParameter(Name = "userIntent", Description = "The intent of the user.")]
    [SKFunctionContextParameter(Name = "tokenLimit", Description = "Maximum number of tokens")]
    public async Task<string> AcquireExternalInformationAsync(SKContext context)
    {
        if (!this._plannerOptions.Enabled)
        {
            return string.Empty;
        }

        // Skills run in the planner may modify the SKContext. Clone the context to avoid
        // modifying the original context variables.
        SKContext plannerContext = Utilities.CopyContextWithVariablesClone(context);

        // Use the user intent message as the input to the plan.
        plannerContext.Variables.Update(plannerContext["userIntent"]);

        // Create a plan and run it.
        Plan plan = await this._planner.CreatePlanAsync(plannerContext.Variables.Input);
        if (plan.Steps.Count <= 0)
        {
            return string.Empty;
        }

        SKContext planContext = await plan.InvokeAsync(plannerContext);
        if (planContext.ErrorOccurred)
        {
            this._logger.LogWarning("{0}: {1}", planContext.LastErrorDescription, planContext.LastException);
            return string.Empty;
        }

        int tokenLimit = int.Parse(context["tokenLimit"], new NumberFormatInfo());

        // The result of the plan may be from an OpenAPI skill. Attempt to extract JSON from the response.
        bool extractJsonFromOpenApi = this.TryExtractJsonFromOpenApiPlanResult(planContext.Variables.Input, out string planResult);
        if (extractJsonFromOpenApi)
        {
            int relatedInformationTokenLimit = (int)Math.Floor(tokenLimit * this._promptSettings.RelatedInformationContextWeight);
            planResult = this.OptimizeOpenApiSkillJson(planResult, relatedInformationTokenLimit, plan);
        }
        else
        {
            // If not, use result of the plan execution result directly.
            planResult = planContext.Variables.Input;
        }

        string informationText = $"[START RELATED INFORMATION]\n{planResult.Trim()}\n[END RELATED INFORMATION]\n";

        // Adjust the token limit using the number of tokens in the information text.
        tokenLimit -= Utilities.TokenCount(informationText);
        context.Variables.Set("tokenLimit", tokenLimit.ToString(new NumberFormatInfo()));

        return informationText;
    }

    /// <summary>
    /// Extract chat history.
    /// </summary>
    /// <param name="context">Contains the 'tokenLimit' controlling the length of the prompt.</param>
    [SKFunction("Extract chat history")]
    [SKFunctionName("ExtractChatHistory")]
    [SKFunctionContextParameter(Name = "chatId", Description = "Chat ID to extract history from")]
    [SKFunctionContextParameter(Name = "tokenLimit", Description = "Maximum number of tokens")]
    public async Task<string> ExtractChatHistoryAsync(SKContext context)
    {
        var chatId = context["chatId"];
        var tokenLimit = int.Parse(context["tokenLimit"], new NumberFormatInfo());

        var messages = await this._chatMessageRepository.FindByChatIdAsync(chatId);
        var sortedMessages = messages.OrderByDescending(m => m.Timestamp);

        var remainingToken = tokenLimit;
        string historyText = "";
        foreach (var chatMessage in sortedMessages)
        {
            var formattedMessage = chatMessage.ToFormattedString();
            var tokenCount = Utilities.TokenCount(formattedMessage);
            if (remainingToken - tokenCount > 0)
            {
                historyText = $"{formattedMessage}\n{historyText}";
                remainingToken -= tokenCount;
            }
            else
            {
                break;
            }
        }

        return $"Chat history:\n{historyText.Trim()}";
    }

    /// <summary>
    /// This is the entry point for getting a chat response. It manages the token limit, saves
    /// messages to memory, and fill in the necessary context variables for completing the
    /// prompt that will be rendered by the template engine.
    /// </summary>
    /// <param name="message"></param>
    /// <param name="context">Contains the 'tokenLimit' and the 'contextTokenLimit' controlling the length of the prompt.</param>
    [SKFunction("Get chat response")]
    [SKFunctionName("Chat")]
    [SKFunctionInput(Description = "The new message")]
    [SKFunctionContextParameter(Name = "userId", Description = "Unique and persistent identifier for the user")]
    [SKFunctionContextParameter(Name = "userName", Description = "Name of the user")]
    [SKFunctionContextParameter(Name = "chatId", Description = "Unique and persistent identifier for the chat")]
    public async Task<SKContext> ChatAsync(string message, SKContext context)
    {
        // Log exception and strip it from the context, leaving the error description.
        SKContext RemoveExceptionFromContext(SKContext chatContext)
        {
            chatContext.Log.LogError("{0}: {1}", chatContext.LastErrorDescription, chatContext.LastException);
            chatContext.Fail(chatContext.LastErrorDescription);
            return chatContext;
        }

        var tokenLimit = this._promptSettings.CompletionTokenLimit;
        var remainingToken =
            tokenLimit -
            this._promptSettings.ResponseTokenLimit -
            Utilities.TokenCount(string.Join("\n", new string[]
                {
                    this._promptSettings.SystemDescriptionPrompt,
                    this._promptSettings.SystemResponsePrompt,
                    this._promptSettings.SystemChatContinuationPrompt
                })
            );
        var contextTokenLimit = remainingToken;
        var userId = context["userId"];
        var userName = context["userName"];
        var chatId = context["chatId"];

        // TODO: check if user has access to the chat

        // Save this new message to memory such that subsequent chat responses can use it
        try
        {
            await this.SaveNewMessageAsync(message, userId, userName, chatId);
        }
        catch (Exception ex) when (!ex.IsCriticalException())
        {
            context.Log.LogError("Unable to save new message: {0}", ex.Message);
            context.Fail($"Unable to save new message: {ex.Message}", ex);
            return context;
        }

        // Clone the context to avoid modifying the original context variables.
        var chatContext = Utilities.CopyContextWithVariablesClone(context);
        chatContext.Variables.Set("knowledgeCutoff", this._promptSettings.KnowledgeCutoffDate);
        chatContext.Variables.Set("audience", userName);

        // Extract user intent and update remaining token count
        var userIntent = await this.ExtractUserIntentAsync(chatContext);
        if (chatContext.ErrorOccurred)
        {
            return RemoveExceptionFromContext(chatContext);
        }

        chatContext.Variables.Set("userIntent", userIntent);
        // Update remaining token count
        remainingToken -= Utilities.TokenCount(userIntent);
        chatContext.Variables.Set("contextTokenLimit", contextTokenLimit.ToString(new NumberFormatInfo()));
        chatContext.Variables.Set("tokenLimit", remainingToken.ToString(new NumberFormatInfo()));

        var completionFunction = this._kernel.CreateSemanticFunction(
            this._promptSettings.SystemChatPrompt,
            skillName: nameof(ChatSkill),
            description: "Complete the prompt.");

        chatContext = await completionFunction.InvokeAsync(
            context: chatContext,
            settings: this.CreateChatResponseCompletionSettings()
        );

        // If the completion function failed, return the context containing the error.
        if (chatContext.ErrorOccurred)
        {
            return RemoveExceptionFromContext(chatContext);
        }

        // Save this response to memory such that subsequent chat responses can use it
        try
        {
            await this.SaveNewResponseAsync(chatContext.Result, chatId);
        }
        catch (Exception ex) when (!ex.IsCriticalException())
        {
            context.Log.LogError("Unable to save new response: {0}", ex.Message);
            context.Fail($"Unable to save new response: {ex.Message}");
            return context;
        }

        // Extract semantic memory
        await this.ExtractSemanticMemoryAsync(chatId, chatContext);

        context.Variables.Update(chatContext.Result);
        context.Variables.Set("userId", "Bot");
        return context;
    }

    #region Private

    /// <summary>
    /// Try to extract json from the planner response as if it were from an OpenAPI skill.
    /// </summary>
    private bool TryExtractJsonFromOpenApiPlanResult(string openApiSkillResponse, out string json)
    {
        try
        {
            JsonNode? jsonNode = JsonNode.Parse(openApiSkillResponse);
            string contentType = jsonNode?["contentType"]?.ToString() ?? string.Empty;
            if (contentType.StartsWith("application/json", StringComparison.InvariantCultureIgnoreCase))
            {
                var content = jsonNode?["content"]?.ToString() ?? string.Empty;
                if (!string.IsNullOrWhiteSpace(content))
                {
                    json = content;
                    return true;
                }
            }
        }
        catch (JsonException)
        {
            this._logger.LogDebug("Unable to extract JSON from planner response, it is likely not from an OpenAPI skill.");
        }
        catch (InvalidOperationException)
        {
            this._logger.LogDebug("Unable to extract JSON from planner response, it may already be proper JSON.");
        }

        json = string.Empty;
        return false;
    }

    /// <summary>
    /// Try to optimize json from the planner response
    /// based on token limit
    /// </summary>
    private string OptimizeOpenApiSkillJson(string jsonContent, int tokenLimit, Plan plan)
    {
        int jsonTokenLimit = (int)(tokenLimit * this._promptSettings.RelatedInformationContextWeight);

        // Remove all new line characters + leading and trailing white space
        jsonContent = Regex.Replace(jsonContent.Trim(), @"[\n\r]", string.Empty);
        var document = JsonDocument.Parse(jsonContent);
        string lastSkillInvoked = plan.Steps[^1].SkillName;
        string lastSkillFunctionInvoked = plan.Steps[^1].Name;
        bool trimSkillResponse = false;

        // The json will be deserialized based on the response type of the particular operation that was last invoked by the planner
        // The response type can be a custom trimmed down json structure, which is useful in staying within the token limit
        Type skillResponseType = this.GetOpenApiSkillResponseType(ref document, ref lastSkillInvoked, ref lastSkillFunctionInvoked, ref trimSkillResponse);

        if (trimSkillResponse)
        {
            // Deserializing limits the json content to only the fields defined in the respective OpenApiSkill's Model classes
            var skillResponse = JsonSerializer.Deserialize(jsonContent, skillResponseType);
            jsonContent = skillResponse != null ? JsonSerializer.Serialize(skillResponse) : string.Empty;
            document = JsonDocument.Parse(jsonContent);
        }

        int jsonContentTokenCount = Utilities.TokenCount(jsonContent);

        // Return the JSON content if it does not exceed the token limit
        if (jsonContentTokenCount < jsonTokenLimit)
        {
            return jsonContent;
        }

        List<object> itemList = new();

        // Summary (List) Object
        // To stay within token limits, attempt to truncate the list of results
        if (document.RootElement.ValueKind == JsonValueKind.Array)
        {
            foreach (JsonElement item in document.RootElement.EnumerateArray())
            {
                int itemTokenCount = Utilities.TokenCount(item.ToString());

                if (jsonTokenLimit - itemTokenCount > 0)
                {
                    itemList.Add(item);
                    jsonTokenLimit -= itemTokenCount;
                }
                else
                {
                    break;
                }
            }
        }

        // Detail Object
        // To stay within token limits, attempt to truncate the list of properties
        if (document.RootElement.ValueKind == JsonValueKind.Object)
        {
            foreach (JsonProperty property in document.RootElement.EnumerateObject())
            {
                int propertyTokenCount = Utilities.TokenCount(property.ToString());

                if (jsonTokenLimit - propertyTokenCount > 0)
                {
                    itemList.Add(property);
                    jsonTokenLimit -= propertyTokenCount;
                }
                else
                {
                    break;
                }
            }
        }

        return itemList.Count > 0
            ? JsonSerializer.Serialize(itemList)
            : string.Format(CultureInfo.InvariantCulture, "JSON response for {0} is too large to be consumed at this time.", lastSkillInvoked);
    }

    private Type GetOpenApiSkillResponseType(ref JsonDocument document, ref string lastSkillInvoked, ref string lastSkillFunctionInvoked, ref bool trimSkillResponse)
    {
        Type skillResponseType = typeof(object); // Use a reasonable default response type

        // Different operations under the skill will return responses as json structures;
        // Prune each operation response according to the most important/contextual fields only to avoid going over the token limit
        // Check what the last skill invoked was and deserialize the JSON content accordingly
        if (string.Equals(lastSkillInvoked, "GitHubSkill", StringComparison.Ordinal))
        {
            trimSkillResponse = true;
            skillResponseType = this.GetGithubSkillResponseType(ref document);
        }
        else if (string.Equals(lastSkillInvoked, "JiraSkill", StringComparison.Ordinal))
        {
            trimSkillResponse = true;
            skillResponseType = this.GetJiraSkillResponseType(ref document, ref lastSkillFunctionInvoked);
        }

        return skillResponseType;
    }

    private Type GetGithubSkillResponseType(ref JsonDocument document)
    {
        return document.RootElement.ValueKind == JsonValueKind.Array ? typeof(PullRequest[]) : typeof(PullRequest);
    }

    private Type GetJiraSkillResponseType(ref JsonDocument document, ref string lastSkillFunctionInvoked)
    {
        if (lastSkillFunctionInvoked == "GetIssue")
        {
            return document.RootElement.ValueKind == JsonValueKind.Array ? typeof(IssueResponse[]) : typeof(IssueResponse);
        }

        return typeof(IssueResponse);
    }

    /// <summary>
    /// Save a new message to the chat history.
    /// </summary>
    /// <param name="message">The message</param>
    /// <param name="userId">The user ID</param>
    /// <param name="userName"></param>
    /// <param name="chatId">The chat ID</param>
    private async Task SaveNewMessageAsync(string message, string userId, string userName, string chatId)
    {
        // Make sure the chat exists.
        await this._chatSessionRepository.FindByIdAsync(chatId);

        var chatMessage = new ChatMessage(userId, userName, chatId, message);
        await this._chatMessageRepository.CreateAsync(chatMessage);
    }

    /// <summary>
    /// Save a new response to the chat history.
    /// </summary>
    /// <param name="response">Response from the chat.</param>
    /// <param name="chatId">The chat ID</param>
    private async Task SaveNewResponseAsync(string response, string chatId)
    {
        // Make sure the chat exists.
        await this._chatSessionRepository.FindByIdAsync(chatId);

        var chatMessage = ChatMessage.CreateBotResponseMessage(chatId, response);
        await this._chatMessageRepository.CreateAsync(chatMessage);
    }

    /// <summary>
    /// Extract and save semantic memory.
    /// </summary>
    /// <param name="chatId">The Chat ID.</param>
    /// <param name="context">The context containing the memory.</param>
    private async Task ExtractSemanticMemoryAsync(string chatId, SKContext context)
    {
        foreach (var memoryName in this._promptSettings.MemoryMap.Keys)
        {
            try
            {
                var semanticMemory = await SemanticMemoryExtractor.ExtractCognitiveMemoryAsync(
                    memoryName,
                    this._kernel,
                    context,
                    this._promptSettings
                );
                foreach (var item in semanticMemory.Items)
                {
                    await this.CreateMemoryAsync(item, chatId, context, memoryName);
                }
            }
            catch (Exception ex) when (!ex.IsCriticalException())
            {
                // Skip semantic memory extraction for this item if it fails.
                // We cannot rely on the model to response with perfect Json each time.
                context.Log.LogInformation("Unable to extract semantic memory for {0}: {1}. Continuing...", memoryName, ex.Message);
                continue;
            }
        }
    }

    /// <summary>
    /// Create a memory item in the memory collection.
    /// </summary>
    /// <param name="item">A SemanticChatMemoryItem instance</param>
    /// <param name="chatId">The ID of the chat the memories belong to</param>
    /// <param name="context">The context that contains the memory</param>
    /// <param name="memoryName">Name of the memory</param>
    private async Task CreateMemoryAsync(SemanticChatMemoryItem item, string chatId, SKContext context, string memoryName)
    {
        var memoryCollectionName = SemanticMemoryExtractor.MemoryCollectionName(chatId, memoryName);

        var memories = context.Memory.SearchAsync(
            collection: memoryCollectionName,
            query: item.ToFormattedString(),
            limit: 1,
            minRelevanceScore: this._promptSettings.SemanticMemoryMinRelevance,
            cancellationToken: context.CancellationToken
        ).ToEnumerable();

        if (!memories.Any())
        {
            await context.Memory.SaveInformationAsync(
                collection: memoryCollectionName,
                text: item.ToFormattedString(),
                id: Guid.NewGuid().ToString(),
                description: memoryName,
                cancellationToken: context.CancellationToken
            );
        }
    }

    /// <summary>
    /// Create a completion settings object for chat response. Parameters are read from the PromptSettings class.
    /// </summary>
    private JsonObject CreateChatResponseCompletionSettings()
    {
        var completionSettings = new JsonObject
        {
            ["max_tokens"] = this._promptSettings.ResponseTokenLimit,
            ["temperature"] = this._promptSettings.ResponseTemperature,
            ["top_p"] = this._promptSettings.ResponseTopP,
            ["frequency_penalty"] = this._promptSettings.ResponseFrequencyPenalty,
            ["presence_penalty"] = this._promptSettings.ResponsePresencePenalty
        };

        return completionSettings;
    }

    /// <summary>
    /// Create a completion settings object for intent response. Parameters are read from the PromptSettings class.
    /// </summary>
    private JsonObject CreateIntentCompletionSettings()
    {
        var completionSettings = new JsonObject
        {
            ["max_tokens"] = this._promptSettings.ResponseTokenLimit,
            ["temperature"] = this._promptSettings.IntentTemperature,
            ["top_p"] = this._promptSettings.IntentTopP,
            ["frequency_penalty"] = this._promptSettings.IntentFrequencyPenalty,
            ["presence_penalty"] = this._promptSettings.IntentPresencePenalty,
            ["stop_sequences"] = new JsonArray { "] bot:" }
        };

        return completionSettings;
    }

    # endregion
}
