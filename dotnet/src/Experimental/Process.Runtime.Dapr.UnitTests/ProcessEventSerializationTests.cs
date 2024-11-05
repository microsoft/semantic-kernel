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
public class ProcessEventSerializationTests
{
    /// <summary>
    /// Validates that a <see cref="ProcessEvent"/> can be serialized and deserialized correctly
    /// with out an explicit type definition for <see cref="ProcessEvent.Data"/>
    /// </summary>
    [Fact]
    public void VerifySerializeEventSingleTest()
    {
        // Arrange, Act & Assert
        VerifyContainerSerialization([new() { Namespace = "testname", SourceId = "testid", Data = 3 }]);
        VerifyContainerSerialization([new() { Namespace = "testname", SourceId = "testid", Data = "test" }]);
        VerifyContainerSerialization([new() { Namespace = "testname", SourceId = "testid", Data = Guid.NewGuid() }]);
        VerifyContainerSerialization([new() { Namespace = "testname", SourceId = "testid", Data = new int[] { 1, 2, 3, 4 } }]);
        VerifyContainerSerialization([new() { Namespace = "testname", SourceId = "testid", Data = new ComplexData { Value = 3 } }]);
        VerifyContainerSerialization([new() { Namespace = "testname", SourceId = "testid", Data = KernelProcessError.FromException(new InvalidOperationException()) }]);
    }

    /// <summary>
    /// Validates that a list <see cref="ProcessEvent"/> can be serialized and deserialized correctly
    /// with out varying types assigned to for <see cref="ProcessEvent.Data"/>
    /// </summary>
    [Fact]
    public void VerifySerializeEventMixedTest()
    {
        // Arrange, Act & Assert
        VerifyContainerSerialization(
            [
                new() { Namespace = "testname", SourceId = "testid", Data = 3 },
                new() { Namespace = "testname", SourceId = "testid", Data = "test" },
                new() { Namespace = "testname", SourceId = "testid", Data = Guid.NewGuid() },
                new() { Namespace = "testname", SourceId = "testid", Data = new int[] { 1, 2, 3, 4 } },
                new() { Namespace = "testname", SourceId = "testid", Data = new ComplexData { Value = 3 } },
                new() { Namespace = "testname", SourceId = "testid", Data = KernelProcessError.FromException(new InvalidOperationException()) },
            ]);
    }

    /// <summary>
    /// Validates that a list <see cref="ProcessEvent"/> can be serialized and deserialized correctly
    /// with out varying types assigned to for <see cref="ProcessEvent.Data"/>
    /// </summary>
    [Fact]
    public void VerifyDataContractSerializationTest()
    {
        // Arrange
        ProcessEvent[] processEvents =
            [
                new() { Namespace = "testname", SourceId = "testid", Data = 3 },
                new() { Namespace = "testname", SourceId = "testid", Data = "test" },
                new() { Namespace = "testname", SourceId = "testid", Data = Guid.NewGuid() },
                new() { Namespace = "testname", SourceId = "testid", Data = new int[] { 1, 2, 3, 4 } },
                new() { Namespace = "testname", SourceId = "testid", Data = new ComplexData { Value = 3 } },
                new() { Namespace = "testname", SourceId = "testid", Data = KernelProcessError.FromException(new InvalidOperationException()) },
            ];
        List<string> jsonEvents = [];
        foreach (ProcessEvent processEvent in processEvents)
        {
            jsonEvents.Add(ProcessEventSerializer.ToJson(processEvent));
        }

        // Act
        using MemoryStream stream = new();
        jsonEvents.Serialize(stream);
        stream.Position = 0;

        List<string>? copy = stream.Deserialize<List<string>>();

        // Assert
        Assert.NotNull(copy);

        // Act
        IList<ProcessEvent> copiedEvents = ProcessEventSerializer.ToProcessEvents(jsonEvents);

        // Assert
        Assert.Equivalent(processEvents, copiedEvents);
    }

    private static void VerifyContainerSerialization(ProcessEvent[] processEvents)
    {
        // Arrange
        List<string> jsonEvents = [];
        foreach (ProcessEvent processEvent in processEvents)
        {
            jsonEvents.Add(ProcessEventSerializer.ToJson(processEvent));
        }

        // Act
        IList<ProcessEvent> copiedEvents = ProcessEventSerializer.ToProcessEvents(jsonEvents);

        // Assert
        Assert.Equivalent(processEvents, copiedEvents);
    }

    internal sealed class ComplexData
    {
        public string Id { get; init; } = string.Empty;

        public int Value { get; init; }
    }
}
