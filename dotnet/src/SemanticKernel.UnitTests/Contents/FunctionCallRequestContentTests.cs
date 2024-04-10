// Copyright (c) Microsoft. All rights reserved.

using System.Linq;
using System.Text.Json;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.ChatCompletion;
using Xunit;

namespace Microsoft.SemanticKernel.Contents;

public class FunctionCallRequestContentTests
{
    private readonly KernelArguments _arguments;

    public FunctionCallRequestContentTests()
    {
        this._arguments = [];
    }

    [Fact]
    public void ItShouldBeInitializedFromFunctionAndPluginName()
    {
        // Arrange & act
        var sut = new FunctionCallRequestContent("f1", "p1", "id", this._arguments);

        // Assert
        Assert.Equal("f1", sut.FunctionName);
        Assert.Equal("p1", sut.PluginName);
        Assert.Equal("id", sut.Id);
        Assert.Same(this._arguments, sut.Arguments);
    }

    [Fact]
    public async Task ItShouldFindKernelFunctionAndInvokeItAsync()
    {
        // Arrange
        var kernel = new Kernel();

        KernelArguments? actualArguments = null;

        var function = KernelFunctionFactory.CreateFromMethod((KernelArguments args) =>
        {
            actualArguments = args;
            return "result";
        }, "f1");

        kernel.Plugins.AddFromFunctions("p1", [function]);

        var sut = new FunctionCallRequestContent("f1", "p1", "id", this._arguments);

        // Act
        var resultContent = await sut.InvokeAsync(kernel);

        // Assert
        Assert.NotNull(resultContent);
        Assert.Equal("result", resultContent.Result);
        Assert.Same(this._arguments, actualArguments);
    }

    [Fact]
    public async Task ItShouldHandleFunctionCallRequestExceptionAsync()
    {
        // Arrange
        var kernel = new Kernel();

        var sut = new FunctionCallRequestContent("f1", "p1", "id")
        {
            Exception = new JsonException("Error: Function call arguments were invalid JSON.")
        };

        // Act
        var resultContent = await sut.InvokeAsync(kernel);

        // Assert
        Assert.NotNull(resultContent);
        Assert.Equal("Error: Function call arguments were invalid JSON.", resultContent.Result);
    }

    [Fact]
    public void ItShouldReturnListOfFunctionCallRequests()
    {
        // Arrange
        var functionCallRequestContents = new ChatMessageContentItemCollection
        {
            new FunctionCallRequestContent("f1", "p1", "id1", this._arguments),
            new FunctionCallRequestContent("f2", "p2", "id2", this._arguments),
            new FunctionCallRequestContent("f3", "p3", "id3", this._arguments)
        };

        var chatMessage = new ChatMessageContent(AuthorRole.Tool, functionCallRequestContents);

        // Act
        var result = FunctionCallRequestContent.GetFunctionCalls(chatMessage).ToArray();

        // Assert
        Assert.NotNull(result);
        Assert.Equal(3, result.Length);
        Assert.Equal("id1", result.ElementAt(0).Id);
        Assert.Equal("id2", result.ElementAt(1).Id);
        Assert.Equal("id3", result.ElementAt(2).Id);
    }
}
