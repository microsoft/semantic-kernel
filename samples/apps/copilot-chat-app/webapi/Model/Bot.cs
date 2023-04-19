// Copyright (c) Microsoft. All rights reserved.

using SemanticKernel.Service.Skills;
using Microsoft.SemanticKernel.Memory;
using SemanticKernel.Service.Config;

namespace SemanticKernel.Service.Model;

public class Bot
{
    public BotSchemaConfig Schema { get; set; } = new BotSchemaConfig();

    public BotConfiguration Configurations { get; set; } = new BotConfiguration();

    public string ChatTitle { get; set; } = string.Empty;

    public List<ChatMessage> ChatHistory { get; set; } = new List<ChatMessage>();

    // TODO: Change from MemoryQueryResult to MemoryRecord
    public List<KeyValuePair<string, List<MemoryQueryResult>>> Embeddings { get; set; } = new List<KeyValuePair<string, List<MemoryQueryResult>>>();
}
