// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel.Services.Storage.Queue;

public class RabbitMqConfig
{
    public string Host { get; set; } = "";
    public int Port { get; set; } = 0;
    public string Username { get; set; } = "";
    public string Password { get; set; } = "";
}
