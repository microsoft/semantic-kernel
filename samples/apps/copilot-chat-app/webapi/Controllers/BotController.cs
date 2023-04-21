// Copyright (c) Microsoft. All rights reserved.

using Microsoft.AspNetCore.Mvc;
using Microsoft.SemanticKernel.Memory;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel;
using SemanticKernel.Service.Config;
using SemanticKernel.Service.Model;
using SemanticKernel.Service.Skills;
using SemanticKernel.Service.Storage;
using System.Text.Json;
using Microsoft.AspNetCore.Authorization;

namespace SemanticKernel.Service.Controllers;

[ApiController]
public class BotController : ControllerBase
{
    private readonly IConfiguration _configuration;
    private readonly ILogger<SemanticKernelController> _logger;
    private readonly PromptSettings _promptSettings;

    public BotController(IConfiguration configuration, PromptSettings promptSettings, ILogger<SemanticKernelController> logger)
    {
        this._configuration = configuration;
        this._promptSettings = promptSettings;
        this._logger = logger;
    }

    [Authorize]
    [HttpPost]
    [Route("bot/import")]
    [ProducesResponseType(StatusCodes.Status202Accepted)]
    [ProducesResponseType(StatusCodes.Status415UnsupportedMediaType)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<ActionResult> ImportAsync(
        [FromServices] Kernel kernel,
        [FromServices] ChatSessionRepository chatRepository,
        [FromServices] ChatMessageRepository chatMessageRepository,
        [FromQuery] string userId,
        [FromBody] Bot bot)
    {
        // TODO: We should get userId from server context instead of from request for privacy/security reasons when support multipe users.
        this._logger.LogDebug("Received call to import a bot");

        if (!this.IsBotCompatible(bot.Schema, bot.Configurations))
        {
            return new UnsupportedMediaTypeResult();
        }

        // TODO: Add real chat title, user object id and user name.
        string chatTitle = $"{bot.ChatTitle} - Clone";

        string chatId = string.Empty;

        // Import chat history into CosmosDB and embeddings into SK memory.
        try
        {
            // 1. Create a new chat and get the chat id.
            var newChat = new ChatSession(userId, chatTitle);
            await chatRepository.CreateAsync(newChat);
            chatId = newChat.Id;

            string oldChatId = bot.ChatHistory.First().ChatId;

            // 2. Update the app's chat storage.
            foreach (var message in bot.ChatHistory)
            {
                var chatMessage = new ChatMessage(message.UserId, message.UserName, chatId, message.Content, ChatMessage.AuthorRoles.Participant);
                chatMessage.Timestamp = message.Timestamp;
                // TODO: should we use UpsertItemAsync?
                await chatMessageRepository.CreateAsync(chatMessage);
            }

            // 3. Update SK memory.
            foreach (var collection in bot.Embeddings)
            {
                foreach (var record in collection.Value)
                {
                    if (record != null && record.Embedding != null)
                    {
                        var newCollectionKey = collection.Key.Replace(oldChatId, chatId, StringComparison.OrdinalIgnoreCase);
                        await kernel.Memory.UpsertAsync(newCollectionKey, record.Metadata.Text, record.Metadata.Id, record.Embedding.Value);
                    }
                }
            }
        }
        catch
        {
            // TODO: Revert changes if any of the actions failed
            throw;
        }

        return this.Accepted();
    }

    [Authorize]
    [HttpGet]
    [Route("bot/export/{chatId:guid}")]
    [ProducesResponseType(StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<ActionResult<string>> ExportAsync(
        [FromServices] Kernel kernel,
        [FromServices] ChatSessionRepository chatRepository,
        [FromServices] ChatMessageRepository chatMessageRepository,
        Guid chatId)
    {
        this._logger.LogDebug("Received call to export a bot");
        var memory = await this.CreateBotAsync(kernel, chatRepository, chatMessageRepository, chatId);

        return JsonSerializer.Serialize(memory);
    }

    private bool IsBotCompatible(BotSchemaConfig externalBotSchema, BotConfiguration externalBotConfiguration)
    {
        var embeddingAIServiceConfig = this._configuration.GetSection("Embedding").Get<AIServiceConfig>();
        var botSchema = this._configuration.GetSection("BotFileSchema").Get<BotSchemaConfig>();

        if (embeddingAIServiceConfig != null && botSchema != null)
        {
            // The app can define what schema/version it supports before the community comes out with an open schema.
            return externalBotSchema.Name.Equals(
                botSchema.Name, StringComparison.OrdinalIgnoreCase)
                && externalBotSchema.Verson == botSchema.Verson
                && externalBotConfiguration.EmbeddingAIService.Equals(
                embeddingAIServiceConfig.AIService, StringComparison.OrdinalIgnoreCase)
                && externalBotConfiguration.EmbeddingDeploymentOrModelId.Equals(
                embeddingAIServiceConfig.DeploymentOrModelId, StringComparison.OrdinalIgnoreCase);
        }
        else
        {
            return false;
        }
    }

    /// <summary>
    /// Prepare the bot information of a given chat.
    /// </summary>
    /// <param name="kernel">The semantic kernel object.</param>
    /// <param name="chatRepository">The chat session repository object.</param>
    /// <param name="chatMessageRepository">The chat message repository object.</param>
    /// <param name="chatId">The chat id of the bot</param>
    private async Task<Bot> CreateBotAsync(
        Kernel kernel,
        ChatSessionRepository chatRepository,
        ChatMessageRepository chatMessageRepository,
        Guid chatId)
    {
        kernel.RegisterNativeSkills(chatRepository, chatMessageRepository, this._promptSettings, this._logger);

        var chatIdString = chatId.ToString();
        var bot = new Bot();

        // get the bot schema version
        bot.Schema = this._configuration.GetSection("BotFileSchema").Get<BotSchemaConfig>();

        // get the embedding configuration
        var embeddingAIServiceConfig = this._configuration.GetSection("Embedding").Get<AIServiceConfig>();
        bot.Configurations = new BotConfiguration
        {
            EmbeddingAIService = embeddingAIServiceConfig?.AIService ?? string.Empty,
            EmbeddingDeploymentOrModelId = embeddingAIServiceConfig?.DeploymentOrModelId ?? string.Empty
        };

        // get the chat title
        ChatSession chat = await chatRepository.FindByIdAsync(chatIdString);
        bot.ChatTitle = chat.Title;

        // get the chat history
        // TODO: should we call skill or call the storage directly?
        var contextVariables = new ContextVariables(chatIdString);
        contextVariables.Set("startIdx", "0");
        contextVariables.Set("count", "100");
        var messages = await this.GetAllChatMessagesAsync(kernel, contextVariables);

        if (messages?.Value != null)
        {
            bot.ChatHistory = JsonSerializer.Deserialize<List<ChatMessage>>(messages.Value);
        }

        // get the memory collections associated with this chat
        // TODO: filtering memory collections by name might be risky. We can discuss if there is a better way.
        var allCollections = (await kernel.Memory.GetCollectionsAsync())
            .Where(collection => collection.StartsWith(chatIdString, StringComparison.OrdinalIgnoreCase));

        foreach (var collection in allCollections)
        {
            List<MemoryQueryResult> collectionMemoryRecords = await kernel.Memory.SearchAsync(
                collection,
                "abc", // dummy query since we don't care about relevance. An empty string will cause exception.
                limit: 999999999, // hacky way to get as much as record as a workaround. TODO: Call GetAll() when it's in the SK memory storage API.
                minRelevanceScore: -1, // no relevance required since the collection only has one entry
                withEmbeddings: true,
                cancel: default
            ).ToListAsync();

            bot.Embeddings.Add(new KeyValuePair<string, List<MemoryQueryResult>>(collection, collectionMemoryRecords));
        }

        return bot;
    }

    /// <summary>
    /// Get chat messages from the ChatHistorySkill
    /// </summary>
    /// <param name="kernel">The semantic kernel object.</param>
    /// <param name="variables">The context variables.</param>
    /// <returns>The result of the ask.</returns>
    private async Task<AskResult> GetAllChatMessagesAsync(Kernel kernel, ContextVariables variables)
    {
        ISKFunction function = kernel.Skills.GetFunction("ChatHistorySkill", "GetAllChatMessages");

        // Invoke the GetAllChatMessages function of ChatHistorySkill.
        SKContext result = await kernel.RunAsync(variables, function!);
        return new AskResult { Value = result.Result, Variables = result.Variables.Select(v => new KeyValuePair<string, string>(v.Key, v.Value)) };
    }
}
