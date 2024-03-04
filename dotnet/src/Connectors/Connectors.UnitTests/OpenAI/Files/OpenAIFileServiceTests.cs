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

namespace SemanticKernel.Connectors.UnitTests.OpenAI.Files;

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
    public void ConstructorWorksCorrectly(bool includeLoggerFactory)
    {
        // Arrange & Act
        var service = includeLoggerFactory ?
            new OpenAIFileService("api-key", "organization", loggerFactory: this._mockLoggerFactory.Object) :
            new OpenAIFileService("api-key", "organization");

        // Assert
        Assert.NotNull(service);
    }

    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public async Task DeleteFileWorksCorrectlyAsync(bool isFailedRequest)
    {
        // Arrange
        var service = new OpenAIFileService("api-key", "organization", this._httpClient);
        using var response =
            isFailedRequest ?
                this.CreateFailedResponse() :
                this.CreateSuccessResponse(
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
        if (isFailedRequest)
        {
            await Assert.ThrowsAsync<HttpOperationException>(() => service.DeleteFileAsync("file-id"));
        }
        else
        {
            await service.DeleteFileAsync("file-id");
        }
    }

    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public async Task GetFileWorksCorrectlyAsync(bool isFailedRequest)
    {
        // Arrange
        var service = new OpenAIFileService("api-key", "organization", this._httpClient);
        using var response =
            isFailedRequest ?
                this.CreateFailedResponse() :
                this.CreateSuccessResponse(
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
        if (isFailedRequest)
        {
            await Assert.ThrowsAsync<HttpOperationException>(() => service.GetFileAsync("file-id"));
        }
        else
        {
            var file = await service.GetFileAsync("file-id");
            Assert.NotNull(file);
            Assert.NotEqual(string.Empty, file.Id);
            Assert.NotEqual(string.Empty, file.FileName);
            Assert.NotEqual(DateTime.MinValue, file.CreatedTimestamp);
            Assert.NotEqual(0, file.SizeInBytes);
        }
    }

    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public async Task GetFilesWorksCorrectlyAsync(bool isFailedRequest)
    {
        // Arrange
        var service = new OpenAIFileService("api-key", "organization", this._httpClient);
        using var response =
            isFailedRequest ?
                this.CreateFailedResponse() :
                this.CreateSuccessResponse(
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
        if (isFailedRequest)
        {
            await Assert.ThrowsAsync<HttpOperationException>(() => service.GetFilesAsync());
        }
        else
        {
            var files = (await service.GetFilesAsync()).ToArray();
            Assert.NotNull(files);
            Assert.NotEmpty(files);
        }
    }

    [Fact]
    public async Task GetFileContentWorksCorrectlyAsync()
    {
        // Arrange
        var data = BinaryData.FromString("Hello AI!");
        var service = new OpenAIFileService("api-key", "organization", this._httpClient);
        this._messageHandlerStub.ResponseToReturn =
            new HttpResponseMessage(System.Net.HttpStatusCode.OK)
            {
                Content = new ByteArrayContent(data.ToArray())
            };

        // Act & Assert
        var content = service.GetFileContent("file-id");
        var result = await content.GetContentAsync();
        Assert.Equal(data.ToArray(), result.ToArray());
    }

    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public async Task UploadContentWorksCorrectlyAsync(bool isFailedRequest)
    {
        // Arrange
        var service = new OpenAIFileService("api-key", "organization", this._httpClient);
        using var response =
            isFailedRequest ?
                this.CreateFailedResponse() :
                this.CreateSuccessResponse(
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

        await using var stream = new MemoryStream();
        await using (var writer = new StreamWriter(stream, leaveOpen: true))
        {
            await writer.WriteLineAsync("test");
            await writer.FlushAsync();
        }

        stream.Position = 0;

        var content = new BinaryContent(() => Task.FromResult<Stream>(stream));

        // Act & Assert
        if (isFailedRequest)
        {
            await Assert.ThrowsAsync<HttpOperationException>(() => service.UploadContentAsync(content, settings));
        }
        else
        {
            var file = await service.UploadContentAsync(content, settings);
            Assert.NotNull(file);
            Assert.NotEqual(string.Empty, file.Id);
            Assert.NotEqual(string.Empty, file.FileName);
            Assert.NotEqual(DateTime.MinValue, file.CreatedTimestamp);
            Assert.NotEqual(0, file.SizeInBytes);
        }
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
