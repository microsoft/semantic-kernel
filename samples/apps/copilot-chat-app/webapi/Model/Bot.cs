// Copyright (c) Microsoft. All rights reserved.

using SKWebApi.Skills;
using Microsoft.SemanticKernel.Memory;

namespace SemanticKernel.Service.Model;

public class Bot
{
    // TODO: Chat configuation

    public IEnumerable<ChatMessage> ChatHistory { get; set; } = Enumerable.Empty<ChatMessage>();

    // TODO: Change from MemoryQueryResult to MemoryRecord
    public IEnumerable<KeyValuePair<string, IEnumerable<MemoryQueryResult>>> Embeddings { get; set; } = Enumerable.Empty<KeyValuePair<string, IEnumerable<MemoryQueryResult>>>();
}
