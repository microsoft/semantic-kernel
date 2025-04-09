// Copyright (c) Microsoft. All rights reserved.
using System;
using System.Collections.Generic;
using System.IO;
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
    /// Validates that a <see cref="KernelProcessEvent"/> can be serialized and deserialized correctly
    /// with out an explicit type definition for <see cref="KernelProcessEvent.Data"/>
    /// </summary>
    [Fact]
    public void VerifySerializeEventSingleTest()
    {
        // Arrange, Act & Assert
        VerifyContainerSerialization([new() { Id = "Test", Data = 3 }]);
        VerifyContainerSerialization([new() { Id = "Test", Data = "test" }]);
        VerifyContainerSerialization([new() { Id = "Test", Data = Guid.NewGuid() }]);
        VerifyContainerSerialization([new() { Id = "Test", Data = new int[] { 1, 2, 3, 4 } }]);
        VerifyContainerSerialization([new() { Id = "Test", Data = new ComplexData { Id = "test", Value = 3 } }]);
        VerifyContainerSerialization([new() { Id = "testid", Data = KernelProcessError.FromException(new InvalidOperationException()) }]);
    }

    /// <summary>
    /// Validates that a list <see cref="KernelProcessEvent"/> can be serialized and deserialized correctly
    /// with out varying types assigned to for <see cref="KernelProcessEvent.Data"/>
    /// </summary>
    [Fact]
    public void VerifySerializeEventMixedTest()
    {
        // Arrange, Act & Assert
        VerifyContainerSerialization(
            [
                new() { Id = "Test", Data = 3 },
                new() { Id = "Test", Data = "test" },
                new() { Id = "Test", Data = Guid.NewGuid() },
                new() { Id = "Test", Data = new int[] { 1, 2, 3, 4 } },
                new() { Id = "Test", Data = new ComplexData { Id = "test", Value = 3 } },
                new() { Id = "testid", Data = KernelProcessError.FromException(new InvalidOperationException()) },
            ]);
    }

    /// <summary>
    /// Validates that a list <see cref="KernelProcessEvent"/> can be serialized and deserialized correctly
    /// with out varying types assigned to for <see cref="KernelProcessEvent.Data"/>
    /// </summary>
    [Fact]
    public void VerifyDataContractSerializationTest()
    {
        // Arrange
        KernelProcessEvent[] processEvents =
            [
                new() { Id = "Test", Data = 3 },
                new() { Id = "Test", Data = "test" },
                new() { Id = "Test", Data = Guid.NewGuid() },
                new() { Id = "Test", Data = new int[] { 1, 2, 3, 4 } },
                new() { Id = "Test", Data = new ComplexData { Id = "test", Value = 3 } },
                new() { Id = "testid", Data = KernelProcessError.FromException(new InvalidOperationException()) },
            ];
        List<string> jsonEvents = [];
        foreach (KernelProcessEvent processEvent in processEvents)
        {
            jsonEvents.Add(KernelProcessEventSerializer.ToJson(processEvent));
        }

        // Act
        using MemoryStream stream = new();
        jsonEvents.Serialize(stream);
        stream.Position = 0;

        List<string>? copy = stream.Deserialize<List<string>>();

        // Assert
        Assert.NotNull(copy);

        // Act
        IList<KernelProcessEvent> copiedEvents = KernelProcessEventSerializer.ToKernelProcessEvents(jsonEvents);

        // Assert
        Assert.Equivalent(processEvents, copiedEvents);
    }

    private static void VerifyContainerSerialization(KernelProcessEvent[] processEvents)
    {
        // Arrange
        List<string> jsonEvents = [];
        foreach (KernelProcessEvent processEvent in processEvents)
        {
            jsonEvents.Add(KernelProcessEventSerializer.ToJson(processEvent));
        }

        // Act
        IList<KernelProcessEvent> copiedEvents = KernelProcessEventSerializer.ToKernelProcessEvents(jsonEvents);

        // Assert
        Assert.Equivalent(processEvents, copiedEvents);
    }

    internal sealed class ComplexData
    {
        public string Id { get; init; } = string.Empty;

        public int Value { get; init; }
    }
}
