// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.TemplateEngine;
using Xunit;

namespace SemanticKernel.UnitTests.TemplateEngine;
public sealed class AggregatorPromptTemplateFactoryTests
{
    [Fact]
    public void ItCreatesMyPromptTemplates()
    {
        // Arrange
        var templateString = "{{$input}}";
        var target = new AggregatorPromptTemplateFactory(new MyPromptTemplateFactory1(), new MyPromptTemplateFactory2());

        // Act
        var result1 = target.Create(templateString, new PromptTemplateConfig() { TemplateFormat = "my-format-1" });
        var result2 = target.Create(templateString, new PromptTemplateConfig() { TemplateFormat = "my-format-2" });

        // Assert
        Assert.NotNull(result1);
        Assert.True(result1 is MyPromptTemplate1);
        Assert.NotNull(result2);
        Assert.True(result2 is MyPromptTemplate2);
    }

    [Fact]
    public void ItThrowsExceptionForUnknowPromptTemplateFormat()
    {
        // Arrange
        var templateString = "{{$input}}";
        var target = new AggregatorPromptTemplateFactory(new MyPromptTemplateFactory1(), new MyPromptTemplateFactory2());

        // Act
        var result1 = target.Create(templateString, new PromptTemplateConfig() { TemplateFormat = "my-format-1" });
        var result2 = target.Create(templateString, new PromptTemplateConfig() { TemplateFormat = "my-format-2" });

        // Assert
        Assert.Throws<SKException>(() => target.Create(templateString, new PromptTemplateConfig() { TemplateFormat = "unknown-format" }));
    }

    #region private
    private sealed class MyPromptTemplateFactory1 : IPromptTemplateFactory
    {
        public IPromptTemplate Create(string templateString, PromptTemplateConfig promptTemplateConfig)
        {
            if (promptTemplateConfig.TemplateFormat.Equals("my-format-1", System.StringComparison.Ordinal))
            {
                return new MyPromptTemplate1(templateString, promptTemplateConfig);
            }

            throw new SKException($"Prompt template format {promptTemplateConfig.TemplateFormat} is not supported.");
        }
    }

    private sealed class MyPromptTemplate1 : IPromptTemplate
    {
        private readonly string _templateString;
        private readonly PromptTemplateConfig _promptTemplateConfig;

        public MyPromptTemplate1(string templateString, PromptTemplateConfig promptTemplateConfig)
        {
            this._templateString = templateString;
            this._promptTemplateConfig = promptTemplateConfig;
        }

        public IReadOnlyList<ParameterView> Parameters => Array.Empty<ParameterView>();

        public Task<string> RenderAsync(SKContext executionContext, CancellationToken cancellationToken = default)
        {
            return Task.FromResult(this._templateString);
        }
    }

    private sealed class MyPromptTemplateFactory2 : IPromptTemplateFactory
    {
        public IPromptTemplate Create(string templateString, PromptTemplateConfig promptTemplateConfig)
        {
            if (promptTemplateConfig.TemplateFormat.Equals("my-format-2", System.StringComparison.Ordinal))
            {
                return new MyPromptTemplate2(templateString, promptTemplateConfig);
            }

            throw new SKException($"Prompt template format {promptTemplateConfig.TemplateFormat} is not supported.");
        }
    }

    private sealed class MyPromptTemplate2 : IPromptTemplate
    {
        private readonly string _templateString;
        private readonly PromptTemplateConfig _promptTemplateConfig;

        public MyPromptTemplate2(string templateString, PromptTemplateConfig promptTemplateConfig)
        {
            this._templateString = templateString;
            this._promptTemplateConfig = promptTemplateConfig;
        }

        public IReadOnlyList<ParameterView> Parameters => Array.Empty<ParameterView>();

        public Task<string> RenderAsync(SKContext executionContext, CancellationToken cancellationToken = default)
        {
            return Task.FromResult(this._templateString);
        }
    }
    #endregion
}
