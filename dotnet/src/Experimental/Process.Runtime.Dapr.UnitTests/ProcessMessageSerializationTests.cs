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
/// Unit tests for the <see cref="ProcessMessage"/> class.
/// </summary>
public class ProcessMessageSerializationTests
{
    /// <summary>
    /// Validates that a <see cref="ProcessMessage"/> can be serialized and deserialized correctly
    /// with out an explicit type definition for <see cref="ProcessMessage.Values"/>
    /// </summary>
    [Fact]
    public void VerifySerializeMessageSingleTest()
    {
        // Arrange, Act & Assert
        VerifyContainerSerialization([CreateMessage(new() { { "Data", 3 } })]);
        VerifyContainerSerialization([CreateMessage(new() { { "Data", "test" } })]);
        VerifyContainerSerialization([CreateMessage(new() { { "Data", Guid.NewGuid() } })]);
        VerifyContainerSerialization([CreateMessage(new() { { "Data", new int[] { 1, 2, 3, 4 } } })]);
        VerifyContainerSerialization([CreateMessage(new() { { "Data", new ComplexData { Value = 3 } } })]);
        VerifyContainerSerialization([CreateMessage(new() { { "Data", KernelProcessError.FromException(new InvalidOperationException()) } })]);
    }

    /// <summary>
    /// Validates that a list <see cref="ProcessEvent"/> can be serialized and deserialized correctly
    /// with out varying types assigned to for <see cref="ProcessMessage.Values"/>
    /// </summary>
    [Fact]
    public void VerifySerializeMessageMixedTest()
    {
        // Arrange, Act & Assert
        VerifyContainerSerialization(
            [
                CreateMessage(new() { { "Data", 3 } }),
                CreateMessage(new() { { "Data", "test" } }),
                CreateMessage(new() { { "Data", Guid.NewGuid() } }),
                CreateMessage(new() { { "Data", new int[] { 1, 2, 3, 4 } } }),
                CreateMessage(new() { { "Data", new ComplexData { Value = 3 } } }),
                CreateMessage(new() { { "Data", KernelProcessError.FromException(new InvalidOperationException()) } }),
            ]);
    }

    /// <summary>
    /// Validates that a list <see cref="ProcessEvent"/> can be serialized and deserialized correctly
    /// with out varying types assigned to for <see cref="ProcessMessage.Values"/>
    /// </summary>
    [Fact]
    public void VerifySerializeMessageManyTest()
    {
        // Arrange, Act & Assert
        VerifyContainerSerialization(
            [
                CreateMessage(new() {
                    { "Data1", 3 },
                    { "Data2", "test" },
                    { "Data3", Guid.NewGuid() },
                    { "Data4", new int[] { 1, 2, 3, 4 } },
                    { "Data5", new ComplexData { Value = 3 } },
                    { "Data6", KernelProcessError.FromException(new InvalidOperationException()) } })
            ]);
    }

    /// <summary>
    /// Validates that a list <see cref="ProcessMessage"/> can be serialized and deserialized correctly
    /// with out varying types assigned to for <see cref="ProcessMessage.Values"/>
    /// </summary>
    [Fact]
    public void VerifyDataContractSerializationTest()
    {
        // Arrange
        ProcessMessage[] processMessages =
            [
                CreateMessage(new() { { "Data", 3 } }),
                CreateMessage(new() { { "Data", "test" } }),
                CreateMessage(new() { { "Data", Guid.NewGuid() } }),
                CreateMessage(new() { { "Data", new int[] { 1, 2, 3, 4 } } }),
                CreateMessage(new() { { "Data", new ComplexData { Value = 3 } } }),
                CreateMessage(new() { { "Data", KernelProcessError.FromException(new InvalidOperationException()) } }),
            ];
        List<string> jsonEvents = [];
        foreach (ProcessMessage processMessage in processMessages)
        {
            jsonEvents.Add(ProcessMessageSerializer.ToJson(processMessage));
        }

        // Act
        using MemoryStream stream = new();
        jsonEvents.Serialize(stream);
        stream.Position = 0;

        List<string>? copy = stream.Deserialize<List<string>>();

        // Assert
        Assert.NotNull(copy);

        // Act
        IList<ProcessMessage> copiedEvents = ProcessMessageSerializer.ToProcessMessages(jsonEvents);

        // Assert
        Assert.Equivalent(processMessages, copiedEvents);
    }

    private static void VerifyContainerSerialization(ProcessMessage[] processMessages)
    {
        // Arrange
        List<string> jsonEvents = [];
        foreach (ProcessMessage processMessage in processMessages)
        {
            jsonEvents.Add(ProcessMessageSerializer.ToJson(processMessage));
        }

        // Act
        IList<ProcessMessage> copiedEvents = ProcessMessageSerializer.ToProcessMessages(jsonEvents);

        // Assert
        Assert.Equivalent(processMessages, copiedEvents);
    }

    private static ProcessMessage CreateMessage(Dictionary<string, object?> values)
    {
        return new ProcessMessage("test-source", "test-destination", "test-function", values)
        {
            TargetEventData = "testdata",
            TargetEventId = "targetevent",
        };
    }

    internal sealed class ComplexData
    {
        public string Id { get; init; } = string.Empty;

        public int Value { get; init; }
    }
}
