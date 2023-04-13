// Copyright (c) Microsoft. All rights reserved.

using SKWebApi.Storage;

namespace SKWebApi.Skills;

public class ChatSessionRepository : Repository<ChatSession>
{
    public ChatSessionRepository(IStorageContext<ChatSession> storageContext)
        : base(storageContext)
    { }

    public Task<IEnumerable<ChatSession>> FindByUserId(string userId)
    {
        return Task.FromResult(base._StorageContext.QueryableEntities.Where(e => e.UserId == userId).AsEnumerable());
    }
}
