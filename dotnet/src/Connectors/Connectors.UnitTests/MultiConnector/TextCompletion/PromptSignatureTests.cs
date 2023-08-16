// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using Microsoft.SemanticKernel.AI.TextCompletion;
using Microsoft.SemanticKernel.Connectors.AI.MultiConnector;
using Microsoft.SemanticKernel.Connectors.AI.MultiConnector.PromptSettings;
using Xunit;

namespace SemanticKernel.Connectors.UnitTests.MultiConnector.TextCompletion;

public class PromptSignatureTests
{
    [Fact]
    public void TestExtractFromPromptWithShortPromptThrowsArgumentException()
    {
        // Arrange
        var completionJob = new CompletionJob("short", new CompleteRequestSettings());
        var promptMultiConnectorSettingsCollection = new List<PromptMultiConnectorSettings>(); // Example collection

        // Act & Assert
        Assert.Throws<ArgumentException>(() =>
            PromptSignature.ExtractFromPrompt(completionJob, promptMultiConnectorSettingsCollection, 10)
        );
    }

    [Fact]
    public void TestExtractFrom2InstancesWithDifferentPromptsReturnsCommonPrefix()
    {
        // Arrange
        var prompt1 = "Hello, this is a";
        var prompt2 = "Hello, that was a";
        var settings = new CompleteRequestSettings();

        // Act
        var signature = PromptSignature.ExtractFrom2Instances(prompt1, prompt2, settings);

        // Assert
        Assert.Equal("Hello, th", signature.PromptStart);
    }

    [Fact]
    public void TestGeneratePromptLogWithShortPromptReturnsSamePrompt()
    {
        // Arrange
        var prompt = "Hello!";
        var truncationLength = 5;

        // Act
        var result = PromptSignature.GeneratePromptLog(prompt, truncationLength, "{0}...{1}", false);

        // Assert
        Assert.Equal("Hello!", result);
    }

    [Fact]
    public void TestMatchesWithMatchingCompletionJobReturnsTrue()
    {
        // Arrange
        var signature = new PromptSignature
        {
            PromptStart = "Hello, ",
            RequestSettings = new CompleteRequestSettings() // You can set specific properties.
        };

        var completionJob = new CompletionJob("Hello, this is a test.", new CompleteRequestSettings());

        // Act
        var isMatch = signature.Matches(completionJob);

        // Assert
        Assert.True(isMatch);
    }

    // More tests can be added to cover other methods and scenarios.
}
