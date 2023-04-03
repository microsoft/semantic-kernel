using SKWebApi.Skills;

namespace SKWebApi.Storage;

public class ChatMessageRepository : Repository<ChatMessage>
{
    public ChatMessageRepository(IStorageContext<ChatMessage> storageContext)
        : base(storageContext)
    { }

    public Task<IEnumerable<ChatMessage>> FindByChatId(string chatId)
    {
        return Task.FromResult(base._StorageContext.QueryableEntities.Where(e => e.ChatId == chatId).AsEnumerable());
    }

    public async Task<ChatMessage> FindLastByChatIdAsync(string chatId)
    {
        var messages = await this.FindByChatId(chatId);
        if (!messages.Any())
        {
            throw new KeyNotFoundException($"No messages found for chat {chatId}.");
        }
        return messages.OrderByDescending(e => e.Timestamp).First();
    }
}
