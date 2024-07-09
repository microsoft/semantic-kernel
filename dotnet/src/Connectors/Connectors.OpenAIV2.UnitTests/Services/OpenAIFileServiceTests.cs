// Copyright (c) Microsoft. All rights reserved.

using System;
using System.IO;
using System.Linq;
using System.Net.Http;
using System.Text;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using Moq;
using Xunit;

namespace SemanticKernel.Connectors.OpenAI.UnitTests.Services;

/// <summary>
/// Unit tests for <see cref="OpenAITextToImageService"/> class.
/// </summary>
public sealed class OpenAIFileServiceTests : IDisposable
{
    private readonly HttpMessageHandlerStub _messageHandlerStub;
    private readonly HttpClient _httpClient;
    private readonly Mock<ILoggerFactory> _mockLoggerFactory;

    public OpenAIFileServiceTests()
    {
        this._messageHandlerStub = new HttpMessageHandlerStub();
        this._httpClient = new HttpClient(this._messageHandlerStub, false);
        this._mockLoggerFactory = new Mock<ILoggerFactory>();
    }

    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public void ConstructorWorksCorrectlyForOpenAI(bool includeLoggerFactory)
    {
        // Arrange & Act
        var service = includeLoggerFactory ?
            new OpenAIFileService("api-key", loggerFactory: this._mockLoggerFactory.Object) :
            new OpenAIFileService("api-key");
    }

    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public void ConstructorWorksCorrectlyForCustomEndpoint(bool includeLoggerFactory)
    {
        // Arrange & Act
        var service = includeLoggerFactory ?
            new OpenAIFileService(new Uri("http://localhost"), "api-key", loggerFactory: this._mockLoggerFactory.Object) :
            new OpenAIFileService(new Uri("http://localhost"), "api-key");
    }

    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public async Task DeleteFileWorksCorrectlyAsync(bool isCustomEndpoint)
    {
        // Arrange
        var service = this.CreateFileService(isCustomEndpoint);
        using var response = this.CreateSuccessResponse(
            """
            {
                "id": "123",
                "filename": "test.txt",
                "purpose": "assistants",
                "bytes": 120000,
                "created_at": 1677610602
            }
            """);

        this._messageHandlerStub.ResponseToReturn = response;

        // Act & Assert
        await service.DeleteFileAsync("file-id");
    }

    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public async Task DeleteFileFailsAsExpectedAsync(bool isCustomEndpoint)
    {
        // Arrange
        var service = this.CreateFileService(isCustomEndpoint);
        using var response = this.CreateFailedResponse();

        this._messageHandlerStub.ResponseToReturn = response;

        // Act & Assert
        await Assert.ThrowsAsync<HttpOperationException>(() => service.DeleteFileAsync("file-id"));
    }

    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public async Task GetFileWorksCorrectlyAsync(bool isCustomEndpoint)
    {
        // Arrange
        var service = this.CreateFileService(isCustomEndpoint);
        using var response = this.CreateSuccessResponse(
            """
            {
                "id": "123",
                "filename": "file.txt",
                "purpose": "assistants",
                "bytes": 120000,
                "created_at": 1677610602
            }
            """);

        this._messageHandlerStub.ResponseToReturn = response;

        // Act & Assert
        var file = await service.GetFileAsync("file-id");
        Assert.NotNull(file);
        Assert.NotEqual(string.Empty, file.Id);
        Assert.NotEqual(string.Empty, file.FileName);
        Assert.NotEqual(DateTime.MinValue, file.CreatedTimestamp);
        Assert.NotEqual(0, file.SizeInBytes);
    }

    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public async Task GetFileFailsAsExpectedAsync(bool isCustomEndpoint)
    {
        // Arrange
        var service = this.CreateFileService(isCustomEndpoint);
        using var response = this.CreateFailedResponse();
        this._messageHandlerStub.ResponseToReturn = response;

        // Act & Assert
        await Assert.ThrowsAsync<HttpOperationException>(() => service.GetFileAsync("file-id"));
    }

    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public async Task GetFilesWorksCorrectlyAsync(bool isCustomEndpoint)
    {
        // Arrange
        var service = this.CreateFileService(isCustomEndpoint);
        using var response = this.CreateSuccessResponse(
                    """
                    {
                        "data": [
                            {
                                "id": "123",
                                "filename": "file1.txt",
                                "purpose": "assistants",
                                "bytes": 120000,
                                "created_at": 1677610602
                            },
                            {
                                "id": "456",
                                "filename": "file2.txt",
                                "purpose": "assistants",
                                "bytes": 999,
                                "created_at": 1677610606
                            }
                        ]
                    }
                    """);

        this._messageHandlerStub.ResponseToReturn = response;

        // Act & Assert
        var files = (await service.GetFilesAsync()).ToArray();
        Assert.NotNull(files);
        Assert.NotEmpty(files);
    }

    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public async Task GetFilesFailsAsExpectedAsync(bool isCustomEndpoint)
    {
        // Arrange
        var service = this.CreateFileService(isCustomEndpoint);
        using var response = this.CreateFailedResponse();

        this._messageHandlerStub.ResponseToReturn = response;

        await Assert.ThrowsAsync<HttpOperationException>(() => service.GetFilesAsync());
    }

    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public async Task GetFileContentWorksCorrectlyAsync(bool isCustomEndpoint)
    {
        // Arrange
        var data = BinaryData.FromString("Hello AI!");
        var service = this.CreateFileService(isCustomEndpoint);
        this._messageHandlerStub.ResponseToReturn =
            new HttpResponseMessage(System.Net.HttpStatusCode.OK)
            {
                Content = new ByteArrayContent(data.ToArray())
            };

        // Act & Assert
        var content = await service.GetFileContentAsync("file-id");
        var result = content.Data!.Value;
        Assert.Equal(data.ToArray(), result.ToArray());
    }

    [Theory]
    [InlineData(false)]
    [InlineData(true)]
    public async Task UploadContentWorksCorrectlyAsync(bool isCustomEndpoint)
    {
        // Arrange
        var service = this.CreateFileService(isCustomEndpoint);
        using var response = this.CreateSuccessResponse(
            """
            {
                "id": "123",
                "filename": "test.txt",
                "purpose": "assistants",
                "bytes": 120000,
                "created_at": 1677610602
            }
            """);

        this._messageHandlerStub.ResponseToReturn = response;

        var settings = new OpenAIFileUploadExecutionSettings("test.txt", OpenAIFilePurpose.Assistants);

        var stream = new MemoryStream();
        var writer = new StreamWriter(stream);
        await writer.WriteLineAsync("test");
        await writer.FlushAsync();

        stream.Position = 0;

        var content = new BinaryContent(stream.ToArray(), "text/plain");

        // Act & Assert
        var file = await service.UploadContentAsync(content, settings);
        Assert.NotNull(file);
        Assert.NotEqual(string.Empty, file.Id);
        Assert.NotEqual(string.Empty, file.FileName);
        Assert.NotEqual(DateTime.MinValue, file.CreatedTimestamp);
        Assert.NotEqual(0, file.SizeInBytes);

        writer.Dispose();
        stream.Dispose();
    }

    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public async Task UploadContentFailsAsExpectedAsync(bool isCustomEndpoint)
    {
        // Arrange
        var service = this.CreateFileService(isCustomEndpoint);
        using var response = this.CreateFailedResponse();

        this._messageHandlerStub.ResponseToReturn = response;

        var settings = new OpenAIFileUploadExecutionSettings("test.txt", OpenAIFilePurpose.Assistants);

        var stream = new MemoryStream();
        var writer = new StreamWriter(stream);
        await writer.WriteLineAsync("test");
        await writer.FlushAsync();

        stream.Position = 0;

        var content = new BinaryContent(stream.ToArray(), "text/plain");

        // Act & Assert
        await Assert.ThrowsAsync<HttpOperationException>(() => service.UploadContentAsync(content, settings));

        writer.Dispose();
        stream.Dispose();
    }

    private OpenAIFileService CreateFileService(bool isCustomEndpoint = false)
    {
        return
            isCustomEndpoint ?
                new OpenAIFileService(new Uri("http://localhost"), "api-key", httpClient: this._httpClient) :
                new OpenAIFileService("api-key", "organization", this._httpClient);
    }

    private HttpResponseMessage CreateSuccessResponse(string payload)
    {
        return
            new HttpResponseMessage(System.Net.HttpStatusCode.OK)
            {
                Content =
                    new StringContent(
                        payload,
                        Encoding.UTF8,
                        "application/json")
            };
    }

    private HttpResponseMessage CreateFailedResponse(string? payload = null)
    {
        return
            new HttpResponseMessage(System.Net.HttpStatusCode.BadRequest)
            {
                Content =
                    string.IsNullOrEmpty(payload) ?
                        null :
                        new StringContent(
                            payload,
                            Encoding.UTF8,
                            "application/json")
            };
    }

    public void Dispose()
    {
        this._httpClient.Dispose();
        this._messageHandlerStub.Dispose();
    }
}
