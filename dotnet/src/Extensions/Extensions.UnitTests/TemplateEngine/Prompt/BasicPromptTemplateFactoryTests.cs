// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.TemplateEngine;
using Microsoft.SemanticKernel.TemplateEngine.Basic;
using Xunit;

namespace SemanticKernel.Extensions.UnitTests.TemplateEngine.Prompt;

public sealed class BasicPromptTemplateFactoryTests
{
    [Fact]
    public void ItCreatesBasicPromptTemplateByDefault()
    {
        // Arrange
        var templateString = "{{$input}}";
        var target = new BasicPromptTemplateFactory();

        // Act
        var result = target.CreatePromptTemplate(templateString, new PromptTemplateConfig());

        // Assert
        Assert.NotNull(result);
        Assert.True(result is BasicPromptTemplate);
    }

    [Fact]
    public void ItCreatesBasicPromptTemplate()
    {
        // Arrange
        var templateString = "{{$input}}";
        var target = new BasicPromptTemplateFactory();

        // Act
        var result = target.CreatePromptTemplate(templateString, new PromptTemplateConfig() { TemplateFormat = "semantic-kernel" });

        // Assert
        Assert.NotNull(result);
        Assert.True(result is BasicPromptTemplate);
    }

    [Fact]
    public void ItReturnsNullForUnknowPromptTemplateFormat()
    {
        // Arrange
        var templateString = "{{$input}}";
        var target = new BasicPromptTemplateFactory();

        // Act
        var result = target.CreatePromptTemplate(templateString, new PromptTemplateConfig() { TemplateFormat = "unknown-format" });

        // Assert
        Assert.Null(result);
    }
}
