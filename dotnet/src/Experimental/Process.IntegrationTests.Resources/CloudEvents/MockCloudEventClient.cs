// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;

namespace SemanticKernel.Process.IntegrationTests.CloudEvents;
public class MockCloudEventClient : IExternalKernelProcessMessageChannel
{
    /// <summary>
    /// Initialization counter for testing
    /// </summary>
    public int InitializationCounter { get; set; } = 0;
    /// <summary>
    /// Uninitialization counter for testing
    /// </summary>
    public int UninitializationCounter { get; set; } = 0;
    /// <summary>
    /// Captures cloud events emitted for testing
    /// </summary>
    public List<MockCloudEventData> CloudEvents { get; set; }

    private static MockCloudEventClient? s_instance = null;

    public MockCloudEventClient()
    {
        this.CloudEvents = [];
    }

    public static MockCloudEventClient? Instance
    {
        get
        {
            return s_instance ??= new MockCloudEventClient();
        }
    }

    /// <inheritdoc/>
    public Task EmitExternalEventAsync(string externalTopicEvent, object? eventData)
    {
        this.CloudEvents.Add(new() { TopicName = externalTopicEvent, Data = (string)eventData });
        return Task.CompletedTask;
    }

    /// <inheritdoc/>
    public ValueTask Initialize()
    {
        this.InitializationCounter++;
        return ValueTask.CompletedTask;
    }

    /// <inheritdoc/>
    public ValueTask Uninitialize()
    {
        this.UninitializationCounter++;
        return ValueTask.CompletedTask;
    }
}
