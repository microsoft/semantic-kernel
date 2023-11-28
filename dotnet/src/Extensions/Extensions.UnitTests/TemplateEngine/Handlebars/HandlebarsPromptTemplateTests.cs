// Copyright (c) Microsoft. All rights reserved.

using System;
using System.ComponentModel;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.TemplateEngine.Handlebars;
using SemanticKernel.Extensions.UnitTests.XunitHelpers;
using Xunit;
using static Microsoft.SemanticKernel.PromptTemplateConfig;

namespace SemanticKernel.Extensions.UnitTests.TemplateEngine.Handlebars;

public sealed class HandlebarsPromptTemplateTests
{
    private readonly HandlebarsPromptTemplateFactory _factory;
    private readonly Kernel _kernel;
    private readonly ContextVariables _variables;

    public HandlebarsPromptTemplateTests()
    {
        this._factory = new HandlebarsPromptTemplateFactory(TestConsoleLogger.LoggerFactory);
        this._kernel = new Kernel();
        this._variables = new ContextVariables(Guid.NewGuid().ToString("X"));
    }

    [Fact]
    public async Task ItRendersVariablesAsync()
    {
        // Arrange
        this._variables.Set("bar", "Bar");
        var template = "Foo {{bar}}";
        var promptConfig = new PromptTemplateConfig() { TemplateFormat = HandlebarsPromptTemplateFactory.HandlebarsTemplateFormat, Template = template };
        var target = (HandlebarsPromptTemplate)this._factory.Create(promptConfig);

        // Act
        var prompt = await target.RenderAsync(this._kernel, this._variables);

        // Assert   
        Assert.Equal("Foo Bar", prompt);
    }

    [Fact]
    public async Task ItRendersFunctionsAsync()
    {
        // Arrange
        this._kernel.ImportPluginFromObject<Foo>();
        var template = "Foo {{Foo_Bar}}";
        var promptConfig = new PromptTemplateConfig() { TemplateFormat = HandlebarsPromptTemplateFactory.HandlebarsTemplateFormat, Template = template };
        var target = (HandlebarsPromptTemplate)this._factory.Create(promptConfig);

        // Act
        var prompt = await target.RenderAsync(this._kernel, this._variables);

        // Assert   
        Assert.Equal("Foo Bar", prompt);
    }

    [Fact]
    public async Task ItRendersAsyncFunctionsAsync()
    {
        // Arrange
        this._kernel.ImportPluginFromObject<Foo>();
        var template = "Foo {{Foo_Bar}} {{Foo_Baz}}";
        var promptConfig = new PromptTemplateConfig() { TemplateFormat = HandlebarsPromptTemplateFactory.HandlebarsTemplateFormat, Template = template };
        var target = (HandlebarsPromptTemplate)this._factory.Create(promptConfig);

        // Act
        var prompt = await target.RenderAsync(this._kernel, this._variables);

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
        promptConfig.InputParameters.Add(new InputParameter()
        {
            Name = "bar",
            Description = "Bar",
            DefaultValue = "Bar"
        });
        promptConfig.InputParameters.Add(new InputParameter()
        {
            Name = "baz",
            Description = "Baz",
            DefaultValue = "Baz"
        });
        promptConfig.Template = "Foo {{bar}} {{baz}}";
        var target = (HandlebarsPromptTemplate)this._factory.Create(promptConfig);

        // Act
        var prompt = await target.RenderAsync(this._kernel, this._variables);

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
