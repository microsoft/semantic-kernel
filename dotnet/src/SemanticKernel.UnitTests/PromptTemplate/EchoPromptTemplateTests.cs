// Copyright (c) Microsoft. All rights reserved.

using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Xunit;

namespace SemanticKernel.UnitTests.PromptTemplate;

public sealed class EchoPromptTemplateTests
{
    [Fact]
    public async Task ItDoesNothingForSemanticKernelFormatAsync()
    {
        // Arrange
        var template = """This {{$x11}} {{$a}}{{$missing}} test template {{p.bar $b}} and {{p.foo c='literal "c"' d = $d}} and {{p.baz ename=$e}}""";
        var promptTemplateConfig = new PromptTemplateConfig(template);
        var templateFactory = new EchoPromptTemplateFactory();

        // Act
        var target = templateFactory.Create(promptTemplateConfig);
        var result = await target.RenderAsync(new Kernel());

        // Assert
        Assert.NotNull(result);
        Assert.Equal(template, result);
    }

    [Fact]
    public async Task ItDoesNothingForHandlebarsFormatAsync()
    {
        // Arrange
        var template = """This {{x11}} {{a}}{{missing}} test template {{p.bar b}} and {{p.foo c='literal "c"' d = d}} and {{p.baz ename=e}}""";
        var promptTemplateConfig = new PromptTemplateConfig(template) { TemplateFormat = "handlebars" };
        var templateFactory = new EchoPromptTemplateFactory();

        // Act
        var target = templateFactory.Create(promptTemplateConfig);
        var result = await target.RenderAsync(new Kernel());

        // Assert
        Assert.NotNull(result);
        Assert.Equal(template, result);
    }
}
