// Copyright (c) Microsoft. All rights reserved.

using System;
using System.ClientModel;
using System.ClientModel.Primitives;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Net;
using System.Net.Http;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using Microsoft.SemanticKernel.Http;
using Microsoft.SemanticKernel.Services;
using Moq;
using OpenAI;
using OpenAI.Chat;
using Xunit;
using BinaryContent = System.ClientModel.BinaryContent;
using ChatMessageContent = Microsoft.SemanticKernel.ChatMessageContent;

namespace SemanticKernel.Connectors.OpenAI.UnitTests.Core;

public partial class ClientCoreTests
{
    [Fact]
    public void ItCanBeInstantiatedAndPropertiesSetAsExpected()
    {
        // Act
        var logger = new Mock<ILogger<ClientCoreTests>>().Object;
        var openAIClient = new OpenAIClient(new ApiKeyCredential("key"));

        var clientCoreModelConstructor = new ClientCore("model1", "apiKey");
        var clientCoreOpenAIClientConstructor = new ClientCore("model1", openAIClient, logger: logger);

        // Assert
        Assert.NotNull(clientCoreModelConstructor);
        Assert.NotNull(clientCoreOpenAIClientConstructor);

        Assert.Equal("model1", clientCoreModelConstructor.ModelId);
        Assert.Equal("model1", clientCoreOpenAIClientConstructor.ModelId);

        Assert.NotNull(clientCoreModelConstructor.Client);
        Assert.NotNull(clientCoreOpenAIClientConstructor.Client);
        Assert.Equal(openAIClient, clientCoreOpenAIClientConstructor.Client);
        Assert.Equal(NullLogger.Instance, clientCoreModelConstructor.Logger);
        Assert.Equal(logger, clientCoreOpenAIClientConstructor.Logger);
    }

    [Theory]
    [InlineData(null, null)]
    [InlineData("http://localhost", null)]
    [InlineData(null, "http://localhost")]
    [InlineData("http://localhost-1", "http://localhost-2")]
    public void ItUsesEndpointAsExpected(string? clientBaseAddress, string? providedEndpoint)
    {
        // Arrange
        Uri? endpoint = null;
        HttpClient? client = null;
        if (providedEndpoint is not null)
        {
            endpoint = new Uri(providedEndpoint);
        }

        if (clientBaseAddress is not null)
        {
            client = new HttpClient { BaseAddress = new Uri(clientBaseAddress) };
        }

        // Act
        var clientCore = new ClientCore("model", "apiKey", endpoint: endpoint, httpClient: client);

        // Assert
        Assert.Equal(endpoint ?? client?.BaseAddress ?? new Uri("https://api.openai.com/v1"), clientCore.Endpoint);
        Assert.True(clientCore.Attributes.ContainsKey(AIServiceExtensions.EndpointKey));
        Assert.Equal(endpoint?.ToString() ?? client?.BaseAddress?.ToString() ?? "https://api.openai.com/v1", clientCore.Attributes[AIServiceExtensions.EndpointKey]);

        client?.Dispose();
    }

    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public async Task ItAddOrganizationHeaderWhenProvidedAsync(bool organizationIdProvided)
    {
        using HttpMessageHandlerStub handler = new();
        using HttpClient client = new(handler);
        handler.ResponseToReturn = new HttpResponseMessage(System.Net.HttpStatusCode.OK);

        // Act
        var clientCore = new ClientCore(
            modelId: "model",
            apiKey: "test",
            organizationId: (organizationIdProvided) ? "organization" : null,
            httpClient: client);

        var pipelineMessage = clientCore.Client!.Pipeline.CreateMessage();
        pipelineMessage.Request.Method = "POST";
        pipelineMessage.Request.Uri = new Uri("http://localhost");
        pipelineMessage.Request.Content = BinaryContent.Create(new BinaryData("test"));

        // Assert
        await clientCore.Client.Pipeline.SendAsync(pipelineMessage);

        if (organizationIdProvided)
        {
            Assert.True(handler.RequestHeaders!.Contains("OpenAI-Organization"));
            Assert.Equal("organization", handler.RequestHeaders.GetValues("OpenAI-Organization").FirstOrDefault());
        }
        else
        {
            Assert.False(handler.RequestHeaders!.Contains("OpenAI-Organization"));
        }
    }

    [Fact]
    public async Task ItAddSemanticKernelHeadersOnEachRequestAsync()
    {
        using HttpMessageHandlerStub handler = new();
        using HttpClient client = new(handler);
        handler.ResponseToReturn = new HttpResponseMessage(System.Net.HttpStatusCode.OK);

        // Act
        var clientCore = new ClientCore(modelId: "model", apiKey: "test", httpClient: client);

        var pipelineMessage = clientCore.Client!.Pipeline.CreateMessage();
        pipelineMessage.Request.Method = "POST";
        pipelineMessage.Request.Uri = new Uri("http://localhost");
        pipelineMessage.Request.Content = BinaryContent.Create(new BinaryData("test"));

        // Assert
        await clientCore.Client.Pipeline.SendAsync(pipelineMessage);

        Assert.True(handler.RequestHeaders!.Contains(HttpHeaderConstant.Names.SemanticKernelVersion));
        Assert.Equal(HttpHeaderConstant.Values.GetAssemblyVersion(typeof(ClientCore)), handler.RequestHeaders.GetValues(HttpHeaderConstant.Names.SemanticKernelVersion).FirstOrDefault());

        Assert.True(handler.RequestHeaders.Contains("User-Agent"));
        Assert.Contains(HttpHeaderConstant.Values.UserAgent, handler.RequestHeaders.GetValues("User-Agent").FirstOrDefault());
    }

    [Fact]
    public async Task ItDoesNotAddSemanticKernelHeadersWhenOpenAIClientIsProvidedAsync()
    {
        using HttpMessageHandlerStub handler = new();
        using HttpClient client = new(handler);
        handler.ResponseToReturn = new HttpResponseMessage(System.Net.HttpStatusCode.OK);

        // Act
        var clientCore = new ClientCore(
            modelId: "model",
            openAIClient: new OpenAIClient(
                new ApiKeyCredential("test"),
                new OpenAIClientOptions()
                {
                    Transport = new HttpClientPipelineTransport(client),
                    RetryPolicy = new ClientRetryPolicy(maxRetries: 0),
                    NetworkTimeout = Timeout.InfiniteTimeSpan
                }));

        var pipelineMessage = clientCore.Client!.Pipeline.CreateMessage();
        pipelineMessage.Request.Method = "POST";
        pipelineMessage.Request.Uri = new Uri("http://localhost");
        pipelineMessage.Request.Content = BinaryContent.Create(new BinaryData("test"));

        // Assert
        await clientCore.Client.Pipeline.SendAsync(pipelineMessage);

        Assert.False(handler.RequestHeaders!.Contains(HttpHeaderConstant.Names.SemanticKernelVersion));
        Assert.DoesNotContain(HttpHeaderConstant.Values.UserAgent, handler.RequestHeaders.GetValues("User-Agent").FirstOrDefault());
    }

    [Theory]
    [InlineData(null)]
    [InlineData("")]
    [InlineData("value")]
    public void ItAddsAttributesButDoesNothingIfNullOrEmpty(string? value)
    {
        // Arrange
        var clientCore = new ClientCore("model", "apikey");
        // Act

        clientCore.AddAttribute("key", value);

        // Assert
        if (string.IsNullOrEmpty(value))
        {
            Assert.False(clientCore.Attributes.ContainsKey("key"));
        }
        else
        {
            Assert.True(clientCore.Attributes.ContainsKey("key"));
            Assert.Equal(value, clientCore.Attributes["key"]);
        }
    }

    [Fact]
    public void ItAddsModelIdAttributeAsExpected()
    {
        // Arrange
        var expectedModelId = "modelId";

        // Act
        var clientCore = new ClientCore(expectedModelId, "apikey");
        var clientCoreBreakingGlass = new ClientCore(expectedModelId, new OpenAIClient(new ApiKeyCredential(" ")));

        // Assert
        Assert.True(clientCore.Attributes.ContainsKey(AIServiceExtensions.ModelIdKey));
        Assert.True(clientCoreBreakingGlass.Attributes.ContainsKey(AIServiceExtensions.ModelIdKey));
        Assert.Equal(expectedModelId, clientCore.Attributes[AIServiceExtensions.ModelIdKey]);
        Assert.Equal(expectedModelId, clientCoreBreakingGlass.Attributes[AIServiceExtensions.ModelIdKey]);
    }

    [Fact]
    public void ItAddOrNotOrganizationIdAttributeWhenProvided()
    {
        // Arrange
        var expectedOrganizationId = "organizationId";

        // Act
        var clientCore = new ClientCore("modelId", "apikey", expectedOrganizationId);
        var clientCoreWithoutOrgId = new ClientCore("modelId", "apikey");

        // Assert
        Assert.True(clientCore.Attributes.ContainsKey(ClientCore.OrganizationKey));
        Assert.Equal(expectedOrganizationId, clientCore.Attributes[ClientCore.OrganizationKey]);
        Assert.False(clientCoreWithoutOrgId.Attributes.ContainsKey(ClientCore.OrganizationKey));
    }

    [Fact]
    public void ItThrowsWhenNotUsingCustomEndpointAndApiKeyIsNotProvided()
    {
        // Act & Assert
        Assert.Throws<ArgumentException>(() => new ClientCore("modelId", " "));
        Assert.Throws<ArgumentException>(() => new ClientCore("modelId", ""));
        Assert.Throws<ArgumentNullException>(() => new ClientCore("modelId", apiKey: null!));
    }

    [Fact]
    public void ItDoesNotThrowWhenUsingCustomEndpointAndApiKeyIsNotProvided()
    {
        // Act & Assert
        ClientCore? clientCore = null;
        clientCore = new ClientCore("modelId", " ", endpoint: new Uri("http://localhost"));
        clientCore = new ClientCore("modelId", "", endpoint: new Uri("http://localhost"));
        clientCore = new ClientCore("modelId", apiKey: null!, endpoint: new Uri("http://localhost"));
    }

    [Theory]
    [ClassData(typeof(ChatMessageContentWithFunctionCalls))]
    public async Task ItShouldReplaceDisallowedCharactersInFunctionName(ChatMessageContent chatMessageContent, bool nameContainsDisallowedCharacter)
    {
        // Arrange
        using var responseMessage = new HttpResponseMessage(HttpStatusCode.OK)
        {
            Content = new StringContent(File.ReadAllText("TestData/chat_completion_test_response.json"))
        };

        using HttpMessageHandlerStub handler = new();
        handler.ResponseToReturn = responseMessage;
        using HttpClient client = new(handler);

        var clientCore = new ClientCore("modelId", "apikey", httpClient: client);

        ChatHistory chatHistory = [chatMessageContent];

        // Act
        await clientCore.GetChatMessageContentsAsync("gpt-4", chatHistory, new OpenAIPromptExecutionSettings(), new Kernel());

        // Assert
        JsonElement jsonString = JsonSerializer.Deserialize<JsonElement>(handler.RequestContent);

        var function = jsonString.GetProperty("messages")[0].GetProperty("tool_calls")[0].GetProperty("function");

        if (nameContainsDisallowedCharacter)
        {
            // The original name specified in function calls is "bar.foo", which contains a disallowed character '.'.
            Assert.Equal("bar_foo", function.GetProperty("name").GetString());
        }
        else
        {
            // The original name specified in function calls is "bar-foo" and contains no disallowed characters.
            Assert.Equal("bar-foo", function.GetProperty("name").GetString());
        }
    }

    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public async Task FunctionArgumentTypesShouldBeRetainedIfSpecifiedAsync(bool retain)
    {
        // Arrange
        using var responseMessage = new HttpResponseMessage(HttpStatusCode.OK)
        {
            Content = new StringContent(File.ReadAllText("TestData/chat_completion_multiple_function_calls_test_response.json"))
        };

        using HttpMessageHandlerStub handler = new();
        handler.ResponseToReturn = responseMessage;
        using HttpClient client = new(handler);

        var clientCore = new ClientCore("modelId", "apikey", httpClient: client);

        ChatHistory chatHistory = [];
        chatHistory.Add(new ChatMessageContent(AuthorRole.User, "Hello"));

        var settings = new OpenAIPromptExecutionSettings()
        {
            FunctionChoiceBehavior = FunctionChoiceBehavior.Auto(
                autoInvoke: false,
                options: new FunctionChoiceBehaviorOptions
                {
                    RetainArgumentTypes = retain
                })
        };

        // Act
        var result = await clientCore.GetChatMessageContentsAsync("gpt-4", chatHistory, settings, new Kernel());

        // Assert
        var functionCalls = FunctionCallContent.GetFunctionCalls(result.Single()).ToArray();
        Assert.NotEmpty(functionCalls);

        var getCurrentWeatherFunctionCall = functionCalls.FirstOrDefault(call => call.FunctionName == "GetCurrentWeather");
        Assert.NotNull(getCurrentWeatherFunctionCall);

        var intArgumentsFunctionCall = functionCalls.FirstOrDefault(call => call.FunctionName == "IntArguments");
        Assert.NotNull(intArgumentsFunctionCall);

        if (retain)
        {
            var location = Assert.IsType<JsonElement>(getCurrentWeatherFunctionCall.Arguments?["location"]);
            Assert.Equal(JsonValueKind.String, location.ValueKind);
            Assert.Equal("Boston, MA", location.ToString());

            var age = Assert.IsType<JsonElement>(intArgumentsFunctionCall.Arguments?["age"]);
            Assert.Equal(JsonValueKind.Number, age.ValueKind);
            Assert.Equal(36, age.GetInt32());
        }
        else
        {
            var location = Assert.IsType<string>(getCurrentWeatherFunctionCall.Arguments?["location"]);
            Assert.Equal("Boston, MA", location);

            var age = Assert.IsType<string>(intArgumentsFunctionCall.Arguments?["age"]);
            Assert.Equal("36", age);
        }
    }

    internal sealed class ChatMessageContentWithFunctionCalls : TheoryData<ChatMessageContent, bool>
    {
        private static readonly ChatToolCall s_functionCallWithInvalidFunctionName = ChatToolCall.CreateFunctionToolCall(id: "call123", functionName: "bar.foo", functionArguments: BinaryData.FromString("{}"));

        private static readonly ChatToolCall s_functionCallWithValidFunctionName = ChatToolCall.CreateFunctionToolCall(id: "call123", functionName: "bar-foo", functionArguments: BinaryData.FromString("{}"));

        public ChatMessageContentWithFunctionCalls()
        {
            this.AddMessagesWithFunctionCallsWithInvalidFunctionName();
        }

        private void AddMessagesWithFunctionCallsWithInvalidFunctionName()
        {
            // Case when function calls are available via the `Tools` property.
            this.Add(new OpenAIChatMessageContent(AuthorRole.Assistant, "", "", [s_functionCallWithInvalidFunctionName]), true);

            // Case when function calls are available via the `ChatResponseMessage.FunctionToolCalls` metadata as an array of ChatToolCall type.
            this.Add(new ChatMessageContent(AuthorRole.Assistant, "", metadata: new Dictionary<string, object?>()
            {
                [OpenAIChatMessageContent.FunctionToolCallsProperty] = new ChatToolCall[] { s_functionCallWithInvalidFunctionName }
            }), true);

            // Case when function calls are available via the `ChatResponseMessage.FunctionToolCalls` metadata as an array of JsonElement type.
            this.Add(new ChatMessageContent(AuthorRole.Assistant, "", metadata: new Dictionary<string, object?>()
            {
                [OpenAIChatMessageContent.FunctionToolCallsProperty] = JsonSerializer.Deserialize<JsonElement>($$"""[{"Id": "{{s_functionCallWithInvalidFunctionName.Id}}", "Name": "{{s_functionCallWithInvalidFunctionName.FunctionName}}", "Arguments": "{{s_functionCallWithInvalidFunctionName.FunctionArguments}}"}]""")
            }), true);
        }

        private void AddMessagesWithFunctionCallsWithValidFunctionName()
        {
            // Case when function calls are available via the `Tools` property.
            this.Add(new OpenAIChatMessageContent(AuthorRole.Assistant, "", "", [s_functionCallWithValidFunctionName]), false);

            // Case when function calls are available via the `ChatResponseMessage.FunctionToolCalls` metadata as an array of ChatToolCall type.
            this.Add(new ChatMessageContent(AuthorRole.Assistant, "", metadata: new Dictionary<string, object?>()
            {
                [OpenAIChatMessageContent.FunctionToolCallsProperty] = new ChatToolCall[] { s_functionCallWithValidFunctionName }
            }), false);

            // Case when function calls are available via the `ChatResponseMessage.FunctionToolCalls` metadata as an array of JsonElement type.
            this.Add(new ChatMessageContent(AuthorRole.Assistant, "", metadata: new Dictionary<string, object?>()
            {
                [OpenAIChatMessageContent.FunctionToolCallsProperty] = JsonSerializer.Deserialize<JsonElement>($$"""[{"Id": "{{s_functionCallWithValidFunctionName.Id}}", "Name": "{{s_functionCallWithValidFunctionName.FunctionName}}", "Arguments": "{{s_functionCallWithValidFunctionName.FunctionArguments}}"}]""")
            }), false);
        }
    }
}
