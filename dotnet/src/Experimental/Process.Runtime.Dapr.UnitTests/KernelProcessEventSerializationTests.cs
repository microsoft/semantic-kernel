// Copyright (c) Microsoft. All rights reserved.
using System.Linq;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Process.Runtime;
using Microsoft.SemanticKernel.Process.Serialization;
using Xunit;

namespace SemanticKernel.Process.Dapr.Runtime.UnitTests;

/// <summary>
/// Unit tests for the <see cref="ProcessEvent"/> class.
/// </summary>
public class KernelProcessEventSerializationTests
{
    /// <summary>
    /// Validates that the <see cref="ProcessEvent"/> can be serialized and deserialized correctly.
    /// </summary>
    [Fact]
    public void VerifySerializeEventSingleTest()
    {
        // Arrange, Act & Assert
        KernelProcessEvent processEvent = new() { Id = "Test", Data = 3 };
    }

    private static void VerifyContainerSerialization(KernelProcessEvent[] processEvents)
    {
        // Arrange
        string json = KernelProcessEventSerializer.Write(processEvents);

        // Act
        KernelProcessEvent[] copiedEvents = KernelProcessEventSerializer.Read(json).ToArray();

        // Assert
        Assert.Equivalent(processEvents, copiedEvents);
    }
}
