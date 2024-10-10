// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Net.Http;
using System.Text;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.AssemblyAI;
using Xunit;

namespace SemanticKernel.Connectors.AssemblyAI.UnitTests;

/// <summary>
/// Unit tests for <see cref="AssemblyAIAudioToTextService"/> class.
/// </summary>
public sealed class AssemblyAIAudioToTextServiceTests : IDisposable
{
    private const string TranscriptGuid = "0D0446CE-5C41-476F-9642-61F425FEA477";

    private const string UploadFileResponseContent =
        """
        {
            "upload_url": "http://localhost/path/to/file.mp3"
        }
        """;

    private const string CreateTranscriptResponseContent =
        $$"""
          {
            "id": "{{TranscriptGuid}}",
            "text": null,
            "status": "queued"
          }
          """;

    private const string TranscriptCompletedResponseContent =
        $$"""
          {
            "id": "{{TranscriptGuid}}",
            "text": "Test audio-to-text response",
            "status": "completed"
          }
          """;

    private const string ExpectedTranscriptText = "Test audio-to-text response";

    private readonly MultipleHttpMessageHandlerStub _messageHandlerStub;
    private readonly HttpClient _httpClient;

    public AssemblyAIAudioToTextServiceTests()
    {
        this._messageHandlerStub = new MultipleHttpMessageHandlerStub();
        this._httpClient = new HttpClient(this._messageHandlerStub, false);
    }

    [Fact]
    public void ConstructorWithHttpClientWorksCorrectly()
    {
        // Arrange & Act
        var service = new AssemblyAIAudioToTextService("api-key", httpClient: this._httpClient);

        // Assert
        Assert.NotNull(service);
    }

    [Fact]
    public async Task GetTextContentByDefaultWorksCorrectlyAsync()
    {
        // Arrange
        var service = new AssemblyAIAudioToTextService("api-key", httpClient: this._httpClient);
        using var uploadFileResponse = new HttpResponseMessage(System.Net.HttpStatusCode.OK);
        uploadFileResponse.Content = new StringContent(UploadFileResponseContent);
        using var transcribeResponse = new HttpResponseMessage(System.Net.HttpStatusCode.OK);
        transcribeResponse.Content = new StringContent(CreateTranscriptResponseContent);
        using var transcribedResponse = new HttpResponseMessage(System.Net.HttpStatusCode.OK);
        transcribedResponse.Content = new StringContent(TranscriptCompletedResponseContent);
        this._messageHandlerStub.ResponsesToReturn =
        [
            uploadFileResponse,
            transcribeResponse,
            transcribedResponse
        ];

        // Act
        var result = await service.GetTextContentsAsync(
            new AudioContent(new BinaryData("data"))
        ).ConfigureAwait(true);

        // Assert
        Assert.NotNull(result);
        Assert.Single(result);
        Assert.Equal(ExpectedTranscriptText, result[0].Text);
    }

    [Fact]
    public async Task GetTextContentByUrlWorksCorrectlyAsync()
    {
        // Arrange
        var service = new AssemblyAIAudioToTextService("api-key", httpClient: this._httpClient);
        using var transcribeResponse = new HttpResponseMessage(System.Net.HttpStatusCode.OK);
        transcribeResponse.Content = new StringContent(CreateTranscriptResponseContent);
        using var transcribedResponse = new HttpResponseMessage(System.Net.HttpStatusCode.OK);
        transcribedResponse.Content = new StringContent(TranscriptCompletedResponseContent);
        this._messageHandlerStub.ResponsesToReturn = [transcribeResponse, transcribedResponse];

        // Act
        var result = await service.GetTextContentsAsync(
            new AudioContent(new Uri("https://storage.googleapis.com/aai-docs-samples/nbc.mp3"))
        ).ConfigureAwait(true);

        // Assert
        Assert.NotNull(result);
        Assert.Single(result);
        Assert.Equal(ExpectedTranscriptText, result[0].Text);
    }

    [Fact]
    public async Task HttpErrorShouldThrowWithErrorMessageAsync()
    {
        // Arrange
        var service = new AssemblyAIAudioToTextService("api-key", httpClient: this._httpClient);
        using var uploadFileResponse = new HttpResponseMessage(System.Net.HttpStatusCode.InternalServerError);
        this._messageHandlerStub.ResponsesToReturn =
        [
            uploadFileResponse
        ];

        // Act & Assert
        await Assert.ThrowsAsync<HttpOperationException>(
            async () => await service.GetTextContentsAsync(
                new AudioContent(new BinaryData("data"))
            ).ConfigureAwait(true)
        ).ConfigureAwait(true);
    }

    [Fact]
    public async Task JsonErrorShouldThrowWithErrorMessageAsync()
    {
        // Arrange
        var service = new AssemblyAIAudioToTextService("api-key", httpClient: this._httpClient);
        using var uploadFileResponse = new HttpResponseMessage(System.Net.HttpStatusCode.Unauthorized);
        const string ErrorMessage = "Bad API key";
        uploadFileResponse.Content = new StringContent(
            $$"""
              {
                  "error": "{{ErrorMessage}}"
              }
              """,
            Encoding.UTF8,
            "application/json"
        );
        this._messageHandlerStub.ResponsesToReturn =
        [
            uploadFileResponse
        ];

        // Act & Assert
        await Assert.ThrowsAsync<HttpOperationException>(
            async () => await service.GetTextContentsAsync(
                new AudioContent(new BinaryData("data"))
            ).ConfigureAwait(true)
        ).ConfigureAwait(true);
    }

    public void Dispose()
    {
        this._httpClient.Dispose();
        this._messageHandlerStub.Dispose();
    }
}
