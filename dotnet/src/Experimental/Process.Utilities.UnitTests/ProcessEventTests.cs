// Copyright (c) Microsoft. All rights reserved.
using System.IO;
using System.Runtime.Serialization;
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

    [DataContract]
    internal sealed class ComplexData
    {
        [DataMember]
        public string Id { get; init; } = string.Empty;

        [DataMember]
        public int Value { get; init; }
    }
}
