using System.Globalization;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.AI;
using Microsoft.SemanticKernel.CoreSkills;
using Microsoft.SemanticKernel.KernelExtensions;
using Microsoft.SemanticKernel.Memory;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.SkillDefinition;

namespace SKWebApi.Skills;

public class ChatSkill
{
    private readonly IKernel _kernel;

    public ChatSkill(IKernel kernel)
    {
        this._kernel = kernel;
    }

    [SKFunction("Extract user intent")]
    [SKFunctionName("ExtractUserIntent")]
    [SKFunctionContextParameter(Name = "audience", Description = "The audience the chat bot is interacting with.")]
    public async Task<string> ExtractUserIntentAsync(SKContext context)
    {
        var tokenLimit = SystemPromptDefaults.CompletionTokenLimit;
        var historyTokenBudget =
            tokenLimit -
            SystemPromptDefaults.ResponseTokenLimit -
            this.EstimateTokenCount(string.Join("\n", new string[]{
                SystemPromptDefaults.SystemDescriptionPrompt,
                SystemPromptDefaults.SystemIntentPrompt,
                SystemPromptDefaults.SystemIntentContinuationPrompt})
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
            settings: this.GetIntentCompletionSettings()
        );

        return $"User intent: {result.ToString()}";
    }

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

        var latestMessage = await this.GetLatestMemoryAsync(context);
        Console.WriteLine($"Latest message: {latestMessage.Text}");
        var results = context.Memory.SearchAsync("ChatMessages", latestMessage.Text, limit: 1000);

        string memoryText = "";
        await foreach (var memory in results)
        {
            var estimatedTokenCount = this.EstimateTokenCount(memory.Text);
            if (remainingToken - estimatedTokenCount > 0)
            {
                memoryText += $"\n{memory.Text}";
                remainingToken -= estimatedTokenCount;
            }
            else
            {
                break;
            }
        }

        return $"Past memories:\n{memoryText.Trim()}";
    }

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
            var estimatedTokenCount = this.EstimateTokenCount(message.Text);
            if (remainingToken - estimatedTokenCount > 0)
            {
                historyText += $"\n{message.Text}";
                remainingToken -= estimatedTokenCount;
            }
            else
            {
                break;
            }
        }

        return $"Chat history:\n{historyText.Trim()}";
    }

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
            this.EstimateTokenCount(string.Join("\n", new string[]{
                SystemPromptDefaults.SystemDescriptionPrompt,
                SystemPromptDefaults.SystemResponsePrompt,
                SystemPromptDefaults.SystemChatContinuationPrompt})
            );
        var contextTokenLimit = remainingToken;

        // Save this new message to memory such that subsequent chat responses can use it
        try
        {
            await this.SaveNewMessageAsync(message, context);
        }
        catch (Exception ex)
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
            settings: this.GetChatResponseCompletionSettings()
        );

        // Save this response to memory such that subsequent chat responses can use it
        try
        {
            context.Variables.Set("audience", "bot");
            await this.SaveNewMessageAsync(context.Result, context);
        }
        catch (Exception ex)
        {
            context.Fail($"Unable to save new response: {ex.Message}", ex);
            return context;
        }

        return context;
    }

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

    private async IAsyncEnumerable<MemoryQueryResult> GetAllMemoriesAsync(SKContext context)
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
                    "abc",                  // dummy query
                    limit: 1,
                    minRelevanceScore: 0.0, // no relevance required since the collection only has one entry
                    cancel: context.CancellationToken
                ).ToListAsync();
                allChatMessageMemories.Add(results.First());
            }
        }
        catch (Exception e)
        {
            Console.WriteLine("Exception while retrieving memories: {0}", e.Message);
            throw e;
        }

        foreach (var memory in allChatMessageMemories.OrderBy(memory => memory.Id))
        {
            yield return memory;
        }
    }

    private async Task<MemoryQueryResult> GetLatestMemoryAsync(SKContext context)
    {
        var allMemories = this.GetAllMemoriesAsync(context);
        return await allMemories.FirstAsync();
    }

    private CompleteRequestSettings GetChatResponseCompletionSettings()
    {
        var completionSettings = new CompleteRequestSettings();
        completionSettings.MaxTokens = SystemPromptDefaults.ResponseTokenLimit;
        completionSettings.Temperature = SystemPromptDefaults.ResponseTemperature;
        completionSettings.TopP = SystemPromptDefaults.ResponseTopP;
        completionSettings.FrequencyPenalty = SystemPromptDefaults.ResponseFrequencyPenalty;
        completionSettings.PresencePenalty = SystemPromptDefaults.ResponsePresencePenalty;
        return completionSettings;
    }

    private CompleteRequestSettings GetIntentCompletionSettings()
    {
        var completionSettings = new CompleteRequestSettings();
        completionSettings.MaxTokens = SystemPromptDefaults.ResponseTokenLimit;
        completionSettings.Temperature = SystemPromptDefaults.IntentTemperature;
        completionSettings.TopP = SystemPromptDefaults.IntentTopP;
        completionSettings.FrequencyPenalty = SystemPromptDefaults.IntentFrequencyPenalty;
        completionSettings.PresencePenalty = SystemPromptDefaults.IntentPresencePenalty;
        completionSettings.StopSequences = new string[] { "] bot:" };
        return completionSettings;
    }

    private int EstimateTokenCount(string text)
    {
        return (int)Math.Floor(text.Length / SystemPromptDefaults.TokenEstimateFactor);
    }
}
