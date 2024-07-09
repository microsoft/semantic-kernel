// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using Xunit;

namespace SemanticKernel.Connectors.OpenAI.UnitTests.Models;

public sealed class OpenAIFileReferenceTests
{
    [Fact]
    public void CanBeInstantiated()
    {
        // Arrange
        var fileReference = new OpenAIFileReference
        {
            CreatedTimestamp = DateTime.UtcNow,
            FileName = "test.txt",
            Id = "123",
            Purpose = OpenAIFilePurpose.Assistants,
            SizeInBytes = 100
        };
    }
}
