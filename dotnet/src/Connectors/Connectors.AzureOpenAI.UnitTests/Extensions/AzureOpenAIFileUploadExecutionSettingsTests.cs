// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.Connectors.AzureOpenAI;

namespace SemanticKernel.Connectors.AzureOpenAI.UnitTests.Extensions;

public class AzureOpenAIFileUploadExecutionSettingsTests
{
    [Fact]
    public void ItCanCreateAzureOpenAIFileUploadExecutionSettings()
    {
        // Arrange
        var fileName = "file.txt";
        var purpose = AzureOpenAIFileUploadPurpose.FineTune;

        // Act
        var settings = new AzureOpenAIFileUploadExecutionSettings(fileName, purpose);

        // Assert
        Assert.Equal(fileName, settings.FileName);
        Assert.Equal(purpose, settings.Purpose);
    }
}
