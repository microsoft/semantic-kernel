// Copyright (c) Microsoft. All rights reserved.

namespace KernelHttpServer.Config;

public class ApiKeyConfig
{
    public BackendConfig CompletionConfig { get; set; } = new();

    public BackendConfig EmbeddingConfig { get; set; } = new();
}
