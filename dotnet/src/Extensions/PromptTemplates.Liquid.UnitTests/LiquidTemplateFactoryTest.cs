// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.PromptTemplates.Liquid;
using Xunit;

namespace SemanticKernel.Extensions.PromptTemplates.Liquid.UnitTests;

public class LiquidTemplateFactoryTest
{
    [Fact]
    public void ItThrowsExceptionForUnknownPromptTemplateFormat()
    {
        // Arrange
        var promptConfig = new PromptTemplateConfig("UnknownFormat")
        {
            TemplateFormat = "unknown-format",
        };

        var target = new LiquidPromptTemplateFactory();

        // Act & Assert
        Assert.Throws<KernelException>(() => target.Create(promptConfig));
    }

    [Fact]
    public void ItCreatesLiquidPromptTemplate()
    {
        // Arrange
        var promptConfig = new PromptTemplateConfig("Liquid")
        {
            TemplateFormat = LiquidPromptTemplateFactory.LiquidTemplateFormat,
        };

        var target = new LiquidPromptTemplateFactory();

        // Act
        var result = target.Create(promptConfig);

        // Assert
        Assert.NotNull(result);
        Assert.True(result is LiquidPromptTemplate);
    }
}
