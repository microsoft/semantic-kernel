// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using SemanticKernel.Service.CopilotChat.Models;

namespace SemanticKernel.Service.CopilotChat.Storage;

/// <summary>
/// A repository for chat messages.
/// </summary>
public class ChatMessageRepository : Repository<ChatMessage>
{
    /// <summary>
    /// Initializes a new instance of the ChatMessageRepository class.
    /// </summary>
    /// <param name="storageContext">The storage context.</param>
    public ChatMessageRepository(IStorageContext<ChatMessage> storageContext)
        : base(storageContext)
    {
    }

    /// <summary>
    /// Finds chat messages by chat id.
    /// </summary>
    public Task<IEnumerable<ChatMessage>> FindByChatIdAsync(string chatId)
    {
        return base.StorageContext.QueryEntitiesAsync(e => e.ChatId == chatId);
    }

    public async Task<ChatMessage> FindLastByChatIdAsync(string chatId)
    {
        var chatMessages = await this.FindByChatIdAsync(chatId);
        var first = chatMessages.MaxBy(e => e.Timestamp);
        return first ?? throw new KeyNotFoundException($"No messages found for chat '{chatId}'.");
    }
}
