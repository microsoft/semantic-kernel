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
public sealed class AssemblyAIFileServiceTests : IDisposable
{
    private const string UploadedFileUrl = "http://localhost/path/to/file.mp3";

    private const string UploadFileResponseContent =
        $$"""
          {
              "upload_url": "{{UploadedFileUrl}}"
          }
          """;

    private readonly MultipleHttpMessageHandlerStub _messageHandlerStub;
    private readonly HttpClient _httpClient;

    public AssemblyAIFileServiceTests()
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
    public async Task UploadFileAsync()
    {
        // Arrange
        var service = new AssemblyAIFileService("api-key", httpClient: this._httpClient);
        using var uploadFileResponse = new HttpResponseMessage(System.Net.HttpStatusCode.OK);
        uploadFileResponse.Content = new StringContent(UploadFileResponseContent);
        using var transcribeResponse = new HttpResponseMessage(System.Net.HttpStatusCode.OK);
        this._messageHandlerStub.ResponsesToReturn =
        [
            uploadFileResponse,
        ];
        using var stream = new BinaryData("data").ToStream();

        // Act
        var result = await service.UploadAsync(stream).ConfigureAwait(true);

        // Assert
        Assert.NotNull(result);
        Assert.Null(result.Data);
        Assert.Equal(new Uri(UploadedFileUrl), result.Uri);
    }

    [Fact]
    public async Task HttpErrorShouldThrowWithErrorMessageAsync()
    {
        // Arrange
        var service = new AssemblyAIFileService("api-key", httpClient: this._httpClient);
        using var uploadFileResponse = new HttpResponseMessage(System.Net.HttpStatusCode.InternalServerError);
        this._messageHandlerStub.ResponsesToReturn =
        [
            uploadFileResponse
        ];
        using var stream = new BinaryData("data").ToStream();
        // Act & Assert
        await Assert.ThrowsAsync<HttpOperationException>(
            async () => await service.UploadAsync(stream).ConfigureAwait(true)
        ).ConfigureAwait(true);
    }

    [Fact]
    public async Task JsonErrorShouldThrowWithErrorMessageAsync()
    {
        // Arrange
        var service = new AssemblyAIFileService("api-key", httpClient: this._httpClient);
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
        using var stream = new BinaryData("data").ToStream();

        // Act & Assert
        await Assert.ThrowsAsync<HttpOperationException>(
            async () => await service.UploadAsync(stream).ConfigureAwait(true)
        ).ConfigureAwait(true);
    }

    public void Dispose()
    {
        this._httpClient.Dispose();
        this._messageHandlerStub.Dispose();
    }
}
