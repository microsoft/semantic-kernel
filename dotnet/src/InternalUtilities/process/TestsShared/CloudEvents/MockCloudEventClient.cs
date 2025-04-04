// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;

namespace SemanticKernel.Process.TestsShared.CloudEvents;
/// <summary>
/// Class used for testing purposes to mock emitting external cloud events
/// </summary>
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
    public List<KernelProcessProxyMessage> CloudEvents { get; set; } = [];

    private static MockCloudEventClient? s_instance = null;

    /// <summary>
    /// Instance of <see cref="MockCloudEventClient"/> when used as singleton
    /// </summary>
    public static MockCloudEventClient Instance
    {
        get
        {
            return s_instance ??= new MockCloudEventClient();
        }
    }

    /// <summary>
    /// For testing purposes reset public properties
    /// </summary>
    public void Reset()
    {
        this.InitializationCounter = 0;
        this.UninitializationCounter = 0;
        this.CloudEvents.Clear();
    }

    /// <inheritdoc/>
    public Task EmitExternalEventAsync(string externalTopicEvent, KernelProcessProxyMessage message)
    {
        if (message != null)
        {
            this.CloudEvents.Add(message);
        }

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
