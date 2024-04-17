// Copyright (c) Microsoft. All rights reserved.
using System.Linq;
using System.Text.Json;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents.Chat;
using Microsoft.SemanticKernel.ChatCompletion;
using Xunit;

namespace SemanticKernel.Agents.UnitTests.Core.Chat;

/// <summary>
/// Unit testing of <see cref="FunctionResultProcessor{TestResult}"/>.
/// </summary>
public class FunctionResultProcessorTests
{
    /// <summary>
    /// Verify result processing.
    /// </summary>
    [Fact]
    public void VerifyFunctionResultProcessorSuccess()
    {
        this.VerifyFunctionResultProcessing("test", "test");
        this.VerifyFunctionResultProcessing("3", 3);
        this.VerifyFunctionResultProcessing(bool.TrueString, true);
        this.VerifyFunctionResultProcessing("-1090.3", -1090.3F);

        TestModel model = new(3, "test");
        this.VerifyFunctionResultProcessing(JsonSerializer.Serialize(model), model);
    }

    /// <summary>
    /// Verify processing when result doesn't match expectations.
    /// </summary>
    [Fact]
    public void VerifyFunctionResultProcessorFailure()
    {
        this.VerifyFunctionResultFailure<int>("test");
        this.VerifyFunctionResultFailure<bool>("test");
        this.VerifyFunctionResultFailure<float>("test");
        this.VerifyFunctionResultProcessing<TestModel>("[}badjson");
    }

    /// <summary>
    /// Verify <see cref="ChatMessageContent"/> processing.
    /// </summary>
    [Fact]
    public void VerifyFunctionResultProcessorContent()
    {
        KernelPlugin plugin = KernelPluginFactory.CreateFromObject(new TestPlugin());
        FunctionResultProcessor<string> processor = new();

        FunctionResult result = new(plugin.Single(), new ChatMessageContent(AuthorRole.System, content: null));
        string? value = processor.InterpretResult(result);
        Assert.Null(value);

        result = new(plugin.Single(), new ChatMessageContent(AuthorRole.System, content: "test"));
        value = processor.InterpretResult(result);
        Assert.NotNull(value);
        Assert.Equal("test", value);
    }

    private void VerifyFunctionResultFailure<TResult>(string seedResult)
    {
        TResult? result = this.VerifyFunctionResultProcessing<TResult>(seedResult);
        Assert.Equal(default, result);
    }

    private void VerifyFunctionResultProcessing<TResult>(string seedResult, TResult expectedResult)
    {
        TResult? result = this.VerifyFunctionResultProcessing<TResult>(seedResult);
        Assert.NotNull(result);
        Assert.Equal(expectedResult, result);
    }

    private TResult? VerifyFunctionResultProcessing<TResult>(string seedResult)
    {
        KernelPlugin plugin = KernelPluginFactory.CreateFromObject(new TestPlugin());
        FunctionResult result = new(plugin.Single(), seedResult);
        FunctionResultProcessor<TResult> processor = new();

        TResult? value = processor.InterpretResult(result);

        return value;
    }

    private record struct TestModel(int score, string notes);

    /// <summary>
    /// Empty plugin to satisfy <see cref="FunctionResult"/> constructor.
    /// </summary>
    private sealed class TestPlugin()
    {
        [KernelFunction]
        public void Anything() { }
    }
}
