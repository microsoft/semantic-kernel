using System.Globalization;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.AI;
using Microsoft.SemanticKernel.AI.TextCompletion;
using Microsoft.SemanticKernel.CoreSkills;
using Microsoft.SemanticKernel.Memory;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.SkillDefinition;

namespace SemanticKernel.Service.Skills;

/// <summary>
/// ChatSkill offers a more coherent chat experience by using memories
/// to extract conversation history and user intentions.
/// </summary>
public class ChatSkill
{
    /// <summary>
    /// A kernel instance to create a completion function since each invocation
    /// of the <see cref="ChatAsync"/> function will generate a new prompt dynamically.
    /// </summary>
    private readonly IKernel _kernel;

    public ChatSkill(IKernel kernel)
    {
        this._kernel = kernel;
    }

    /// <summary>
    /// Extract user intent from the conversation history.
    /// </summary>
    /// <param name="context">Contains the 'audience' indicating the name of the user.</param>
    [SKFunction("Extract user intent")]
    [SKFunctionName("ExtractUserIntent")]
    [SKFunctionContextParameter(Name = "audience", Description = "The audience the chat bot is interacting with.")]
    public async Task<string> ExtractUserIntentAsync(SKContext context)
    {
        var tokenLimit = SystemPromptDefaults.CompletionTokenLimit;
        var historyTokenBudget =
            tokenLimit -
            SystemPromptDefaults.ResponseTokenLimit -
            this.EstimateTokenCount(string.Join("\n", new string[]
                {
                    SystemPromptDefaults.SystemDescriptionPrompt,
                    SystemPromptDefaults.SystemIntentPrompt,
                    SystemPromptDefaults.SystemIntentContinuationPrompt
                })
            );

        var intentExtractionVariables = new ContextVariables();
        intentExtractionVariables.Set("tokenLimit", historyTokenBudget.ToString(new NumberFormatInfo()));
        intentExtractionVariables.Set("knowledgeCutoff", SystemPromptDefaults.KnowledgeCutoffDate);
        intentExtractionVariables.Set("audience", context["audience"]);

        var completionFunction = this._kernel.CreateSemanticFunction(
            SystemPromptDefaults.SystemIntentExtractionPrompt,
            skillName: nameof(ChatSkill),
            description: "Complete the prompt.");

        var result = await completionFunction.InvokeAsync(
            new SKContext(
                intentExtractionVariables,
                context.Memory,
                context.Skills,
                context.Log,
                context.CancellationToken
            ),
            settings: this.CreateIntentCompletionSettings()
        );

        return $"User intent: {result}";
    }

    /// <summary>
    /// Extract relevant memories based on the latest message.
    /// </summary>
    /// <param name="context">Contains the 'tokenLimit' and the 'contextTokenLimit' controlling the length of the prompt.</param>
    [SKFunction("Extract user memories")]
    [SKFunctionName("ExtractUserMemories")]
    [SKFunctionContextParameter(Name = "tokenLimit", Description = "Maximum number of tokens")]
    [SKFunctionContextParameter(Name = "contextTokenLimit", Description = "Maximum number of context tokens")]
    public async Task<string> ExtractUserMemoriesAsync(SKContext context)
    {
        var tokenLimit = int.Parse(context["tokenLimit"], new NumberFormatInfo());
        var contextTokenLimit = int.Parse(context["contextTokenLimit"], new NumberFormatInfo());

        var remainingToken = Math.Min(
            tokenLimit,
            Math.Floor(contextTokenLimit * SystemPromptDefaults.MemoriesResponseContextWeight)
        );

        string memoryText = "";
        var latestMessage = await this.GetLatestMemoryAsync(context);
        if (latestMessage != null)
        {
            var results = context.Memory.SearchAsync("ChatMessages", latestMessage.Metadata.Text, limit: 1000);
            await foreach (var memory in results)
            {
                var estimatedTokenCount = this.EstimateTokenCount(memory.Metadata.Text);
                if (remainingToken - estimatedTokenCount > 0)
                {
                    memoryText += $"\n{memory.Metadata.Text}";
                    remainingToken -= estimatedTokenCount;
                }
                else
                {
                    break;
                }
            }
        }

        return $"Past memories:\n{memoryText.Trim()}";
    }

    /// <summary>
    /// Extract chat history.
    /// </summary>
    /// <param name="context">Contains the 'tokenLimit' and the 'contextTokenLimit' controlling the length of the prompt.</param>
    [SKFunction("Extract chat history")]
    [SKFunctionName("ExtractChatHistory")]
    [SKFunctionContextParameter(Name = "tokenLimit", Description = "Maximum number of tokens")]
    [SKFunctionContextParameter(Name = "contextTokenLimit", Description = "Maximum number of context tokens")]
    public async Task<string> ExtractChatHistoryAsync(SKContext context)
    {
        var tokenLimit = int.Parse(context["tokenLimit"], new NumberFormatInfo());

        // TODO: Use contextTokenLimit to determine how much of the chat history to return
        // TODO: relevant history

        var remainingToken = tokenLimit;
        string historyText = "";

        await foreach (var message in this.GetAllMemoriesAsync(context))
        {
            if (message == null)
            {
                continue;
            }

            var estimatedTokenCount = this.EstimateTokenCount(message.Metadata.Text);
            if (remainingToken - estimatedTokenCount > 0)
            {
                historyText += $"\n{message.Metadata.Text}";
                remainingToken -= estimatedTokenCount;
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
    [SKFunctionContextParameter(Name = "audience", Description = "The audience the chat bot is interacting with.")]
    public async Task<SKContext> ChatAsync(string message, SKContext context)
    {
        var tokenLimit = SystemPromptDefaults.CompletionTokenLimit;
        var remainingToken =
            tokenLimit -
            SystemPromptDefaults.ResponseTokenLimit -
            this.EstimateTokenCount(string.Join("\n", new string[]
                {
                    SystemPromptDefaults.SystemDescriptionPrompt,
                    SystemPromptDefaults.SystemResponsePrompt,
                    SystemPromptDefaults.SystemChatContinuationPrompt
                })
            );
        var contextTokenLimit = remainingToken;

        // Save this new message to memory such that subsequent chat responses can use it
        try
        {
            await this.SaveNewMessageAsync(message, context);
        }
        catch (Exception ex) when (!ex.IsCriticalException())
        {
            context.Fail($"Unable to save new message: {ex.Message}", ex);
            return context;
        }

        // Extract user intent and update remaining token count
        var userIntent = await this.ExtractUserIntentAsync(context);
        remainingToken -= this.EstimateTokenCount(userIntent);

        context.Variables.Set("tokenLimit", remainingToken.ToString(new NumberFormatInfo()));
        context.Variables.Set("contextTokenLimit", contextTokenLimit.ToString(new NumberFormatInfo()));
        context.Variables.Set("knowledgeCutoff", SystemPromptDefaults.KnowledgeCutoffDate);
        context.Variables.Set("userIntent", userIntent);
        context.Variables.Set("audience", context["audience"]);

        var completionFunction = this._kernel.CreateSemanticFunction(
            SystemPromptDefaults.SystemChatPrompt,
            skillName: nameof(ChatSkill),
            description: "Complete the prompt.");

        context = await completionFunction.InvokeAsync(
            context: context,
            settings: this.CreateChatResponseCompletionSettings()
        );

        // Save this response to memory such that subsequent chat responses can use it
        try
        {
            context.Variables.Set("audience", "bot");
            await this.SaveNewMessageAsync(context.Result, context);
        }
        catch (Exception ex) when (!ex.IsCriticalException())
        {
            context.Fail($"Unable to save new response: {ex.Message}", ex);
            return context;
        }

        return context;
    }

    /// <summary>
    /// Save a new message to the chat history.
    /// </summary>
    /// <param name="message"></param>
    /// <param name="context">Contains the 'audience' indicating the name of the user.</param>
    [SKFunction("Save a new message to the chat history")]
    [SKFunctionName("SaveNewMessage")]
    [SKFunctionInput(Description = "The new message")]
    [SKFunctionContextParameter(Name = "audience", Description = "The audience who created the message.")]
    public async Task SaveNewMessageAsync(string message, SKContext context)
    {
        var timeSkill = new TimeSkill();
        var currentTime = $"{timeSkill.Now()} {timeSkill.Second()}";
        var messageIdentifier = $"[{currentTime}] {context["audience"]}";
        var formattedMessage = $"{messageIdentifier}: {message}";

        /*
         * There will be two types of collections:
         * 1. ChatMessages: this collection saves all the raw chat messages.
         * 2. {timestamp}: each of these collections will only have one chat message whose key is the timestamp.
         * All chat messages will be saved to both kinds of collections.
         */
        await context.Memory.SaveInformationAsync(
            collection: "ChatMessages",
            text: message,
            id: messageIdentifier,
            cancel: context.CancellationToken
        );

        await context.Memory.SaveInformationAsync(
            collection: messageIdentifier,
            text: formattedMessage,
            id: currentTime,
            cancel: context.CancellationToken
        );
    }

    /// <summary>
    /// Get all chat messages from memory.
    /// </summary>
    /// <param name="context">Contains the memory object.</param>
    private async IAsyncEnumerable<MemoryQueryResult?> GetAllMemoriesAsync(SKContext context)
    {
        var allCollections = await context.Memory.GetCollectionsAsync(context.CancellationToken);
        var allChatMessageCollections = allCollections.Where(collection => collection != "ChatMessages");
        IList<MemoryQueryResult> allChatMessageMemories = new List<MemoryQueryResult>();
        try
        {
            foreach (var collection in allChatMessageCollections)
            {
                var results = await context.Memory.SearchAsync(
                    collection,
                    "abc", // dummy query since we don't care about relevance. An empty string will cause exception.
                    limit: 1,
                    minRelevanceScore: 0.0, // no relevance required since the collection only has one entry
                    cancel: context.CancellationToken
                ).ToListAsync();
                allChatMessageMemories.Add(results.First());
            }
        }
        catch (AIException ex)
        {
            context.Log.LogWarning("Exception while retrieving memories: {0}", ex);
            context.Fail($"Exception while retrieving memories: {ex.Message}", ex);
            yield break;
        }

        foreach (var memory in allChatMessageMemories.OrderBy(memory => memory.Metadata.Id))
        {
            yield return memory;
        }
    }

    /// <summary>
    /// Get the latest chat message from memory.
    /// </summary>
    /// <param name="context">Contains the memory object.</param>
    private async Task<MemoryQueryResult?> GetLatestMemoryAsync(SKContext context)
    {
        var allMemories = this.GetAllMemoriesAsync(context);

        return await allMemories.FirstOrDefaultAsync();
    }

    /// <summary>
    /// Create a completion settings object for chat response. Parameters are read from the SystemPromptDefaults class.
    /// </summary>
    private CompleteRequestSettings CreateChatResponseCompletionSettings()
    {
        var completionSettings = new CompleteRequestSettings
        {
            MaxTokens = SystemPromptDefaults.ResponseTokenLimit,
            Temperature = SystemPromptDefaults.ResponseTemperature,
            TopP = SystemPromptDefaults.ResponseTopP,
            FrequencyPenalty = SystemPromptDefaults.ResponseFrequencyPenalty,
            PresencePenalty = SystemPromptDefaults.ResponsePresencePenalty
        };

        return completionSettings;
    }

    /// <summary>
    /// Create a completion settings object for intent response. Parameters are read from the SystemPromptDefaults class.
    /// </summary>
    private CompleteRequestSettings CreateIntentCompletionSettings()
    {
        var completionSettings = new CompleteRequestSettings
        {
            MaxTokens = SystemPromptDefaults.ResponseTokenLimit,
            Temperature = SystemPromptDefaults.IntentTemperature,
            TopP = SystemPromptDefaults.IntentTopP,
            FrequencyPenalty = SystemPromptDefaults.IntentFrequencyPenalty,
            PresencePenalty = SystemPromptDefaults.IntentPresencePenalty,
            StopSequences = new string[] { "] bot:" }
        };

        return completionSettings;
    }

    /// <summary>
    /// Estimate the number of tokens in a string.
    /// TODO: This is a very naive implementation. We should use the new implementation that is available in the kernel.
    /// </summary>
    private int EstimateTokenCount(string text)
    {
        return (int)Math.Floor(text.Length / SystemPromptDefaults.TokenEstimateFactor);
    }
}
