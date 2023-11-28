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
        var promptConfig = new PromptTemplateConfig() { TemplateFormat = HandlebarsPromptTemplateFactory.HandlebarsTemplateFormat, Template = templateString };
        var target = new HandlebarsPromptTemplateFactory();

        // Act
        var result = target.Create(promptConfig);

        // Assert
        Assert.NotNull(result);
        Assert.True(result is HandlebarsPromptTemplate);
    }

    [Fact]
    public void ItThrowsExceptionForUnknowPromptTemplateFormat()
    {
        // Arrange
        var templateString = "{{input}}";
        var promptConfig = new PromptTemplateConfig() { TemplateFormat = "unknown-format", Template = templateString };
        var target = new HandlebarsPromptTemplateFactory();

        // Act
        // Assert
        Assert.Throws<KernelException>(() => target.Create(promptConfig));
    }
}
