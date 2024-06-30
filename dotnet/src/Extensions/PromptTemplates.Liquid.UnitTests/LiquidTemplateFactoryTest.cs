// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.PromptTemplates.Liquid;
using Xunit;

namespace SemanticKernel.Extensions.PromptTemplates.Liquid.UnitTests;

public class LiquidTemplateFactoryTest
{
    [Theory]
    [InlineData("unknown-format")]
    [InlineData(null)]
    public void ItThrowsExceptionForUnknownPromptTemplateFormat(string? format)
    {
        // Arrange
        var promptConfig = new PromptTemplateConfig("UnknownFormat")
        {
            TemplateFormat = format,
        };

        var target = new LiquidPromptTemplateFactory();

        // Act & Assert
        Assert.False(target.TryCreate(promptConfig, out IPromptTemplate? result));
        Assert.Null(result);
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
        Assert.IsType<LiquidPromptTemplate>(result);
    }
}
