// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.Connectors.OpenAI;
using OpenAI.Files;
using Xunit;

namespace SemanticKernel.Connectors.OpenAI.UnitTests.Extensions;

public class OpenAIFileUploadExecutionSettingsTests
{
    [Fact]
    public void ItCanCreateOpenAIFileUploadExecutionSettings()
    {
        // Arrange
        var fileName = "file.txt";
        var purpose = FileUploadPurpose.FineTune;

        // Act
        var settings = new OpenAIFileUploadExecutionSettings(fileName, purpose);

        // Assert
        Assert.Equal(fileName, settings.FileName);
        Assert.Equal(purpose, settings.Purpose);
    }
}
