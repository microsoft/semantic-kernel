using System.Globalization;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.CoreSkills;
using Microsoft.SemanticKernel.KernelExtensions;
using Microsoft.SemanticKernel.Memory;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.SkillDefinition;

namespace SKWebApi.Skills;

public class InifiniteChatSkill
{
    private readonly ISKFunction _completionFunction;

    public InifiniteChatSkill(IKernel kernel)
    {
        this._completionFunction = kernel.CreateSemanticFunction(
            "{{$INPUT}}",
            skillName: nameof(InifiniteChatSkill),
            description: "Complete the prompt.");
    }

    [SKFunction("Extract user intent")]
    [SKFunctionName("ExtractUserAsync")]
    [SKFunctionContextParameter(Name = "tokenLimit", Description = "Maximum number of tokens")]
    public async Task<SKContext> ExtractUserIntentAsync(SKContext context)
    {
        var tokenLimit = int.Parse(context["tokenLimit"], new NumberFormatInfo());
        var historyTokenBudget =
            tokenLimit -
            SystemPromptDefaults.ResponseTokenLimit -
            this.EstimateTokenCount(string.Join("\n", new string[]{
                SystemPromptDefaults.SystemDescriptionPrompt,
                SystemPromptDefaults.SystemIntentPrompt,
                SystemPromptDefaults.SystemIntentContinuationPrompt})
            );

        var intentExtractionVariables = new ContextVariables(SystemPromptDefaults.SystemIntentExtractiongPrompt);
        intentExtractionVariables.Set("tokenLimit", historyTokenBudget.ToString(new NumberFormatInfo()));
        return await this._completionFunction.InvokeAsync(
            new SKContext(
                intentExtractionVariables,
                context.Memory,
                context.Skills,
                context.Log,
                context.CancellationToken
            )
        );
    }

    [SKFunction("Extract user memories")]
    [SKFunctionContextParameter(Name = "tokenLimit", Description = "Maximum number of tokens")]
    public async Task<string> ExtractUserMemoriesAsync(SKContext context)
    {
        var tokenLimit = int.Parse(context["tokenLimit"], new NumberFormatInfo());
        var remainingToken = tokenLimit;

        var latestMessage = await this.GetLatestMemoryAsync(context);
        var results = context.Memory.SearchAsync("ChatMessages", latestMessage.Text);

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
    public async Task<string> ExtractChatHistoryAsync(SKContext context)
    {
        var tokenLimit = int.Parse(context["tokenLimit"], new NumberFormatInfo());

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
    [SKFunctionInput(Description = "Prompt")]
    public async Task<SKContext> ChatAsync(SKContext context)
    {
        var tokenLimit = int.Parse(context["tokenLimit"], new NumberFormatInfo());
        var remainingToken =
            tokenLimit -
            SystemPromptDefaults.ResponseTokenLimit -
            this.EstimateTokenCount(string.Join("\n", new string[]{
                SystemPromptDefaults.SystemDescriptionPrompt,
                SystemPromptDefaults.SystemResponsePrompt,
                SystemPromptDefaults.SystemChatContinuationPrompt})
            );

        var contextVariables = new ContextVariables(SystemPromptDefaults.SystemIntentExtractiongPrompt);
        contextVariables.Set("tokenLimit", remainingToken.ToString(new NumberFormatInfo()));
        return await this._completionFunction.InvokeAsync(
            new SKContext(
                contextVariables,
                context.Memory,
                context.Skills,
                context.Log,
                context.CancellationToken
            )
        );
    }

    [SKFunction("Save a new message to the chat history")]
    [SKFunctionName("SaveNewMessage")]
    [SKFunctionInput(Description = "The new message")]
    [SKFunctionContextParameter(Name = "audience", Description = "The audience who created the message.")]
    public async Task<bool> SaveNewMessageAsync(string message, SKContext context)
    {
        var timeSkill = new TimeSkill();
        var currentTime = timeSkill.Now();
        var messageIdentifier = $"[{currentTime}] {context["audience"]}";
        var rawMessagePrompt = "{{TextMemorySkill.Save " + message + " }}";
        var formattedMessage = $"{messageIdentifier}: {message}";
        var formattedMessagePrompt = "{{TextMemorySkill.Save " + formattedMessage + " }}";

        /*
         * There will be two types of collections:
         * 1. ChatMessages: this collection saves all the raw chat messages.
         * 2. {timestamp}: each of these collections will only have one chat message whose key is the timestamp.
         * All chat messages will be saved to both kinds of collections.
         */
        var chatMessagesVarianbles = new ContextVariables(rawMessagePrompt);
        chatMessagesVarianbles.Set("CollectionParam", "ChatMessages");
        chatMessagesVarianbles.Set("KeyParam", messageIdentifier);

        var timestampedMessagesVarianbles = new ContextVariables(formattedMessagePrompt);
        timestampedMessagesVarianbles.Set("CollectionParam", messageIdentifier);
        timestampedMessagesVarianbles.Set("KeyParam", currentTime);

        return await this._completionFunction.InvokeAsync(
            new SKContext(
                chatMessagesVarianbles,
                context.Memory,
                context.Skills,
                context.Log,
                context.CancellationToken
            )
        ) != null && await this._completionFunction.InvokeAsync(
            new SKContext(
                timestampedMessagesVarianbles,
                context.Memory,
                context.Skills,
                context.Log,
                context.CancellationToken
            )
        ) != null;
    }

    private async IAsyncEnumerable<MemoryQueryResult> GetAllMemoriesAsync(SKContext context)
    {
        var allCollections = await context.Memory.GetCollectionsAsync(context.CancellationToken);
        var allChatMessageCollections = allCollections.Where(collection => collection != "ChatMessages");
        IList<MemoryQueryResult> allChatMessageMemories = new List<MemoryQueryResult>();
        foreach (var collection in allChatMessageCollections)
        {
            var results = await context.Memory.SearchAsync(
                collection,
                "",
                limit: 1,
                minRelevanceScore: 0.0, // no relevance required since the collection only has one entry
                cancel: context.CancellationToken
            ).ToListAsync();
            allChatMessageMemories.Add(results.First());
        }
        yield return (MemoryQueryResult)allChatMessageMemories.OrderBy(memory => memory.Id).ToAsyncEnumerable();
    }

    private async Task<MemoryQueryResult> GetLatestMemoryAsync(SKContext context)
    {
        var allMemories = this.GetAllMemoriesAsync(context);
        return await allMemories.FirstAsync();
    }

    private int EstimateTokenCount(string text)
    {
        return (int)Math.Floor(text.Length / SystemPromptDefaults.TokenEstimateFactor);
    }
}
