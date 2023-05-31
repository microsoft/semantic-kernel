// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using Microsoft.SemanticKernel.Memory;
using SemanticKernel.Service.CopilotChat.Options;

namespace SemanticKernel.Service.CopilotChat.Models;

/// <summary>
/// The data model of a bot for portability.
/// </summary>
public class Bot
{
    /// <summary>
    /// The schema information of the bot data model.
    /// </summary>
    public BotSchemaOptions Schema { get; set; } = new BotSchemaOptions();

    /// <summary>
    /// The embedding configurations.
    /// </summary>
    public BotEmbeddingConfig EmbeddingConfigurations { get; set; } = new BotEmbeddingConfig();

    /// <summary>
    /// The title of the chat with the bot.
    /// </summary>
    public string ChatTitle { get; set; } = string.Empty;

    /// <summary>
    /// The chat history. It contains all the messages in the conversation with the bot.
    /// </summary>
    public List<ChatMessage> ChatHistory { get; set; } = new List<ChatMessage>();

    // TODO: Change from MemoryQueryResult to MemoryRecord
    /// <summary>
    /// The embeddings of the bot.
    /// </summary>
    public List<KeyValuePair<string, List<MemoryQueryResult>>> Embeddings { get; set; } = new List<KeyValuePair<string, List<MemoryQueryResult>>>();

    // TODO: Change from MemoryQueryResult to MemoryRecord
    /// <summary>
    /// The embeddings of uploaded documents in Copilot Chat. It represents the document memory which is accessible to all chat sessions of a given user.
    /// </summary>
    public List<KeyValuePair<string, List<MemoryQueryResult>>> DocumentEmbeddings { get; set; } = new List<KeyValuePair<string, List<MemoryQueryResult>>>();
}
