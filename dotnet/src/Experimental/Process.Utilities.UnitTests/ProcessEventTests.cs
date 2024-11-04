// Copyright (c) Microsoft. All rights reserved.
using System.Collections.Generic;
using System.IO;
using System.Runtime.Serialization;
using System.Text.Json;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Process.Runtime;
using Xunit;

namespace SemanticKernel.Process.Utilities.UnitTests;

/// <summary>
/// Unit tests for the <see cref="ProcessEvent"/> class.
/// </summary>
public class ProcessEventTests
{
    /// <summary>
    /// Validates that the <see cref="ProcessEvent"/> can be serialized and deserialized correctly.
    /// </summary>
    [Fact]
    public void VerifySerializeEventMinimumTest()
    {
        // Arrange
        ProcessEvent source = new KernelProcessEvent { Id = "1" }.ToProcessEvent("test");

        // Act & Assert
        this.VerifySerializeEvent(source);
    }

    /// <summary>
    /// Validates that the <see cref="ProcessEvent"/> can be serialized and deserialized correctly.
    /// </summary>
    [Fact]
    public void VerifySerializeEventAllTest()
    {
        // Arrange
        ProcessEvent source = new KernelProcessEvent { Id = "1", Data = 1, Visibility = KernelProcessEventVisibility.Public }.ToProcessEvent("test");

        // Act & Assert
        this.VerifySerializeEvent(source);
    }

    /// <summary>
    /// Validates that the <see cref="ProcessEvent"/> can be serialized and deserialized correctly.
    /// </summary>
    [Fact]
    public void VerifySerializeEventComplexTest()
    {
        // Arrange
        ComplexData data = new() { Id = "test", Value = 33 };
        ProcessEvent source = new KernelProcessEvent { Id = "1", Data = data, Visibility = KernelProcessEventVisibility.Public }.ToProcessEvent("test");

        // Act & Assert
        this.VerifySerializeEvent(source);
    }

    /// <summary>
    /// Validates that the <see cref="ProcessEvent"/> can be serialized and deserialized correctly.
    /// </summary>
    [Fact]
    public void VerifySerializeEventCollectionTest()
    {
        // Arrange
        int[] data = [1, 2, 3, 4, 5];
        ProcessEvent source = new KernelProcessEvent { Id = "1", Data = data, Visibility = KernelProcessEventVisibility.Public }.ToProcessEvent("test");

        // Act & Assert
        this.VerifySerializeEvent(source);
    }

    private static readonly JsonSerializerOptions s_options = new() { WriteIndented = true };

    /// <summary>
    /// Validates that the <see cref="ProcessEvent"/> can be serialized and deserialized correctly.
    /// </summary>
    [Fact]
    public void VerifySerializeCollectionOfEventsTest()
    {
        // Arrange
        ComplexData data = new() { Id = "test", Value = 33 };
        ProcessEvent[] processEvents = [
            new KernelProcessEvent { Id = "1", Data = 1 }.ToProcessEvent("test"),
            new KernelProcessEvent { Id = "1", Data = "test"}.ToProcessEvent("test"),
            new KernelProcessEvent { Id = "1", Data = data}.ToProcessEvent("test"),
        ];

        // Act
        string json = JsonSerializer.Serialize(processEvents, s_options);
        // Assert
    }

    /// <summary>
    /// Validates that the <see cref="ProcessEvent"/> can be serialized and deserialized correctly.
    /// </summary>
    [Fact]
    public void VerifySerializeCollectionOfKernelEventsTest()
    {
        // Arrange
        ComplexData data = new() { Id = "test", Value = 33 };
        KernelProcessEvent[] processEvents = [
            new KernelProcessEvent { Id = "1", Data = 1 },
            new KernelProcessEvent { Id = "1", Data = "test"},
            new KernelProcessEvent { Id = "1", Data = data},
        ];

        // Act
        string json = JsonSerializer.Serialize(processEvents, s_options);
        // Assert
    }

    /// <summary>
    /// Validates that the <see cref="ProcessEvent"/> can be serialized and deserialized correctly.
    /// </summary>
    [Fact]
    public void VerifySerializeCollectionOfMessagesTest()
    {
        // Arrange
        ComplexData data = new() { Id = "test", Value = 33 };
        ProcessMessage[] processEvents = [
            new ProcessMessage("testsource", "testdestination", "testfunction", new Dictionary<string, object?>() { { "data", 123 } }),
            new ProcessMessage("testsource", "testdestination", "testfunction", new Dictionary<string, object?>() { { "text", "testext" } }),
            new ProcessMessage("testsource", "testdestination", "testfunction", new Dictionary<string, object?>() { { "data", data } }),
        ];

        // Act
        string json = JsonSerializer.Serialize(processEvents, s_options);
        // Assert
    }

    private void VerifySerializeEvent(ProcessEvent source)
    {
        // Act
        using MemoryStream stream = new();
        source.Serialize(stream);
        ProcessEvent? copy1 = stream.Deserialize<ProcessEvent>(source.GetType());

        // Assert
        Assert.NotNull(copy1);
        Assert.Equivalent(source, copy1); // record type evaluates logical equality
    }

    //private void VerifySerializeEvent<TData>(ProcessEvent<TData> source)
    //{
    //    // Act
    //    using MemoryStream stream = new();
    //    source.Serialize(stream);
    //    ProcessEvent<TData>? copy1 = stream.Deserialize<ProcessEvent<TData>>();

    //    // Assert
    //    Assert.NotNull(copy1);
    //    Assert.Equivalent(source, copy1); // record type evaluates logical equality
    //}

    [DataContract]
    internal sealed class ComplexData
    {
        [DataMember]
        public string Id { get; init; } = string.Empty;

        [DataMember]
        public int Value { get; init; }
    }
}
