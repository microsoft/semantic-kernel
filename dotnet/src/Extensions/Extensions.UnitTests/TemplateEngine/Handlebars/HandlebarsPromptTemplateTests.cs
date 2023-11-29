// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.TemplateEngine.Handlebars;
using SemanticKernel.Extensions.UnitTests.XunitHelpers;
using Xunit;
using static Microsoft.SemanticKernel.PromptTemplateConfig;

namespace SemanticKernel.Extensions.UnitTests.TemplateEngine.Handlebars;

public sealed class HandlebarsPromptTemplateTests
{
    private readonly HandlebarsPromptTemplateFactory _factory;
    private readonly Kernel _kernel;
    private readonly IDictionary<string, string> _arguments;

    public HandlebarsPromptTemplateTests()
    {
        this._factory = new HandlebarsPromptTemplateFactory(TestConsoleLogger.LoggerFactory);
        this._kernel = new KernelBuilder().Build();
        this._arguments = new Dictionary<string, string>();
        this._arguments["input"] = Guid.NewGuid().ToString("X");
    }

    [Fact]
    public async Task ItRendersVariablesAsync()
    {
        // Arrange
        this._arguments["bar"] = "Bar";
        var template = "Foo {{bar}}";
        var target = (HandlebarsPromptTemplate)this._factory.Create(template, new PromptTemplateConfig() { TemplateFormat = HandlebarsPromptTemplateFactory.HandlebarsTemplateFormat });

        // Act
        var prompt = await target.RenderAsync(this._kernel, this._arguments);

        // Assert   
        Assert.Equal("Foo Bar", prompt);
    }

    [Fact]
    public async Task ItRendersFunctionsAsync()
    {
        // Arrange
        this._kernel.ImportPluginFromObject<Foo>();
        var template = "Foo {{Foo_Bar}}";
        var target = (HandlebarsPromptTemplate)this._factory.Create(template, new PromptTemplateConfig() { TemplateFormat = HandlebarsPromptTemplateFactory.HandlebarsTemplateFormat });

        // Act
        var prompt = await target.RenderAsync(this._kernel, this._arguments);

        // Assert   
        Assert.Equal("Foo Bar", prompt);
    }

    [Fact]
    public async Task ItRendersAsyncFunctionsAsync()
    {
        // Arrange
        this._kernel.ImportPluginFromObject<Foo>();
        var template = "Foo {{Foo_Bar}} {{Foo_Baz}}";
        var target = (HandlebarsPromptTemplate)this._factory.Create(template, new PromptTemplateConfig() { TemplateFormat = HandlebarsPromptTemplateFactory.HandlebarsTemplateFormat });

        // Act
        var prompt = await target.RenderAsync(this._kernel, this._arguments);

        // Assert   
        Assert.Equal("Foo Bar Baz", prompt);
    }

    [Fact]
    public void ItReturnsParameters()
    {
        // Arrange
        var promptTemplateConfig = new PromptTemplateConfig()
        {
            TemplateFormat = HandlebarsPromptTemplateFactory.HandlebarsTemplateFormat
        };
        promptTemplateConfig.Input.Parameters.Add(new InputParameter()
        {
            Name = "bar",
            Description = "Bar",
            DefaultValue = "Bar"
        });
        promptTemplateConfig.Input.Parameters.Add(new InputParameter()
        {
            Name = "baz",
            Description = "Baz",
            DefaultValue = "Baz"
        });
        var template = "Foo {{Bar}} {{Baz}}";
        var target = (HandlebarsPromptTemplate)this._factory.Create(template, promptTemplateConfig);

        // Act
        var parameters = target.Parameters;

        // Assert   
        Assert.Equal(2, parameters.Count);
    }

    [Fact]
    public async Task ItUsesDefaultValuesAsync()
    {
        // Arrange
        var promptTemplateConfig = new PromptTemplateConfig()
        {
            TemplateFormat = HandlebarsPromptTemplateFactory.HandlebarsTemplateFormat
        };
        promptTemplateConfig.Input.Parameters.Add(new InputParameter()
        {
            Name = "Bar",
            Description = "Bar",
            DefaultValue = "Bar"
        });
        promptTemplateConfig.Input.Parameters.Add(new InputParameter()
        {
            Name = "Baz",
            Description = "Baz",
            DefaultValue = "Baz"
        });
        var template = "Foo {{Bar}} {{Baz}}";
        var target = (HandlebarsPromptTemplate)this._factory.Create(template, promptTemplateConfig);

        // Act
        var prompt = await target.RenderAsync(this._kernel, this._arguments);

        // Assert   
        Assert.Equal("Foo Bar Baz", prompt);
    }

    private sealed class Foo
    {
        [KernelFunction, Description("Return Bar")]
        public string Bar() => "Bar";

        [KernelFunction, Description("Return Baz")]
        public async Task<string> BazAsync()
        {
            await Task.Delay(1000);
            return await Task.FromResult("Baz");
        }
    }
}
