// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.TemplateEngine.Handlebars;
using Xunit;

namespace SemanticKernel.Extensions.UnitTests.TemplateEngine.Handlebars;

public sealed class HandlebarsPromptTemplateFactoryTests
{
    [Fact]
    public void ItCreatesHandlebarsPromptTemplate()
    {
        // Arrange
        var templateString = "{{input}}";
        var target = new HandlebarsPromptTemplateFactory();

        // Act
        var result = target.Create(templateString, new PromptTemplateConfig() { TemplateFormat = HandlebarsPromptTemplateFactory.HandlebarsTemplateFormat });

        // Assert
        Assert.NotNull(result);
        Assert.True(result is HandlebarsPromptTemplate);
    }

    [Fact]
    public void ItThrowsExceptionForUnknowPromptTemplateFormat()
    {
        // Arrange
        var templateString = "{{input}}";
        var target = new HandlebarsPromptTemplateFactory();

        // Act
        // Assert
        Assert.Throws<SKException>(() => target.Create(templateString, new PromptTemplateConfig() { TemplateFormat = "unknown-format" }));
    }
}
