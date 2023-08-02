// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Http;
using Microsoft.AspNetCore.Mvc;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Options;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Memory;
using SemanticKernel.Service.CopilotChat.Extensions;
using SemanticKernel.Service.CopilotChat.Models;
using SemanticKernel.Service.CopilotChat.Options;
using SemanticKernel.Service.CopilotChat.Storage;
using SemanticKernel.Service.Options;

namespace SemanticKernel.Service.CopilotChat.Controllers;

[ApiController]
public class BotController : ControllerBase
{
    private readonly ILogger<BotController> _logger;
    private readonly IMemoryStore? _memoryStore;
    private readonly ISemanticTextMemory _semanticMemory;
    private readonly ChatSessionRepository _chatRepository;
    private readonly ChatMessageRepository _chatMessageRepository;
    private readonly ChatParticipantRepository _chatParticipantRepository;

    private readonly BotSchemaOptions _botSchemaOptions;
    private readonly AIServiceOptions _embeddingOptions;
    private readonly DocumentMemoryOptions _documentMemoryOptions;

    /// <summary>
    /// The constructor of BotController.
    /// </summary>
    /// <param name="optionalIMemoryStore">Optional memory store.
    ///     High level semantic memory implementations, such as Azure Cognitive Search, do not allow for providing embeddings when storing memories.
    ///     We wrap the memory store in an optional memory store to allow controllers to pass dependency injection validation and potentially optimize
    ///     for a lower-level memory implementation (e.g. Qdrant). Lower level memory implementations (i.e., IMemoryStore) allow for reusing embeddings,
    ///     whereas high level memory implementation (i.e., ISemanticTextMemory) assume embeddings get recalculated on every write.
    /// </param>
    /// <param name="chatRepository">The chat session repository.</param>
    /// <param name="chatMessageRepository">The chat message repository.</param>
    /// <param name="chatParticipantRepository">The chat participant repository.</param>
    /// <param name="aiServiceOptions">The AI service options where we need the embedding settings from.</param>
    /// <param name="botSchemaOptions">The bot schema options.</param>
    /// <param name="documentMemoryOptions">The document memory options.</param>
    /// <param name="logger">The logger.</param>
    public BotController(
        OptionalIMemoryStore optionalIMemoryStore,
        ISemanticTextMemory semanticMemory,
        ChatSessionRepository chatRepository,
        ChatMessageRepository chatMessageRepository,
        ChatParticipantRepository chatParticipantRepository,
        IOptions<AIServiceOptions> aiServiceOptions,
        IOptions<BotSchemaOptions> botSchemaOptions,
        IOptions<DocumentMemoryOptions> documentMemoryOptions,
        ILogger<BotController> logger)
    {
        this._memoryStore = optionalIMemoryStore.MemoryStore;
        this._logger = logger;
        this._semanticMemory = semanticMemory;
        this._chatRepository = chatRepository;
        this._chatMessageRepository = chatMessageRepository;
        this._chatParticipantRepository = chatParticipantRepository;
        this._botSchemaOptions = botSchemaOptions.Value;
        this._embeddingOptions = aiServiceOptions.Value;
        this._documentMemoryOptions = documentMemoryOptions.Value;
    }

    /// <summary>
    /// Upload a bot.
    /// </summary>
    /// <param name="kernel">The Semantic Kernel instance.</param>
    /// <param name="userId">The user id.</param>
    /// <param name="bot">The bot object from the message body</param>
    /// <param name="cancellationToken">The cancellation token.</param>
    /// <returns>The HTTP action result with new chat session object.</returns>
    [Authorize]
    [HttpPost]
    [Route("bot/upload")]
    [ProducesResponseType(StatusCodes.Status201Created)]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<ActionResult<ChatSession>> UploadAsync(
        [FromServices] IKernel kernel,
        [FromQuery] string userId,
        [FromBody] Bot bot,
        CancellationToken cancellationToken)
    {
        // TODO: We should get userId from server context instead of from request for privacy/security reasons when support multiple users.
        this._logger.LogDebug("Received call to upload a bot");

        if (!IsBotCompatible(
                externalBotSchema: bot.Schema,
                externalBotEmbeddingConfig: bot.EmbeddingConfigurations,
                embeddingOptions: this._embeddingOptions,
                botSchemaOptions: this._botSchemaOptions))
        {
            return this.BadRequest("Incompatible schema. " +
                                   $"The supported bot schema is {this._botSchemaOptions.Name}/{this._botSchemaOptions.Version} " +
                                   $"for the {this._embeddingOptions.Models.Embedding} model from {this._embeddingOptions.Type}. " +
                                   $"But the uploaded file is with schema {bot.Schema.Name}/{bot.Schema.Version} " +
                                   $"for the {bot.EmbeddingConfigurations.DeploymentOrModelId} model from {bot.EmbeddingConfigurations.AIService}.");
        }

        string chatTitle = $"{bot.ChatTitle} - Clone";
        string chatId = string.Empty;
        ChatSession newChat;

        // Upload chat history into chat repository and embeddings into memory.

        // 1. Create a new chat and get the chat id.
        newChat = new ChatSession(chatTitle);
        await this._chatRepository.CreateAsync(newChat);
        await this._chatParticipantRepository.CreateAsync(new ChatParticipant(userId, newChat.Id));
        chatId = newChat.Id;

        string oldChatId = bot.ChatHistory.First().ChatId;

        // 2. Update the app's chat storage.
        foreach (var message in bot.ChatHistory)
        {
            var chatMessage = new ChatMessage(
                message.UserId,
                message.UserName,
                chatId,
                message.Content,
                message.Prompt,
                ChatMessage.AuthorRoles.Participant)
            {
                Timestamp = message.Timestamp
            };
            await this._chatMessageRepository.CreateAsync(chatMessage);
        }

        // 3. Update the memory.
        await this.BulkUpsertMemoryRecordsAsync(oldChatId, chatId, bot.Embeddings, cancellationToken);

        // TODO: Revert changes if any of the actions failed

        return this.CreatedAtAction(
            nameof(ChatHistoryController.GetChatSessionByIdAsync),
            nameof(ChatHistoryController).Replace("Controller", "", StringComparison.OrdinalIgnoreCase),
            new { chatId },
            newChat);
    }

    /// <summary>
    /// Download a bot.
    /// </summary>
    /// <param name="kernel">The Semantic Kernel instance.</param>
    /// <param name="chatId">The chat id to be downloaded.</param>
    /// <returns>The serialized Bot object of the chat id.</returns>
    [Authorize]
    [HttpGet]
    [ActionName("DownloadAsync")]
    [Route("bot/download/{chatId:guid}")]
    [ProducesResponseType(StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<ActionResult<string>> DownloadAsync(
        [FromServices] IKernel kernel,
        Guid chatId)
    {
        this._logger.LogDebug("Received call to download a bot");
        var memory = await this.CreateBotAsync(kernel: kernel, chatId: chatId);

        return JsonSerializer.Serialize(memory);
    }

    /// <summary>
    /// Check if an external bot file is compatible with the application.
    /// </summary>
    /// <remarks>
    /// If the embeddings are not generated from the same model, the bot file is not compatible.
    /// </remarks>
    /// <param name="externalBotSchema">The external bot schema.</param>
    /// <param name="externalBotEmbeddingConfig">The external bot embedding configuration.</param>
    /// <param name="embeddingOptions">The embedding options.</param>
    /// <param name="botSchemaOptions">The bot schema options.</param>
    /// <returns>True if the bot file is compatible with the app; otherwise false.</returns>
    private static bool IsBotCompatible(
        BotSchemaOptions externalBotSchema,
        BotEmbeddingConfig externalBotEmbeddingConfig,
        AIServiceOptions embeddingOptions,
        BotSchemaOptions botSchemaOptions)
    {
        // The app can define what schema/version it supports before the community comes out with an open schema.
        return externalBotSchema.Name.Equals(botSchemaOptions.Name, StringComparison.OrdinalIgnoreCase)
               && externalBotSchema.Version == botSchemaOptions.Version
               && externalBotEmbeddingConfig.AIService == embeddingOptions.Type
               && externalBotEmbeddingConfig.DeploymentOrModelId.Equals(embeddingOptions.Models.Embedding, StringComparison.OrdinalIgnoreCase);
    }

    /// <summary>
    /// Get memory from memory store and append the memory records to a given list.
    /// It will update the memory collection name in the new list if the newCollectionName is provided.
    /// </summary>
    /// <param name="kernel">The Semantic Kernel instance.</param>
    /// <param name="collectionName">The current collection name. Used to query the memory storage.</param>
    /// <param name="embeddings">The embeddings list where we will append the fetched memory records.</param>
    /// <param name="newCollectionName">
    /// The new collection name when appends to the embeddings list. Will use the old collection name if not provided.
    /// </param>
    private static async Task GetMemoryRecordsAndAppendToEmbeddingsAsync(
        IKernel kernel,
        string collectionName,
        List<KeyValuePair<string, List<MemoryQueryResult>>> embeddings,
        string newCollectionName = "")
    {
        List<MemoryQueryResult> collectionMemoryRecords = await kernel.Memory.SearchAsync(
            collectionName,
            "abc", // dummy query since we don't care about relevance. An empty string will cause exception.
            limit: 999999999, // temp solution to get as much as record as a workaround.
            minRelevanceScore: -1, // no relevance required since the collection only has one entry
            withEmbeddings: true,
            cancellationToken: default
        ).ToListAsync();

        embeddings.Add(new KeyValuePair<string, List<MemoryQueryResult>>(
            string.IsNullOrEmpty(newCollectionName) ? collectionName : newCollectionName,
            collectionMemoryRecords));
    }

    /// <summary>
    /// Prepare the bot information of a given chat.
    /// </summary>
    /// <param name="kernel">The semantic kernel object.</param>
    /// <param name="chatId">The chat id of the bot</param>
    /// <returns>A Bot object that represents the chat session.</returns>
    private async Task<Bot> CreateBotAsync(IKernel kernel, Guid chatId)
    {
        var chatIdString = chatId.ToString();
        var bot = new Bot
        {
            // get the bot schema version
            Schema = this._botSchemaOptions,

            // get the embedding configuration
            EmbeddingConfigurations = new BotEmbeddingConfig
            {
                AIService = this._embeddingOptions.Type,
                DeploymentOrModelId = this._embeddingOptions.Models.Embedding
            }
        };

        // get the chat title
        ChatSession chat = await this._chatRepository.FindByIdAsync(chatIdString);
        bot.ChatTitle = chat.Title;

        // get the chat history
        bot.ChatHistory = await this.GetAllChatMessagesAsync(chatIdString);

        // get the memory collections associated with this chat
        // TODO: filtering memory collections by name might be fragile.
        var chatCollections = (await kernel.Memory.GetCollectionsAsync())
            .Where(collection => collection.StartsWith(chatIdString, StringComparison.OrdinalIgnoreCase));

        foreach (var collection in chatCollections)
        {
            await GetMemoryRecordsAndAppendToEmbeddingsAsync(kernel: kernel, collectionName: collection, embeddings: bot.Embeddings);
        }

        // get the document memory collection names (global scope)
        await GetMemoryRecordsAndAppendToEmbeddingsAsync(
            kernel: kernel,
            collectionName: this._documentMemoryOptions.GlobalDocumentCollectionName,
            embeddings: bot.DocumentEmbeddings);

        // get the document memory collection names (user scope)
        await GetMemoryRecordsAndAppendToEmbeddingsAsync(
            kernel: kernel,
            collectionName: this._documentMemoryOptions.ChatDocumentCollectionNamePrefix + chatIdString,
            embeddings: bot.DocumentEmbeddings);

        return bot;
    }

    /// <summary>
    /// Get chat messages of a given chat id.
    /// </summary>
    /// <param name="chatId">The chat id</param>
    /// <returns>The list of chat messages in descending order of the timestamp</returns>
    private async Task<List<ChatMessage>> GetAllChatMessagesAsync(string chatId)
    {
        // TODO: We might want to set limitation on the number of messages that are pulled from the storage.
        return (await this._chatMessageRepository.FindByChatIdAsync(chatId))
            .OrderByDescending(m => m.Timestamp).ToList();
    }

    /// <summary>
    /// Bulk upsert memory records into memory store.
    /// </summary>
    /// <param name="oldChatId">The original chat id of the memory records.</param>
    /// <param name="chatId">The new chat id that will replace the original chat id.</param>
    /// <param name="embeddings">The list of embeddings of the chat id.</param>
    /// <returns>The function doesn't return anything.</returns>
    private async Task BulkUpsertMemoryRecordsAsync(string oldChatId, string chatId, List<KeyValuePair<string, List<MemoryQueryResult>>> embeddings, CancellationToken cancellationToken = default)
    {
        foreach (var collection in embeddings)
        {
            foreach (var record in collection.Value)
            {
                if (record != null && record.Embedding != null)
                {
                    var newCollectionName = collection.Key.Replace(oldChatId, chatId, StringComparison.OrdinalIgnoreCase);

                    if (this._memoryStore == null)
                    {
                        await this._semanticMemory.SaveInformationAsync(
                            collection: newCollectionName,
                            text: record.Metadata.Text,
                            id: record.Metadata.Id,
                            cancellationToken: cancellationToken);
                    }
                    else
                    {
                        MemoryRecord data = MemoryRecord.LocalRecord(
                            id: record.Metadata.Id,
                            text: record.Metadata.Text,
                            embedding: record.Embedding.Value,
                            description: null,
                            additionalMetadata: null);

                        if (!(await this._memoryStore.DoesCollectionExistAsync(newCollectionName, default)))
                        {
                            await this._memoryStore.CreateCollectionAsync(newCollectionName, default);
                        }

                        await this._memoryStore.UpsertAsync(newCollectionName, data, default);
                    }
                }
            }
        }
    }
}
