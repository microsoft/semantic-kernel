// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Functions.Markdown.Functions;
using Xunit;

namespace SemanticKernel.Functions.UnitTests.Markdown.Functions;

public class SKFunctionMarkdownTests
{
    [Fact]
    public void ItShouldCreateSemanticFunctionConfigFromMarkdown()
    {
        // Arrange
        // Act
        var model = SKFunctionMarkdown.CreateFromPromptMarkdown(this._markdown, "TellMeAbout");

        // Assert
        Assert.NotNull(model);
        Assert.Equal("TellMeAbout", model.Name);
        Assert.Equal("Hello AI, tell me about {{$input}}", model.Template);
        Assert.Equal(2, model.ModelSettings.Count);
        Assert.Equal("gpt4", model.ModelSettings[0].ModelId);
        Assert.Equal("gpt3.5", model.ModelSettings[1].ModelId);
    }

    [Fact]
    public void ItShouldCreateSemanticFunctionFromMarkdown()
    {
        // Arrange
        var kernel = new KernelBuilder().Build();

        // Act
        var skfunction = SKFunctionMarkdown.CreateFromPromptMarkdown(this._markdown, "TellMeAbout");

        // Assert
        Assert.NotNull(skfunction);
        Assert.Equal("TellMeAbout", skfunction.Name);
    }

    private readonly string _markdown = @"
This is a semantic kernel prompt template
```sk.prompt
Hello AI, tell me about {{$input}}
```
These are AI request settings
```sk.model_settings
{
    ""model_id"": ""gpt4"",
    ""temperature"": 0.7
}
```
These are more AI request settings
```sk.model_settings
{
    ""model_id"": ""gpt3.5"",
    ""temperature"": 0.8
}
```
";
}
