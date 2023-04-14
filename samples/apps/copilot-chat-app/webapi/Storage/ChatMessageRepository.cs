// Copyright (c) Microsoft. All rights reserved.

using SemanticKernel.Service.Skills;

namespace SemanticKernel.Service.Storage;

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
        return Task.FromResult(base.StorageContext.QueryableEntities.Where(e => e.ChatId == chatId).AsEnumerable());
    }

    public async Task<ChatMessage> FindLastByChatIdAsync(string chatId)
    {
        var messages = await this.FindByChatIdAsync(chatId);
        if (!messages.Any())
        {
            throw new KeyNotFoundException($"No messages found for chat {chatId}.");
        }

        return messages.OrderByDescending(e => e.Timestamp).First();
    }
}
