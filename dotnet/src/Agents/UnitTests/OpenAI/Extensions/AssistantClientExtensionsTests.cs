// Copyright (c) Microsoft. All rights reserved.
using System;
using System.ClientModel;
using System.Collections.Generic;
using System.Net;
using System.Net.Http;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents.OpenAI;
using Microsoft.SemanticKernel.ChatCompletion;
using OpenAI.Assistants;
using Xunit;

namespace SemanticKernel.Agents.UnitTests.OpenAI.Extensions;

/// <summary>
/// Unit testing of <see cref="OpenAIAssistantAgent"/>.
/// </summary>
public sealed class AssistantClientExtensionsTests : IDisposable
{
    private const string ModelValue = "testmodel";

    private readonly HttpMessageHandlerStub _messageHandlerStub;
    private readonly HttpClient _httpClient;
    private readonly OpenAIClientProvider _clientProvider;

    /// <summary>
    /// Verify the assistant creation with default values.
    /// </summary>
    [Fact]
    public async Task VerifyCreateAssistantAsync()
    {
        // Arrange
        this.SetupResponse(HttpStatusCode.OK, OpenAIAssistantResponseContent.AssistantDefinition(ModelValue));

        // Act
        Assistant definition = await this._clientProvider.AssistantClient.CreateAssistantAsync(modelId: ModelValue);

        // Assert
        Assert.NotNull(definition);
        Assert.Equal(ModelValue, definition.Model);
    }

    /// <summary>
    /// Verify the assistant creation with name, instructions, and description.
    /// </summary>
    [Fact]
    public async Task VerifyCreateAssistantWithIdentityAsync()
    {
        // Arrange
        const string NameValue = "test name";
        const string DescriptionValue = "test instructions";
        const string InstructionsValue = "test description";

        this.SetupResponse(
            HttpStatusCode.OK,
            OpenAIAssistantResponseContent.AssistantDefinition(
                ModelValue,
                name: NameValue,
                instructions: InstructionsValue,
                description: DescriptionValue));

        // Act
        Assistant definition = await this._clientProvider.AssistantClient.CreateAssistantAsync(
            modelId: ModelValue,
            name: NameValue,
            instructions: InstructionsValue,
            description: DescriptionValue);

        // Assert
        Assert.NotNull(definition);
        Assert.Equal(NameValue, definition.Name);
        Assert.Equal(DescriptionValue, definition.Description);
        Assert.Equal(InstructionsValue, definition.Instructions);
    }

    /// <summary>
    /// Verify the assistant creation with name, instructions, and description.
    /// </summary>
    [Fact]
    public async Task VerifyCreateAssistantWithTemplateAsync()
    {
        // Arrange
        const string NameValue = "test name";
        const string DescriptionValue = "test instructions";
        const string InstructionsValue = "test description";
        PromptTemplateConfig templateConfig =
            new(InstructionsValue)
            {
                Name = NameValue,
                Description = InstructionsValue,
            };
        this.SetupResponse(
            HttpStatusCode.OK,
            OpenAIAssistantResponseContent.AssistantDefinition(
                ModelValue,
                name: NameValue,
                instructions: InstructionsValue,
                description: DescriptionValue));

        // Act
        Assistant definition = await this._clientProvider.AssistantClient.CreateAssistantFromTemplateAsync(modelId: ModelValue, templateConfig);

        // Assert
        Assert.NotNull(definition);
        Assert.Equal(NameValue, definition.Name);
        Assert.Equal(DescriptionValue, definition.Description);
        Assert.Equal(InstructionsValue, definition.Instructions);
    }

    /// <summary>
    /// Verify the assistant creation with code-interpreter enabled.
    /// </summary>
    [Fact]
    public async Task VerifyCreateAssistantWithCodeInterpreterAsync()
    {
        // Arrange
        this.SetupResponse(
            HttpStatusCode.OK,
            OpenAIAssistantResponseContent.AssistantDefinition(ModelValue, enableCodeInterpreter: true));

        // Act
        Assistant definition = await this._clientProvider.AssistantClient.CreateAssistantAsync(
            modelId: ModelValue,
            enableCodeInterpreter: true);

        // Assert
        Assert.NotNull(definition);
        Assert.Single(definition.Tools);
        Assert.IsType<CodeInterpreterToolDefinition>(definition.Tools[0]);
    }

    /// <summary>
    /// Verify the assistant creation with code-interpreter files specified.
    /// </summary>
    [Fact]
    public async Task VerifyCreateAssistantWithCodeInterpreterFilesAsync()
    {
        // Arrange
        string[] fileIds = ["file1", "file2"];
        this.SetupResponse(
            HttpStatusCode.OK,
            OpenAIAssistantResponseContent.AssistantDefinition(ModelValue, codeInterpreterFileIds: fileIds));

        // Act
        Assistant definition = await this._clientProvider.AssistantClient.CreateAssistantAsync(
            modelId: ModelValue,
            codeInterpreterFileIds: fileIds);

        // Assert
        Assert.NotNull(definition);
        Assert.Single(definition.Tools);
        Assert.IsType<CodeInterpreterToolDefinition>(definition.Tools[0]);
        Assert.NotNull(definition.ToolResources.CodeInterpreter);
        Assert.Equal(2, definition.ToolResources.CodeInterpreter.FileIds.Count);
    }

    /// <summary>
    /// Verify the assistant creation with file-search enabled.
    /// </summary>
    [Fact]
    public async Task VerifyCreateAssistantWithFileSearchAsync()
    {
        // Arrange
        this.SetupResponse(
            HttpStatusCode.OK,
            OpenAIAssistantResponseContent.AssistantDefinition(ModelValue, enableFileSearch: true));

        // Act
        Assistant definition = await this._clientProvider.AssistantClient.CreateAssistantAsync(
            modelId: ModelValue,
            enableFileSearch: true);

        // Assert
        Assert.NotNull(definition);
        Assert.Single(definition.Tools);
        Assert.IsType<FileSearchToolDefinition>(definition.Tools[0]);
    }

    /// <summary>
    /// Verify the assistant creation with vector-store specified.
    /// </summary>
    [Fact]
    public async Task VerifyCreateAssistantWithVectorStoreAsync()
    {
        // Arrange
        const string VectorStoreValue = "test store";
        this.SetupResponse(
            HttpStatusCode.OK,
            OpenAIAssistantResponseContent.AssistantDefinition(ModelValue, vectorStoreId: VectorStoreValue));

        // Act
        Assistant definition = await this._clientProvider.AssistantClient.CreateAssistantAsync(
            modelId: ModelValue,
            vectorStoreId: VectorStoreValue);

        // Assert
        Assert.NotNull(definition);
        Assert.Single(definition.Tools);
        Assert.IsType<FileSearchToolDefinition>(definition.Tools[0]);
        Assert.NotNull(definition.ToolResources.FileSearch);
        Assert.Single(definition.ToolResources.FileSearch.VectorStoreIds);
    }

    /// <summary>
    /// Verify the invocation and response of <see cref="OpenAIAssistantAgent.CreateAsync"/>
    /// for an agent with temperature defined.
    /// </summary>
    [Fact]
    public async Task VerifyCreateAssistantWithTemperatureAsync()
    {
        // Arrange
        const float TemperatureValue = 0.5F;
        this.SetupResponse(HttpStatusCode.OK, OpenAIAssistantResponseContent.AssistantDefinition("testmodel", temperature: TemperatureValue));

        // Act
        Assistant definition = await this._clientProvider.AssistantClient.CreateAssistantAsync(
            modelId: "testmodel",
            temperature: TemperatureValue);

        // Assert
        Assert.NotNull(definition);
        Assert.Equal(TemperatureValue, definition.Temperature);
    }

    /// <summary>
    /// Verify the invocation and response of <see cref="OpenAIAssistantAgent.CreateAsync"/>
    /// for an agent with topP defined.
    /// </summary>
    [Fact]
    public async Task VerifyCreateAssistantWithTopPAsync()
    {
        // Arrange
        const float TopPValue = 2.0F;
        this.SetupResponse(HttpStatusCode.OK, OpenAIAssistantResponseContent.AssistantDefinition("testmodel", topP: TopPValue));

        // Act
        Assistant definition = await this._clientProvider.AssistantClient.CreateAssistantAsync(
            modelId: "testmodel",
            topP: TopPValue);

        // Assert
        Assert.NotNull(definition);
        Assert.Equal(TopPValue, definition.NucleusSamplingFactor);
    }

    /// <summary>
    /// Verify the invocation and response of <see cref="OpenAIAssistantAgent.CreateAsync"/>
    /// for an agent with execution settings and meta-data.
    /// </summary>
    [Fact]
    public async Task VerifyCreateAssistantWithMetadataAsync()
    {
        // Arrange
        Dictionary<string, string> metadata =
            new()
            {
                { "a", "1" },
                { "b", "2" },
            };
        this.SetupResponse(HttpStatusCode.OK, OpenAIAssistantResponseContent.AssistantDefinition("testmodel", metadata: metadata));

        // Act
        Assistant definition = await this._clientProvider.AssistantClient.CreateAssistantAsync(
            modelId: "testmodel",
            metadata: metadata);

        // Assert
        Assert.NotNull(definition);
        Assert.NotEmpty(definition.Metadata);
    }

    /// <summary>
    /// Verify the deletion of assistant.
    /// </summary>
    [Fact]
    public async Task VerifyDeleteAssistantAsync()
    {
        // Arrange
        this.SetupResponse(HttpStatusCode.OK, OpenAIAssistantResponseContent.DeleteAgent);

        // Act
        AssistantDeletionResult result = await this._clientProvider.AssistantClient.DeleteAssistantAsync("testid");

        // Assert
        Assert.True(result.Deleted);
    }

    /// <summary>
    /// Verify the creating a thread.
    /// </summary>
    [Fact]
    public async Task VerifyCreateThreadAsync()
    {
        // Arrange
        this.SetupResponse(HttpStatusCode.OK, OpenAIAssistantResponseContent.CreateThread);

        // Act
        string threadId = await this._clientProvider.AssistantClient.CreateThreadAsync(messages: null);

        // Assert
        Assert.NotNull(threadId);
    }

    /// <summary>
    /// Verify the creating a thread with messages.
    /// </summary>
    [Fact]
    public async Task VerifyCreateThreadWithMessagesAsync()
    {
        // Arrange
        this.SetupResponse(HttpStatusCode.OK, OpenAIAssistantResponseContent.CreateThread);

        // Act
        string threadId = await this._clientProvider.AssistantClient.CreateThreadAsync(messages: [new ChatMessageContent(AuthorRole.User, "test")]);

        // Assert
        Assert.NotNull(threadId);
    }

    /// <summary>
    /// Verify the creating a thread with metadata.
    /// </summary>
    [Fact]
    public async Task VerifyCreateThreadWithMetadataAsync()
    {
        // Arrange
        this.SetupResponse(HttpStatusCode.OK, OpenAIAssistantResponseContent.CreateThread);
        Dictionary<string, string> metadata = new() { { "a", "1" }, { "b", "2" } };

        // Act
        string threadId = await this._clientProvider.AssistantClient.CreateThreadAsync(metadata: metadata);

        // Assert
        Assert.NotNull(threadId);
    }

    /// <inheritdoc/>
    public void Dispose()
    {
        this._messageHandlerStub.Dispose();
        this._httpClient.Dispose();
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="OpenAIAssistantAgentTests"/> class.
    /// </summary>
    public AssistantClientExtensionsTests()
    {
        this._messageHandlerStub = new HttpMessageHandlerStub();
        this._httpClient = new HttpClient(this._messageHandlerStub, disposeHandler: false);
        this._clientProvider = OpenAIClientProvider.ForOpenAI(apiKey: new ApiKeyCredential("fakekey"), endpoint: null, this._httpClient);
    }

    private void SetupResponse(HttpStatusCode statusCode, string content) =>
        this._messageHandlerStub.SetupResponses(statusCode, content);
}
