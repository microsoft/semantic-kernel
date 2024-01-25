// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;
using Xunit;

namespace SemanticKernel.Functions.UnitTests.Markdown.Functions;

public class KernelFunctionMarkdownTests
{
    [Fact]
    public void ItShouldCreatePromptFunctionConfigFromMarkdown()
    {
        // Arrange
        // Act
        var model = KernelFunctionMarkdown.CreateFromPromptMarkdown(this._markdown, "TellMeAbout");

        // Assert
        Assert.NotNull(model);
        Assert.Equal("TellMeAbout", model.Name);
        Assert.Equal("Hello AI, tell me about {{$input}}", model.Template);
        Assert.Equal(2, model.ExecutionSettings.Count);
        Assert.Equal("gpt4", model.ExecutionSettings["service1"].ModelId);
        Assert.Equal("gpt3.5", model.ExecutionSettings["service2"].ModelId);
    }

    [Fact]
    public void ItShouldCreatePromptFunctionFromMarkdown()
    {
        // Arrange
        var kernel = new Kernel();

        // Act
        var function = KernelFunctionMarkdown.CreateFromPromptMarkdown(this._markdown, "TellMeAbout");

        // Assert
        Assert.NotNull(function);
        Assert.Equal("TellMeAbout", function.Name);
    }

    private readonly string _markdown = @"
This is a semantic kernel prompt template
```sk.prompt
Hello AI, tell me about {{$input}}
```
These are AI execution settings
```sk.execution_settings
{
    ""service1"" : {
        ""model_id"": ""gpt4"",
        ""temperature"": 0.7
    }
}
```
These are more AI execution settings
```sk.execution_settings
{
    ""service2"" : {
        ""model_id"": ""gpt3.5"",
        ""temperature"": 0.8
    }
}
```
";
}
