// Copyright (c) Microsoft. All rights reserved.
using System;
using System.IO;
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
            ];
        string json = KernelProcessEventSerializer.Write(processEvents);

        // Act
        using MemoryStream stream = new();
        json.Serialize(stream);
        stream.Position = 0;

        string? copy = stream.Deserialize<string>();

        // Assert
        Assert.NotNull(copy);

        // Act
        KernelProcessEvent[] copiedEvents = KernelProcessEventSerializer.Read(copy).ToArray();

        // Assert
        Assert.Equivalent(processEvents, copiedEvents);
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

    internal sealed class ComplexData
    {
        public string Id { get; init; } = string.Empty;

        public int Value { get; init; }
    }
}
