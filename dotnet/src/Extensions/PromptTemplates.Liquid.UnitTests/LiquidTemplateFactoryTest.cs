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
        var promptConfig = new PromptTemplateConfig("UnknownFormat")
        {
            TemplateFormat = "unknown-format",
        };

        var target = new LiquidPromptTemplateFactory();

        Assert.Throws<KernelException>(() => target.Create(promptConfig));
    }

    [Fact]
    public void ItCreatesLiquidPromptTemplate()
    {
        var promptConfig = new PromptTemplateConfig("Liquid")
        {
            TemplateFormat = LiquidPromptTemplateFactory.LiquidTemplateFormat,
        };

        var target = new LiquidPromptTemplateFactory();

        var result = target.Create(promptConfig);

        Assert.NotNull(result);
        Assert.True(result is LiquidPromptTemplate);
    }
}
