// Copyright (c) Microsoft. All rights reserved.

using System;
using System.ComponentModel;
using System.Globalization;
using System.Threading.Tasks;
using HandlebarsDotNet;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.PromptTemplate.Handlebars;
using SemanticKernel.Extensions.UnitTests.XunitHelpers;
using Xunit;
using static Extensions.UnitTests.PromptTemplate.Handlebars.HandlebarsPromptTemplateTestUtils;

namespace SemanticKernel.Extensions.UnitTests.PromptTemplate.Handlebars.Helpers;

public sealed class KernelFunctionHelpersTests
{
    public KernelFunctionHelpersTests()
    {
        this._factory = new(TestConsoleLogger.LoggerFactory);
        this._kernel = new();
        this._arguments = new(Guid.NewGuid().ToString("X"));
    }

    [Fact]
    public async Task ItRendersFunctionsAsync()
    {
        var template = "Foo {{Foo-Bar}}";
        var result = await this.RenderPromptTemplateAsync(template);

        // Assert   
        Assert.Equal("Foo Bar", result);
    }

    [Fact]
    public async Task ItRendersAsyncFunctionsAsync()
    {
        // Arrange and Act
        var template = "Foo {{Foo-Bar}} {{Foo-Baz}}";
        var result = await this.RenderPromptTemplateAsync(template);

        // Assert   
        Assert.Equal("Foo Bar Baz", result);
    }

    [Fact]
    public async Task ItRendersFunctionHelpersWithPositionalArgumentsAsync()
    {
        var template = "{{Foo-Combine \"Bar\" \"Baz\"}}"; // Use positional arguments instead of hashed arguments
        var result = await this.RenderPromptTemplateAsync(template);

        // Assert
        Assert.Equal("BazBar", result);
    }

    [Fact]
    public async Task ItRendersFunctionHelpersWitHashArgumentsAsync()
    {
        // Arrange and Act
        var template = "{{Foo-Combine x=\"Bar\" y=\"Baz\"}}"; // Use positional arguments instead of hashed arguments
        var result = await this.RenderPromptTemplateAsync(template);

        // Assert
        Assert.Equal("BazBar", result);
    }

    [Fact]
    public async Task ShouldThrowExceptionWhenMissingRequiredParameterAsync()
    {
        // Arrange and Act
        var template = "{{Foo-Combine x=\"Bar\"}}";

        // Assert
        var exception = await Assert.ThrowsAsync<KernelException>(() => this.RenderPromptTemplateAsync(template));
        Assert.Matches("Parameter .* is required for function", exception.Message);
    }

    [Fact]
    public async Task ShouldThrowExceptionWhenFunctionHelperHasInvalidParameterTypeAsync()
    {
        // Arrange and Act
        var template = "{{Foo-StringifyInt x=\"twelve\"}}";

        // Assert
        var exception = await Assert.ThrowsAsync<KernelException>(() => this.RenderPromptTemplateAsync(template));
        Assert.Contains("Invalid parameter type", exception.Message, StringComparison.CurrentCultureIgnoreCase);
    }

    [Fact]
    public async Task ShouldThrowExceptionWhenFunctionHelperIsNotDefinedAsync()
    {
        // Arrange and Act
        var template = "{{Foo-Random x=\"random\"}}";

        // Assert
        var exception = await Assert.ThrowsAsync<HandlebarsRuntimeException>(() => this.RenderPromptTemplateAsync(template));
        Assert.Contains("Template references a helper that cannot be resolved", exception.Message, StringComparison.CurrentCultureIgnoreCase);
    }

    private readonly HandlebarsPromptTemplateFactory _factory;
    private readonly Kernel _kernel;
    private readonly KernelArguments _arguments;

    private async Task<string> RenderPromptTemplateAsync(string template)
    {
        this._kernel.ImportPluginFromObject<Foo>();
        var resultConfig = InitializeHbPromptConfig(template);
        var target = (HandlebarsPromptTemplate)this._factory.Create(resultConfig);

        // Act
        var result = await target.RenderAsync(this._kernel, this._arguments);

        return result;
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

        [KernelFunction, Description("Return words concatenated")]
        public string Combine([Description("First word")] string x, [Description("Second word")] string y) => y + x;

        [KernelFunction, Description("Return number as string")]
        public string StringifyInt([Description("Number to stringify")] int x) => x.ToString(CultureInfo.InvariantCulture);
    }
}
