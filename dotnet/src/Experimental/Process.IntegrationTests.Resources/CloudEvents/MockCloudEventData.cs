// Copyright (c) Microsoft. All rights reserved.

namespace SemanticKernel.Process.IntegrationTests.CloudEvents;

/// <summary>
/// Mock cloud event data used for testing purposes only
/// </summary>
public class MockCloudEventData
{
    /// <summary>
    /// Name of the mock topic
    /// </summary>
    public required string TopicName { get; set; }

    /// <summary>
    /// Data emitted in the mock cloud event
    /// </summary>
    public string? Data { get; set; }
}
