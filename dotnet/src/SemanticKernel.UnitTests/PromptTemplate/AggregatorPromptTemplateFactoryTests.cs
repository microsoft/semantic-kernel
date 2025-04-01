// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Xunit;

#pragma warning disable CS8767 // Nullability of reference types in type of parameter doesn't match implicitly implemented member (possibly because of nullability attributes).

namespace SemanticKernel.UnitTests.PromptTemplate;

public sealed class AggregatorPromptTemplateFactoryTests
{
    [Fact]
    public void ItCreatesMyPromptTemplates()
    {
        // Arrange
        var templateString = "{{$input}}";
        var promptModel1 = new PromptTemplateConfig() { TemplateFormat = "my-format-1", Template = templateString };
        var promptModel2 = new PromptTemplateConfig() { TemplateFormat = "my-format-2", Template = templateString };
        var target = new AggregatorPromptTemplateFactory(new MyPromptTemplateFactory1(), new MyPromptTemplateFactory2());

        // Act
        var result1 = target.Create(promptModel1);
        var result2 = target.Create(promptModel2);

        // Assert
        Assert.NotNull(result1);
        Assert.True(result1 is MyPromptTemplate1);
        Assert.NotNull(result2);
        Assert.True(result2 is MyPromptTemplate2);
    }

    [Fact]
    public void ItThrowsExceptionForUnknownPromptTemplateFormat()
    {
        // Arrange
        var templateString = "{{$input}}";
        var promptConfig = new PromptTemplateConfig() { TemplateFormat = "unknown-format", Template = templateString };
        var target = new AggregatorPromptTemplateFactory(new MyPromptTemplateFactory1(), new MyPromptTemplateFactory2());

        // Act
        // Assert
        Assert.Throws<KernelException>(() => target.Create(promptConfig));
    }

    [Fact]
    public void ItCreatesPromptFunctionsUsingCorrectFactory()
    {
        // Arrange
        var templateString = "{{$input}}";
        var kernel = new Kernel();
        var factory1 = new MyPromptTemplateFactory1();
        var factory2 = new MyPromptTemplateFactory2();
        var target = new AggregatorPromptTemplateFactory(factory1, factory2);

        // Act
        var function1 = kernel.CreateFunctionFromPrompt(templateString, templateFormat: "my-format-1", promptTemplateFactory: target);
        var function2 = kernel.CreateFunctionFromPrompt(templateString, templateFormat: "my-format-1", promptTemplateFactory: target);

        // Assert
        Assert.NotNull(function1);
        Assert.NotNull(function2);
    }

    [Fact]
    public void ItThrowsExceptionCreatePromptFunctionWithoutFormat()
    {
        // Arrange
        var templateString = "{{$input}}";
        var kernel = new Kernel();
        var factory1 = new MyPromptTemplateFactory1();

        // Act & Assert
        var result = Assert.Throws<ArgumentException>(() => kernel.CreateFunctionFromPrompt(templateString, promptTemplateFactory: factory1));
        Assert.Equal("templateFormat", result.ParamName);
        Assert.Equal("Template format is required when providing a promptTemplateFactory (Parameter 'templateFormat')", result.Message);
    }

    #region private
    private sealed class MyPromptTemplateFactory1 : IPromptTemplateFactory
    {
        public bool TryCreate(PromptTemplateConfig templateConfig, out IPromptTemplate? result)
        {
            if (templateConfig.TemplateFormat.Equals("my-format-1", StringComparison.Ordinal))
            {
                result = new MyPromptTemplate1(templateConfig);
                return true;
            }

            result = null;
            return false;
        }
    }

    private sealed class MyPromptTemplate1(PromptTemplateConfig promptConfig) : IPromptTemplate
    {
        private readonly PromptTemplateConfig _promptModel = promptConfig;

        public Task<string> RenderAsync(Kernel kernel, KernelArguments? arguments = null, CancellationToken cancellationToken = default)
        {
            return Task.FromResult(this._promptModel.Template);
        }
    }

    private sealed class MyPromptTemplateFactory2 : IPromptTemplateFactory
    {
        public bool TryCreate(PromptTemplateConfig templateConfig, out IPromptTemplate? result)
        {
            if (templateConfig.TemplateFormat.Equals("my-format-2", StringComparison.Ordinal))
            {
                result = new MyPromptTemplate2(templateConfig);
                return true;
            }

            result = null;
            return false;
        }
    }

    private sealed class MyPromptTemplate2(PromptTemplateConfig promptConfig) : IPromptTemplate
    {
        private readonly PromptTemplateConfig _promptModel = promptConfig;

        public Task<string> RenderAsync(Kernel kernel, KernelArguments? arguments = null, CancellationToken cancellationToken = default)
        {
            return Task.FromResult(this._promptModel.Template);
        }
    }
    #endregion
}
