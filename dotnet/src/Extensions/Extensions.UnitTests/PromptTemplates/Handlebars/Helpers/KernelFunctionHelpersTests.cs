// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Globalization;
using System.Threading.Tasks;
using HandlebarsDotNet;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.PromptTemplates.Handlebars;
using Xunit;
using static Extensions.UnitTests.PromptTemplates.Handlebars.TestUtilities;

namespace SemanticKernel.Extensions.UnitTests.PromptTemplates.Handlebars.Helpers;

public sealed class KernelFunctionHelpersTests
{
    public KernelFunctionHelpersTests()
    {
        this._factory = new();
        this._kernel = new();
        this._arguments = new() { ["input"] = Guid.NewGuid().ToString("X") };
    }

    [Fact]
    public async Task ItRendersFunctionsAsync()
    {
        // Arrange and Act
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
        // Arrange and Act
        var template = """{{Foo-Combine "Bar" "Baz"}}"""; // Use positional arguments instead of hashed arguments
        var result = await this.RenderPromptTemplateAsync(template);

        // Assert
        Assert.Equal("BazBar", result);
    }

    [Fact]
    public async Task ItThrowsExceptionWhenPositionalArgumentHasInvalidTypeAsync()
    {
        // Arrange
        var template = "{{Foo-StringifyInt \"twelve\"}}";

        // Act and Assert
        var exception = await Assert.ThrowsAsync<KernelException>(() => this.RenderPromptTemplateAsync(template));

        Assert.Contains("Invalid parameter type for function", exception.Message, StringComparison.OrdinalIgnoreCase);
    }

    [Fact]
    public async Task ItThrowsExceptionWhenPositionalArgumentNumberIsIncorrectAsync()
    {
        // Arrange
        var template = "{{Foo-Combine \"Bar\"}}";

        // Act and Assert
        var exception = await Assert.ThrowsAsync<KernelException>(() => this.RenderPromptTemplateAsync(template));

        Assert.Contains("Invalid parameter count for function", exception.Message, StringComparison.OrdinalIgnoreCase);
    }

    [Fact]
    public async Task ItRendersFunctionHelpersWitHashArgumentsAsync()
    {
        // Arrange and Act
        var template = """{{Foo-Combine x="Bar" y="Baz"}}"""; // Use positional arguments instead of hashed arguments
        var result = await this.RenderPromptTemplateAsync(template);

        // Assert
        Assert.Equal("BazBar", result);
    }

    [Fact]
    public async Task ItRendersFunctionHelpersWitHashArgumentsAndInputVariableAsync()
    {
        // Arrange and Act
        const string VarName = "param_x";
        var template = """{{Foo-StringifyInt (""" + VarName + """)}}""";
        var inputVariables = new List<InputVariable> { new() { Name = VarName } };
        var arguments = new KernelArguments { [VarName] = 5 };

        var result = await this.RenderPromptTemplateAsync(template, inputVariables, arguments);

        // Assert
        Assert.Equal("5", result);
    }

    [Fact]
    public async Task ShouldThrowExceptionWhenMissingRequiredParameterAsync()
    {
        // Arrange and Act
        var template = """{{Foo-Combine x="Bar"}}""";

        // Assert
        var exception = await Assert.ThrowsAsync<KernelException>(() => this.RenderPromptTemplateAsync(template));
        Assert.Matches("Parameter .* is required for function", exception.Message);
    }

    [Fact]
    public async Task ShouldThrowExceptionWhenArgumentsAreNotProvidedAsync()
    {
        // Arrange
        var template = "{{Foo-Combine}}";

        // Act and Assert
        var exception = await Assert.ThrowsAsync<ArgumentException>(() => this.RenderPromptTemplateAsync(template));
        Assert.Matches("No arguments are provided for .*", exception.Message);
    }

    [Fact]
    public async Task ShouldThrowExceptionWhenFunctionHelperHasInvalidParameterTypeAsync()
    {
        // Arrange and Act
        var template = """{{Foo-StringifyInt x="twelve"}}""";

        // Assert
        var exception = await Assert.ThrowsAsync<KernelException>(() => this.RenderPromptTemplateAsync(template));
        Assert.Contains("Invalid argument type", exception.Message, StringComparison.CurrentCultureIgnoreCase);
    }

    [Fact]
    public async Task ShouldThrowExceptionWhenFunctionHasNullPositionalParameterAsync()
    {
        // Arrange and Act
        var template = """{{Foo-StringifyInt (nullParameter)}}""";
        var inputVariables = new List<InputVariable> { new() { Name = "nullParameter" } };
        var arguments = new KernelArguments { ["nullParameter"] = null };

        // Assert
        var exception = await Assert.ThrowsAsync<KernelException>(() => this.RenderPromptTemplateAsync(template, inputVariables, arguments));
        Assert.Contains("Invalid parameter type for function", exception.Message, StringComparison.CurrentCultureIgnoreCase);
        Assert.Contains("<null>", exception.Message, StringComparison.CurrentCultureIgnoreCase);
    }

    [Fact]
    public async Task ShouldThrowExceptionWhenFunctionHasNullHashParameterAsync()
    {
        // Arrange and Act
        var template = """{{Foo-StringifyInt x=(nullParameter)}}""";
        var inputVariables = new List<InputVariable> { new() { Name = "nullParameter" } };
        var arguments = new KernelArguments { ["nullParameter"] = null };

        // Assert
        var exception = await Assert.ThrowsAsync<KernelException>(() => this.RenderPromptTemplateAsync(template, inputVariables, arguments));
        Assert.Contains("Invalid argument type for function", exception.Message, StringComparison.CurrentCultureIgnoreCase);
        Assert.Contains("<null>", exception.Message, StringComparison.CurrentCultureIgnoreCase);
    }

    [Fact]
    public async Task ShouldThrowExceptionWhenFunctionHelperIsNotDefinedAsync()
    {
        // Arrange and Act
        var template = """{{Foo-Random x="random"}}""";

        // Assert
        var exception = await Assert.ThrowsAsync<HandlebarsRuntimeException>(() => this.RenderPromptTemplateAsync(template));
        Assert.Contains("Template references a helper that cannot be resolved", exception.Message, StringComparison.CurrentCultureIgnoreCase);
    }

    [Fact]
    public async Task ItCanReturnChatMessageContentAsync()
    {
        // Arrange
        var template = "{{Foo-ChatMessageContent \"user\" \"User content\"}}";

        // Act
        var result = await this.RenderPromptTemplateAsync(template);

        // Assert
        Assert.Equal("User content", result);
    }

    [Theory]
    [InlineData("{{Foo-RestApiOperationResponse \"text\" \"text/plain\"}}", "text")]
    [InlineData("{{Foo-RestApiOperationResponse \'{\"key\":\"value\"}\' \'application/json\'}}", "[key, value]")]
    public async Task ItCanReturnRestApiOperationResponseAsync(string template, string expectedResult)
    {
        // Arrange and Act
        var result = await this.RenderPromptTemplateAsync(template);

        // Assert
        Assert.Equal(expectedResult, result);
    }

    [Fact]
    public async Task ItCanReturnCustomReturnTypeAsync()
    {
        // Arrange
        var template = "{{Foo-CustomReturnType \"text\"}}";

        // Act
        var result = await this.RenderPromptTemplateAsync(template);

        // Assert
        Assert.Equal("text", result);
    }

    private readonly HandlebarsPromptTemplateFactory _factory;
    private readonly Kernel _kernel;
    private readonly KernelArguments _arguments;

    private async Task<string> RenderPromptTemplateAsync(string template, List<InputVariable>? inputVariables = null, KernelArguments? arguments = null)
    {
        // Arrange
        this._kernel.ImportPluginFromObject(new Foo());
        var resultConfig = InitializeHbPromptConfig(template);
        if (inputVariables != null)
        {
            resultConfig.InputVariables = inputVariables;
        }

        var target = (HandlebarsPromptTemplate)this._factory.Create(resultConfig);

        // Act
        var result = await target.RenderAsync(this._kernel, arguments ?? this._arguments);

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

        [KernelFunction, Description("Return ChatMessageContent")]
        public ChatMessageContent ChatMessageContent(string role, string content) => new(new AuthorRole(role), content);

        [KernelFunction, Description("Return RestApiOperationResponse")]
        public RestApiOperationResponse RestApiOperationResponse(string content, string contentType) => new(content, contentType);

        [KernelFunction, Description("Return CustomReturnType")]
        public CustomReturnType CustomReturnType(string textProperty) => new(textProperty);
    }

    private sealed class CustomReturnType(string textProperty)
    {
        public string TextProperty { get; set; } = textProperty;

        public override string ToString() => this.TextProperty;
    }
}
