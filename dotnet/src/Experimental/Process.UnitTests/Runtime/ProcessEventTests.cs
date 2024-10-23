// Copyright (c) Microsoft. All rights reserved.
using System.IO;
using SemanticKernel.Process.UnitTests.Runtime;
using Xunit;

namespace Microsoft.SemanticKernel.Process.Runtime.UnitTests;

/// <summary>
/// Unit tests for the <see cref="LocalProcess"/> class.
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
        ProcessEvent source = new("test", new KernelProcessEvent { Id = "1" });

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
        ProcessEvent source = new("test", new KernelProcessEvent { Id = "1", Data = 1, Visibility = KernelProcessEventVisibility.Public });

        // Act & Assert
        this.VerifySerializeEvent(source);
    }

    private void VerifySerializeEvent(ProcessEvent source)
    {
        // Act
        using MemoryStream stream = new();
        source.Serialize(stream);
        ProcessEvent? copy1 = stream.Deserialize<ProcessEvent>();

        // Assert
        Assert.NotNull(copy1);
        Assert.Equal(source, copy1); // record type evaluates logical equality
    }
}
