// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.PromptTemplates.Handlebars;
using Xunit;

using static Extensions.UnitTests.PromptTemplates.Handlebars.TestUtilities;

namespace SemanticKernel.Extensions.UnitTests.PromptTemplates.Handlebars;

public sealed class HandlebarsPromptTemplateFactoryTests
{
    [Fact]
    public void ItCreatesHandlebarsPromptTemplate()
    {
        // Arrange
        var templateString = "{{input}}";
        var promptConfig = InitializeHbPromptConfig(templateString);
        var target = new HandlebarsPromptTemplateFactory();

        // Act
        var result = target.Create(promptConfig);

        // Assert
        Assert.NotNull(result);
        Assert.True(result is HandlebarsPromptTemplate);
    }

    [Fact]
    public void ItThrowsExceptionForUnknownPromptTemplateFormat()
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
