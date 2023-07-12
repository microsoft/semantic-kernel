// Copyright (c) Microsoft. All rights reserved.

namespace KernelHttpServer.Config;

public class ApiKeyConfig
{
    public AIServiceConfig CompletionConfig { get; } = new();

    public AIServiceConfig EmbeddingConfig { get; } = new();
}
