// Copyright (c) Microsoft. All rights reserved.
using System.IO;
using SemanticKernel.Process.UnitTests.Runtime;
using Xunit;

namespace Microsoft.SemanticKernel.Process.Runtime.UnitTests;

/// <summary>
/// Unit tests for the <see cref="LocalProcess"/> class.
/// </summary>
public class ProcessMessageTests
{
    /// <summary>
    /// Validates that the <see cref="ProcessMessage"/> can be serialized and deserialized correctly.
    /// </summary>
    [Fact]
    public void VerifySerializeMessageMinimumTest()
    {
        // Arrange
        ProcessMessage message = new("source", "destination", "function", new() { { "key", "value" } });

        // Act & Assert
        this.VerifySerializeMessage(message);
    }

    /// <summary>
    /// Validates that the <see cref="ProcessMessage"/> can be serialized and deserialized correctly.
    /// </summary>
    [Fact]
    public void VerifySerializeMessageAllTest()
    {
        // Arrange
        ProcessMessage message =
            new("source", "destination", "function", new() { { "key", "value" } })
            {
                TargetEventId = "target",
                TargetEventData = 3,
            };

        // Act & Assert
        this.VerifySerializeMessage(message);
    }

    private void VerifySerializeMessage(ProcessMessage source)
    {
        // Act
        using MemoryStream stream = new();
        source.Serialize(stream);
        ProcessMessage? copy1 = stream.Deserialize<ProcessMessage>();

        // Assert
        Assert.NotNull(copy1);
        Assert.Equivalent(source, copy1, strict: true);
    }
}
