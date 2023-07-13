// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel.Services.Storage.Queue;

public struct QueueOptions
{
    public static QueueOptions PubSub = new() { DequeueEnabled = true };
    public static QueueOptions PublishOnly = new() { DequeueEnabled = false };

    public bool DequeueEnabled { get; set; } = true;

    public QueueOptions()
    {
    }
}
