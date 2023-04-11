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

    public Task<ChatMessage> FindLastByChatId(string chatId)
    {
        var messages = this.FindByChatId(chatId).Result;
        if (messages.Count() == 0)
        {
            throw new KeyNotFoundException($"No messages found for chat {chatId}.");
        }
        return Task.FromResult(messages.OrderByDescending(e => e.Timestamp).First());
    }
}
