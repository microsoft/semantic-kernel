// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Threading.Tasks;
using SemanticKernel.Service.CopilotChat.Models;

namespace SemanticKernel.Service.CopilotChat.Storage;

/// <summary>
/// A repository for chat messages.
/// </summary>
public class ChatMemorySourceRepository : Repository<MemorySource>
{
    /// <summary>
    /// Initializes a new instance of the ChatMemorySourceRepository class.
    /// </summary>
    /// <param name="storageContext">The storage context.</param>
    public ChatMemorySourceRepository(IStorageContext<MemorySource> storageContext)
        : base(storageContext)
    {
    }

    /// <summary>
    /// Finds chat memory sources by chat session id
    /// </summary>
    /// <param name="chatId">The chat session id.</param>
    /// <param name="includeGlobal">Flag specifying if global documents should be included in the response.</param>
    /// <returns>A list of memory sources.</returns>
    public Task<IEnumerable<MemorySource>> FindByChatIdAsync(string chatId, bool includeGlobal = true)
    {
        return base.StorageContext.QueryEntitiesAsync(e => e.ChatId == chatId || (includeGlobal && e.ChatId == Guid.Empty.ToString()));
    }

    /// <summary>
    /// Finds chat memory sources by name
    /// </summary>
    /// <param name="name">Name</param>
    /// <returns>A list of memory sources with the given name.</returns>
    public Task<IEnumerable<MemorySource>> FindByNameAsync(string name)
    {
        return base.StorageContext.QueryEntitiesAsync(e => e.Name.Equals(name, StringComparison.OrdinalIgnoreCase));
    }
}
