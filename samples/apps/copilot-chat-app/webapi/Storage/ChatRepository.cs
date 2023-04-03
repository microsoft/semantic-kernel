// Copyright (c) Microsoft. All rights reserved.

using SKWebApi.Storage;

namespace SKWebApi.Skills;

public class ChatRepository : Repository<Chat>
{
    public ChatRepository(IStorageContext<Chat> storageContext)
        : base(storageContext)
    { }

    public Task<IEnumerable<Chat>> FindByUserId(string userId)
    {
        return Task.FromResult(base._StorageContext.QueryableEntities.Where(e => e.UserId == userId).AsEnumerable());
    }
}
