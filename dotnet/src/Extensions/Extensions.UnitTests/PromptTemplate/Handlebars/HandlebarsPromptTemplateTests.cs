// Copyright (c) Microsoft. All rights reserved.

using System;
using System.ComponentModel;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.PromptTemplate.Handlebars;
using SemanticKernel.Extensions.UnitTests.XunitHelpers;
using Xunit;

#pragma warning disable CA1812 // Uninstantiated internal types

namespace SemanticKernel.Extensions.UnitTests.PromptTemplate.Handlebars;

public sealed class HandlebarsPromptTemplateTests
{
    private readonly HandlebarsPromptTemplateFactory _factory;
    private readonly Kernel _kernel;
    private readonly KernelArguments _arguments;

    public HandlebarsPromptTemplateTests()
    {
        this._factory = new(TestConsoleLogger.LoggerFactory);
        this._kernel = new();
        this._arguments = new() { ["input"] = Guid.NewGuid().ToString("X") };
    }

    [Fact]
    public async Task ItRendersVariablesAsync()
    {
        // Arrange
        this._arguments["bar"] = "Bar";
        var template = "Foo {{bar}}";
        var promptConfig = new PromptTemplateConfig() { TemplateFormat = HandlebarsPromptTemplateFactory.HandlebarsTemplateFormat, Template = template };
        var target = (HandlebarsPromptTemplate)this._factory.Create(promptConfig);

        // Act
        var prompt = await target.RenderAsync(this._kernel, this._arguments);

        // Assert   
        Assert.Equal("Foo Bar", prompt);
    }

    [Fact]
    public async Task ItRendersFunctionsAsync()
    {
        // Arrange
        this._kernel.ImportPluginFromType<Foo>();
        var template = "Foo {{Foo_Bar}}";
        var promptConfig = new PromptTemplateConfig() { TemplateFormat = HandlebarsPromptTemplateFactory.HandlebarsTemplateFormat, Template = template };
        var target = (HandlebarsPromptTemplate)this._factory.Create(promptConfig);

        // Act
        var prompt = await target.RenderAsync(this._kernel, this._arguments);

        // Assert   
        Assert.Equal("Foo Bar", prompt);
    }

    [Fact]
    public async Task ItRendersAsyncFunctionsAsync()
    {
        // Arrange
        this._kernel.ImportPluginFromType<Foo>();
        var template = "Foo {{Foo_Bar}} {{Foo_Baz}}";
        var promptConfig = new PromptTemplateConfig() { TemplateFormat = HandlebarsPromptTemplateFactory.HandlebarsTemplateFormat, Template = template };
        var target = (HandlebarsPromptTemplate)this._factory.Create(promptConfig);

        // Act
        var prompt = await target.RenderAsync(this._kernel, this._arguments);

        // Assert   
        Assert.Equal("Foo Bar Baz", prompt);
    }

    [Fact]
    public async Task ItUsesDefaultValuesAsync()
    {
        // Arrange
        var promptConfig = new PromptTemplateConfig()
        {
            TemplateFormat = HandlebarsPromptTemplateFactory.HandlebarsTemplateFormat
        };
        promptConfig.InputVariables.Add(new InputVariable()
        {
            Name = "bar",
            Description = "Bar",
            Default = "Bar"
        });
        promptConfig.InputVariables.Add(new InputVariable()
        {
            Name = "baz",
            Description = "Baz",
            Default = "Baz"
        });
        promptConfig.Template = "Foo {{bar}} {{baz}}";
        var target = (HandlebarsPromptTemplate)this._factory.Create(promptConfig);

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
