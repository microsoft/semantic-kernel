// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.SemanticKernel.Orchestration;
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
        var target = new BasicPromptTemplateFactory(new MyPromptTemplateFactory());

        // Act
        var result = target.CreatePromptTemplate(templateString, new PromptTemplateConfig() { TemplateFormat = "semantic-kernel" });

        // Assert
        Assert.NotNull(result);
        Assert.True(result is BasicPromptTemplate);
    }

    [Fact]
    public void ItCreatesMyPromptTemplate()
    {
        // Arrange
        var templateString = "{{$input}}";
        var target = new BasicPromptTemplateFactory(new MyPromptTemplateFactory());

        // Act
        var result = target.CreatePromptTemplate(templateString, new PromptTemplateConfig() { TemplateFormat = "my-format" });

        // Assert
        Assert.NotNull(result);
        Assert.True(result is MyPromptTemplate);
    }
}

public class MyPromptTemplateFactory : IPromptTemplateFactory
{
    public IPromptTemplate CreatePromptTemplate(string templateString, PromptTemplateConfig promptTemplateConfig)
    {
        if (promptTemplateConfig.TemplateFormat.Equals("my-format", System.StringComparison.Ordinal))
        {
            return new MyPromptTemplate(templateString, promptTemplateConfig);
        }

        throw new SKException($"Prompt template format {promptTemplateConfig.TemplateFormat} is not supported.");
    }
}

public class MyPromptTemplate : IPromptTemplate
{
    private readonly string _templateString;
    private readonly PromptTemplateConfig _promptTemplateConfig;

    public MyPromptTemplate(string templateString, PromptTemplateConfig promptTemplateConfig)
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
