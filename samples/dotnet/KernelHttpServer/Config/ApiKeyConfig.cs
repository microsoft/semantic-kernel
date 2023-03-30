// Copyright (c) Microsoft. All rights reserved.

namespace KernelHttpServer.Config;

public class ApiKeyConfig
{
    public AIServiceConfig CompletionConfig { get; set; } = new();

    public AIServiceConfig EmbeddingConfig { get; set; } = new();
}
