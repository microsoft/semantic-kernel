// Copyright (c) Microsoft. All rights reserved.

using System.Linq;
using System.Text.Json;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using SemanticKernel.UnitTests.Functions.JsonSerializerContexts;
using Xunit;

namespace SemanticKernel.UnitTests.Contents.FunctionCallBuilder;

public class FunctionCallContentBuilderTests
{
    [Theory]
    [ClassData(typeof(TestJsonSerializerOptionsForKernelArguments))]
    public void ItShouldBuildFunctionCallContentForOneFunction(JsonSerializerOptions? jsos)
    {
        // Arrange
        var sut = jsos is not null ? new FunctionCallContentBuilder(jsos) : new FunctionCallContentBuilder();

        // Act
        var update1 = CreateStreamingContentWithFunctionCallUpdate(choiceIndex: 1, functionCallIndex: 2, callId: "f_101", name: null, arguments: null);
        sut.Append(update1);

        var update2 = CreateStreamingContentWithFunctionCallUpdate(choiceIndex: 1, functionCallIndex: 2, callId: null, name: "WeatherUtils-GetTemperature", arguments: null);
        sut.Append(update2);

        var update3 = CreateStreamingContentWithFunctionCallUpdate(choiceIndex: 1, functionCallIndex: 2, callId: null, name: null, arguments: "{\"city\":");
        sut.Append(update3);

        var update4 = CreateStreamingContentWithFunctionCallUpdate(choiceIndex: 1, functionCallIndex: 2, callId: null, name: null, arguments: "\"Seattle\"}");
        sut.Append(update4);

        var functionCalls = sut.Build();

        // Assert
        var functionCall = Assert.Single(functionCalls);

        Assert.Equal("f_101", functionCall.Id);
        Assert.Equal("WeatherUtils", functionCall.PluginName);
        Assert.Equal("GetTemperature", functionCall.FunctionName);

        Assert.NotNull(functionCall.Arguments);
        Assert.Equal("Seattle", functionCall.Arguments["city"]);

        Assert.Null(functionCall.Exception);
    }

    [Theory]
    [ClassData(typeof(TestJsonSerializerOptionsForKernelArguments))]
    public void ItShouldNotOverwriteFunctionNameOrId(JsonSerializerOptions? jsos)
    {
        // Arrange
        var sut = jsos is not null ? new FunctionCallContentBuilder(jsos) : new FunctionCallContentBuilder();

        // Act
        var update1 = CreateStreamingContentWithFunctionCallUpdate(choiceIndex: 1, functionCallIndex: 2, callId: "f_101", name: null, arguments: null);
        sut.Append(update1);

        var update2 = CreateStreamingContentWithFunctionCallUpdate(choiceIndex: 1, functionCallIndex: 2, callId: null, name: "WeatherUtils-GetTemperature", arguments: null);
        sut.Append(update2);

        var update3 = CreateStreamingContentWithFunctionCallUpdate(choiceIndex: 1, functionCallIndex: 2, callId: "", name: "", arguments: "{\"city\":");
        sut.Append(update3);

        var update4 = CreateStreamingContentWithFunctionCallUpdate(choiceIndex: 1, functionCallIndex: 2, callId: null, name: null, arguments: "\"Seattle\"}");
        sut.Append(update4);

        var functionCalls = sut.Build();

        // Assert
        var functionCall = Assert.Single(functionCalls);

        Assert.Equal("f_101", functionCall.Id);
        Assert.Equal("WeatherUtils", functionCall.PluginName);
        Assert.Equal("GetTemperature", functionCall.FunctionName);

        Assert.NotNull(functionCall.Arguments);
        Assert.Equal("Seattle", functionCall.Arguments["city"]);

        Assert.Null(functionCall.Exception);
    }

    [Theory]
    [ClassData(typeof(TestJsonSerializerOptionsForKernelArguments))]
    public void ItShouldBuildFunctionCallContentForManyFunctions(JsonSerializerOptions? jsos)
    {
        // Arrange
        var sut = jsos is not null ? new FunctionCallContentBuilder(jsos) : new FunctionCallContentBuilder();

        // Act
        var f1_update1 = CreateStreamingContentWithFunctionCallUpdate(choiceIndex: 0, functionCallIndex: 1, callId: "f_1", name: "WeatherUtils-GetTemperature", arguments: null);
        sut.Append(f1_update1);

        var f2_update1 = CreateStreamingContentWithFunctionCallUpdate(choiceIndex: 0, functionCallIndex: 2, callId: null, name: "WeatherUtils-GetHumidity", arguments: null);
        sut.Append(f2_update1);

        var f2_update2 = CreateStreamingContentWithFunctionCallUpdate(choiceIndex: 0, functionCallIndex: 2, callId: "f_2", name: null, arguments: null);
        sut.Append(f2_update2);

        var f1_update2 = CreateStreamingContentWithFunctionCallUpdate(choiceIndex: 0, functionCallIndex: 1, callId: null, name: null, arguments: "{\"city\":");
        sut.Append(f1_update2);

        var f2_update3 = CreateStreamingContentWithFunctionCallUpdate(choiceIndex: 0, functionCallIndex: 2, callId: null, name: null, arguments: "{\"city\":");
        sut.Append(f2_update3);

        var f1_update3 = CreateStreamingContentWithFunctionCallUpdate(choiceIndex: 0, functionCallIndex: 1, callId: null, name: null, arguments: "\"Seattle\"}");
        sut.Append(f1_update3);

        var f2_update4 = CreateStreamingContentWithFunctionCallUpdate(choiceIndex: 0, functionCallIndex: 2, callId: null, name: null, arguments: "\"Georgia\"}");
        sut.Append(f2_update4);

        var functionCalls = sut.Build();

        // Assert
        Assert.Equal(2, functionCalls.Count);

        var functionCall1 = functionCalls.ElementAt(0);
        Assert.Equal("f_1", functionCall1.Id);
        Assert.Equal("WeatherUtils", functionCall1.PluginName);
        Assert.Equal("GetTemperature", functionCall1.FunctionName);
        Assert.Equal("Seattle", functionCall1.Arguments?["city"]);
        Assert.Null(functionCall1.Exception);

        var functionCall2 = functionCalls.ElementAt(1);
        Assert.Equal("f_2", functionCall2.Id);
        Assert.Equal("WeatherUtils", functionCall2.PluginName);
        Assert.Equal("GetHumidity", functionCall2.FunctionName);
        Assert.Equal("Georgia", functionCall2.Arguments?["city"]);
        Assert.Null(functionCall2.Exception);
    }

    [Theory]
    [ClassData(typeof(TestJsonSerializerOptionsForKernelArguments))]
    public void ItShouldBuildFunctionCallContentForManyFunctionsCameInDifferentRequests(JsonSerializerOptions? jsos)
    {
        // Arrange
        var sut = jsos is not null ? new FunctionCallContentBuilder(jsos) : new FunctionCallContentBuilder();

        // Act

        // f1 call was streamed as part of the first request
        var f1_update1 = CreateStreamingContentWithFunctionCallUpdate(choiceIndex: 0, functionCallIndex: 0, requestIndex: 0, callId: "f_1", name: "WeatherUtils-GetTemperature", arguments: null);
        sut.Append(f1_update1);

        var f1_update2 = CreateStreamingContentWithFunctionCallUpdate(choiceIndex: 0, functionCallIndex: 0, requestIndex: 0, callId: null, name: null, arguments: "{\"city\":");
        sut.Append(f1_update2);

        var f1_update3 = CreateStreamingContentWithFunctionCallUpdate(choiceIndex: 0, functionCallIndex: 0, requestIndex: 0, callId: null, name: null, arguments: "\"Seattle\"}");
        sut.Append(f1_update3);

        // f2 call was streamed as part of the second request
        var f2_update1 = CreateStreamingContentWithFunctionCallUpdate(choiceIndex: 0, functionCallIndex: 0, requestIndex: 1, callId: null, name: "WeatherUtils-GetHumidity", arguments: null);
        sut.Append(f2_update1);

        var f2_update2 = CreateStreamingContentWithFunctionCallUpdate(choiceIndex: 0, functionCallIndex: 0, requestIndex: 1, callId: "f_2", name: null, arguments: null);
        sut.Append(f2_update2);

        var f2_update3 = CreateStreamingContentWithFunctionCallUpdate(choiceIndex: 0, functionCallIndex: 0, requestIndex: 1, callId: null, name: null, arguments: "{\"city\":");
        sut.Append(f2_update3);

        var f2_update4 = CreateStreamingContentWithFunctionCallUpdate(choiceIndex: 0, functionCallIndex: 0, requestIndex: 1, callId: null, name: null, arguments: "\"Georgia\"}");
        sut.Append(f2_update4);

        var functionCalls = sut.Build();

        // Assert
        Assert.Equal(2, functionCalls.Count);

        var functionCall1 = functionCalls.ElementAt(0);
        Assert.Equal("f_1", functionCall1.Id);
        Assert.Equal("WeatherUtils", functionCall1.PluginName);
        Assert.Equal("GetTemperature", functionCall1.FunctionName);
        Assert.Equal("Seattle", functionCall1.Arguments?["city"]);
        Assert.Null(functionCall1.Exception);

        var functionCall2 = functionCalls.ElementAt(1);
        Assert.Equal("f_2", functionCall2.Id);
        Assert.Equal("WeatherUtils", functionCall2.PluginName);
        Assert.Equal("GetHumidity", functionCall2.FunctionName);
        Assert.Equal("Georgia", functionCall2.Arguments?["city"]);
        Assert.Null(functionCall2.Exception);
    }

    [Theory]
    [ClassData(typeof(TestJsonSerializerOptionsForKernelArguments))]
    public void ItShouldCaptureArgumentsDeserializationException(JsonSerializerOptions? jsos)
    {
        // Arrange
        var sut = jsos is not null ? new FunctionCallContentBuilder(jsos) : new FunctionCallContentBuilder();

        // Act
        var update1 = CreateStreamingContentWithFunctionCallUpdate(choiceIndex: 1, functionCallIndex: 2, callId: "f_101", name: "WeatherUtils-GetTemperature", arguments: null);
        sut.Append(update1);

        var update2 = CreateStreamingContentWithFunctionCallUpdate(choiceIndex: 1, functionCallIndex: 2, callId: null, name: null, arguments: "{\"city\":");
        sut.Append(update2);

        // Invalid JSON - double closing braces - }}
        var update3 = CreateStreamingContentWithFunctionCallUpdate(choiceIndex: 1, functionCallIndex: 2, callId: null, name: null, arguments: "\"Seattle\"}}");
        sut.Append(update3);

        var functionCalls = sut.Build();

        // Assert
        var functionCall = Assert.Single(functionCalls);

        Assert.Equal("f_101", functionCall.Id);
        Assert.Equal("WeatherUtils", functionCall.PluginName);
        Assert.Equal("GetTemperature", functionCall.FunctionName);
        Assert.Null(functionCall.Arguments);
        Assert.NotNull(functionCall.Exception);
    }

    [Fact]
    public void ItShouldParseUnderscoreSeparatorForOllamaAndGeminiConnectors()
    {
        // Arrange - Ollama/Gemini use underscore (e.g. time_ReadFile) per FullyQualifiedAIFunction
        var sut = new FunctionCallContentBuilder();

        // Act
        var update1 = CreateStreamingContentWithFunctionCallUpdate(choiceIndex: 1, functionCallIndex: 0, callId: "call_1", name: "time_ReadFile", arguments: null);
        sut.Append(update1);

        var update2 = CreateStreamingContentWithFunctionCallUpdate(choiceIndex: 1, functionCallIndex: 0, callId: null, name: null, arguments: "{\"filePath\":\"d:/test.txt\"}");
        sut.Append(update2);

        var functionCalls = sut.Build();

        // Assert
        var functionCall = Assert.Single(functionCalls);
        Assert.Equal("call_1", functionCall.Id);
        Assert.Equal("time", functionCall.PluginName);
        Assert.Equal("ReadFile", functionCall.FunctionName);
        Assert.NotNull(functionCall.Arguments);
        Assert.Equal("d:/test.txt", functionCall.Arguments["filePath"]);
    }

    [Fact]
    public void ItShouldParseDotSeparatorForFunctionChoiceBehavior()
    {
        // Arrange - FunctionChoiceBehavior uses dot (e.g. time.ReadFile)
        var sut = new FunctionCallContentBuilder();

        // Act
        var update = CreateStreamingContentWithFunctionCallUpdate(choiceIndex: 1, functionCallIndex: 0, callId: "call_1", name: "time.ReadFile", arguments: null);
        sut.Append(update);

        var functionCalls = sut.Build();

        // Assert
        var functionCall = Assert.Single(functionCalls);
        Assert.Equal("time", functionCall.PluginName);
        Assert.Equal("ReadFile", functionCall.FunctionName);
    }

    private static StreamingChatMessageContent CreateStreamingContentWithFunctionCallUpdate(int choiceIndex, int functionCallIndex, string? callId, string? name, string? arguments, int requestIndex = 0)
    {
        var content = new StreamingChatMessageContent(AuthorRole.Assistant, null);

        content.Items.Add(new StreamingFunctionCallUpdateContent
        {
            ChoiceIndex = choiceIndex,
            FunctionCallIndex = functionCallIndex,
            CallId = callId,
            Name = name,
            Arguments = arguments,
            RequestIndex = requestIndex
        });

        return content;
    }

#pragma warning disable CA1812 // Internal class that is apparently never instantiated
    internal sealed class TestJsonSerializerOptionsForKernelArguments : TheoryData<JsonSerializerOptions?>
#pragma warning restore CA1812 // Internal class that is apparently never instantiated
    {
        public TestJsonSerializerOptionsForKernelArguments()
        {
            JsonSerializerOptions options = new();
            options.TypeInfoResolverChain.Add(KernelArgumentsJsonSerializerContext.Default);

            this.Add(null);
            this.Add(options);
        }
    }
}
