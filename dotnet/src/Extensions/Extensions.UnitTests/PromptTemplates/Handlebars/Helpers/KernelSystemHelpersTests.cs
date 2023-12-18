// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.PromptTemplates.Handlebars;
using Xunit;
using static Extensions.UnitTests.PromptTemplates.Handlebars.TestUtilities;

namespace SemanticKernel.Extensions.UnitTests.PromptTemplates.Handlebars.Helpers;

public sealed class KernelSystemHelpersTests
{
    public KernelSystemHelpersTests()
    {
        this._factory = new();
        this._kernel = new();
        this._arguments = new() { ["input"] = Guid.NewGuid().ToString("X") };
    }

    [Fact]
    public async Task ItRendersTemplateWithMessageHelperAsync()
    {
        // Arrange
        var template = "{{#message role=\"title\"}}Hello World!{{/message}}";

        // Act
        var result = await this.RenderPromptTemplateAsync(template);

        // Assert
        Assert.Equal("<title~>Hello World!</title~>", result);
    }

    [Fact]
    public async Task ItRendersTemplateWithSetHelperAsync()
    {
        // Arrange
        var template = "{{set name=\"x\" value=10}}{{json x}}";
        var arguments = new KernelArguments();

        // Act
        var result = await this.RenderPromptTemplateAsync(template);

        // Assert
        Assert.Equal("10", result);
    }

    [Fact]
    public async Task ItRendersTemplateWithJsonHelperAsync()
    {
        // Arrange
        var template = "{{json person}}";
        var arguments = new KernelArguments
            {
                { "person", new { name = "Alice", age = 25 } }
            };

        // Act
        var result = await this.RenderPromptTemplateAsync(template, arguments);

        // Assert
        Assert.Equal("{\"name\":\"Alice\",\"age\":25}", result);
    }

    [Fact]
    public async Task ComplexVariableTypeReturnsObjectAsync()
    {
        // Arrange
        var template = "{{person}}";
        var arguments = new KernelArguments
            {
                { "person", new { name = "Alice", age = 25 } }
            };

        // Act
        var result = await this.RenderPromptTemplateAsync(template, arguments);

        // Assert  
        Assert.Equal("{ name = Alice, age = 25 }", result);
    }

    [Fact]
    public async Task VariableWithPropertyReferenceReturnsPropertyValueAsync()
    {
        // Arrange
        var template = "{{person.name}}";
        var arguments = new KernelArguments
            {
                { "person", new { name = "Alice", age = 25 } }
            };

        // Act
        var result = await this.RenderPromptTemplateAsync(template, arguments);

        // Assert
        Assert.Equal("Alice", result);
    }

    [Fact]
    public async Task VariableWithNestedObjectReturnsNestedObjectAsync()
    {
        // Arrange  
        var template = "{{person.Address}}";
        var arguments = new KernelArguments
        {
            { "person", new { Name = "Alice", Age = 25, Address = new { City = "New York", Country = "USA" } } }
        };

        // Act  
        var result = await this.RenderPromptTemplateAsync(template, arguments);

        // Assert  
        Assert.Equal("{ City = New York, Country = USA }", result);
    }

    [Fact]
    public async Task ItRendersTemplateWithArrayHelperAsync()
    {
        // Arrange
        var template = "{{#each (array 1 2 3)}}{{this}}{{/each}}";

        // Act
        var result = await this.RenderPromptTemplateAsync(template);

        // Assert
        Assert.Equal("123", result);
    }

    [Fact]
    public async Task ItRendersTemplateWithArrayHelperAndVariableReferenceAsync()
    {
        // Arrange
        var template = @"{{array ""hi"" "" "" name ""!"" ""Welcome to"" "" "" Address.City}}";
        var arguments = new KernelArguments
        {
            { "name", "Alice" },
            { "Address", new { City = "New York", Country = "USA"  } }
        };

        // Act
        var result = await this.RenderPromptTemplateAsync(template, arguments);

        // Assert
        Assert.Equal("hi, ,Alice,!,Welcome to, ,New York", result);
    }

    [Fact]
    public async Task ItRendersTemplateWithRawHelperAsync()
    {
        // Arrange
        var template = "{{{{raw}}}}{{x}}{{{{/raw}}}}";

        // Act
        var result = await this.RenderPromptTemplateAsync(template);

        // Assert
        Assert.Equal("{{x}}", result);
    }

    [Fact]
    public async Task ItRendersTemplateWithRangeHelperAsync()
    {
        // Arrange
        var template = "{{#each (range 1 5)}}{{this}}{{/each}}";

        // Act
        var result = await this.RenderPromptTemplateAsync(template);

        // Assert
        Assert.Equal("12345", result);
    }

    [Fact]
    public async Task ItRendersTemplateWithConcatHelperAsync()
    {
        // Arrange
        var template = "{{concat \"Hello\" \" \" name \"!\"}}";
        var arguments = new KernelArguments
            {
                { "name", "Alice" }
            };

        // Act
        var result = await this.RenderPromptTemplateAsync(template, arguments);

        // Assert
        Assert.Equal("Hello Alice!", result);
    }

    [Fact]
    public async Task ItRendersTemplateWithdSetAndConcatHelpersAsync()
    {
        // Arrange
        var template = "{{set name=\"name\" value=\"Alice\"}}{{concat \"Hello\" \" \" name \"!\"}}";

        // Act
        var result = await this.RenderPromptTemplateAsync(template);

        // Assert
        Assert.Equal("Hello Alice!", result);
    }

    [Fact]
    public async Task ItRendersTemplateWithEqualHelperAsync()
    {
        // Arrange
        var template = "{{#if (equals x y)}}Equal{{else}}Not equal{{/if}}";
        var arguments = new KernelArguments { { "x", 10 }, { "y", 10 } };

        // Act
        var result = await this.RenderPromptTemplateAsync(template, arguments);

        // Assert
        Assert.Equal("Equal", result);
    }

    #region private

    private readonly HandlebarsPromptTemplateFactory _factory;
    private readonly Kernel _kernel;
    private readonly KernelArguments _arguments;

    private async Task<string> RenderPromptTemplateAsync(string template, KernelArguments? args = null)
    {
        var resultConfig = InitializeHbPromptConfig(template);
        var target = (HandlebarsPromptTemplate)this._factory.Create(resultConfig);

        // Act
        var result = await target.RenderAsync(this._kernel, args);

        return result;
    }

    #endregion
}
