// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Threading.Tasks;
using HandlebarsDotNet;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.PromptTemplates.Handlebars;
using Xunit;
using static Extensions.UnitTests.PromptTemplates.Handlebars.TestUtilities;

namespace SemanticKernel.Extensions.UnitTests.PromptTemplates.Handlebars;

public sealed class HandlebarsPromptTemplateTests
{
    public HandlebarsPromptTemplateTests()
    {
        this._factory = new();
        this._kernel = new();
        this._arguments = new() { ["input"] = Guid.NewGuid().ToString("X") };
    }

    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public void ItInitializesHandlebarsPromptTemplateInstanceCorrectly(bool includeOptions)
    {
        // Arrange & Act
        var template = includeOptions ?
            new HandlebarsPromptTemplate(new()) :
            new HandlebarsPromptTemplate(new(), new());

        // Assert
        Assert.NotNull(template);
    }

    [Fact]
    public async Task ItRendersVariablesAsync()
    {
        // Arrange
        var template = "Foo {{bar}}";
        var promptConfig = InitializeHbPromptConfig(template);
        var target = (HandlebarsPromptTemplate)this._factory.Create(promptConfig);
        this._arguments["bar"] = "Bar";

        // Act
        var prompt = await target.RenderAsync(this._kernel, this._arguments);

        // Assert   
        Assert.Equal("Foo Bar", prompt);
    }

    [Fact]
    public async Task ItUsesDefaultValuesAsync()
    {
        // Arrange
        var template = "Foo {{bar}} {{baz}}{{null}}{{empty}}";
        var promptConfig = InitializeHbPromptConfig(template);

        promptConfig.InputVariables.Add(new() { Name = "bar", Description = "Bar", Default = "Bar" });
        promptConfig.InputVariables.Add(new() { Name = "baz", Description = "Baz", Default = "Baz" });
        promptConfig.InputVariables.Add(new() { Name = "null", Description = "Null", Default = null });
        promptConfig.InputVariables.Add(new() { Name = "empty", Description = "empty", Default = string.Empty });

        var target = (HandlebarsPromptTemplate)this._factory.Create(promptConfig);

        // Act
        var prompt = await target.RenderAsync(this._kernel, this._arguments);

        // Assert   
        Assert.Equal("Foo Bar Baz", prompt);
    }

    [Fact]
    public async Task ItRendersNestedFunctionsAsync()
    {
        // Arrange
        this._kernel.ImportPluginFromObject(new Foo());
        var template = "Foo {{Foo-Bar}} {{Foo-Baz}} {{Foo-Qux (Foo-Bar)}}";
        var promptConfig = InitializeHbPromptConfig(template);
        var target = (HandlebarsPromptTemplate)this._factory.Create(promptConfig);

        // Act
        var prompt = await target.RenderAsync(this._kernel, this._arguments);

        // Assert   
        Assert.Equal("Foo Bar Baz QuxBar", prompt);
    }

    [Fact]
    public async Task ItRendersConditionalStatementsAsync()
    {
        // Arrange
        var template = "Foo {{#if bar}}{{bar}}{{else}}No Bar{{/if}}";
        var promptConfig = InitializeHbPromptConfig(template);
        var target = (HandlebarsPromptTemplate)this._factory.Create(promptConfig);

        // Act on positive case
        this._arguments["bar"] = "Bar";
        var prompt = await target.RenderAsync(this._kernel, this._arguments);

        // Assert   
        Assert.Equal("Foo Bar", prompt);

        // Act on negative case
        this._arguments.Remove("bar");
        prompt = await target.RenderAsync(this._kernel, this._arguments);

        // Assert   
        Assert.Equal("Foo No Bar", prompt);
    }

    [Fact]
    public async Task ItRendersLoopsAsync()
    {
        // Arrange
        var template = "List: {{#each items}}{{this}}{{/each}}";
        var promptConfig = InitializeHbPromptConfig(template);
        var target = (HandlebarsPromptTemplate)this._factory.Create(promptConfig);
        this._arguments["items"] = new List<string> { "item1", "item2", "item3" };

        // Act
        var prompt = await target.RenderAsync(this._kernel, this._arguments);

        // Assert   
        Assert.Equal("List: item1item2item3", prompt);
    }

    [Fact]
    public async Task ItRegistersCustomHelpersAsync()
    {
        // Arrange
        var template = "Custom: {{customHelper}}";
        var promptConfig = InitializeHbPromptConfig(template);

        var options = new HandlebarsPromptTemplateOptions
        {
            RegisterCustomHelpers = (registerHelper, options, variables) =>
            {
                registerHelper("customHelper", (Context context, Arguments arguments) =>
                {
                    return "Custom Helper Output";
                });
            }
        };

        this._factory = new HandlebarsPromptTemplateFactory(options);
        var target = (HandlebarsPromptTemplate)this._factory.Create(promptConfig);

        // Act
        var prompt = await target.RenderAsync(this._kernel, this._arguments);

        // Assert   
        Assert.Equal("Custom: Custom Helper Output", prompt);
    }

    #region private

    private HandlebarsPromptTemplateFactory _factory;
    private readonly Kernel _kernel;
    private readonly KernelArguments _arguments;

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

        [KernelFunction, Description("Return Qux")]
        public async Task<string> QuxAsync(string input)
        {
            await Task.Delay(1000);
            return await Task.FromResult($"Qux{input}");
        }
    }

    #endregion
}
