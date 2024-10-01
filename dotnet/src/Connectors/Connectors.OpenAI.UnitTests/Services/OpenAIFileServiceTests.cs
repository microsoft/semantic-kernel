﻿// Copyright (c) Microsoft. All rights reserved.

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

namespace SemanticKernel.Connectors.OpenAI.UnitTests.Files;

/// <summary>
/// Unit tests for <see cref="OpenAITextToImageService"/> class.
/// </summary>
[Obsolete("This class is deprecated and will be removed in a future version.")]
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

        // Assert
        Assert.NotNull(service);
    }

    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public void ConstructorWorksCorrectlyForAzure(bool includeLoggerFactory)
    {
        // Arrange & Act
        var service = includeLoggerFactory ?
            new OpenAIFileService(new Uri("http://localhost"), "api-key", loggerFactory: this._mockLoggerFactory.Object) :
            new OpenAIFileService(new Uri("http://localhost"), "api-key");

        // Assert
        Assert.NotNull(service);
    }

    [Theory]
    [InlineData(true, true)]
    [InlineData(false, true)]
    [InlineData(true, false)]
    [InlineData(false, false)]
    public async Task DeleteFileWorksCorrectlyAsync(bool isAzure, bool isFailedRequest)
    {
        // Arrange
        var service = this.CreateFileService(isAzure);
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
    [InlineData(true, true)]
    [InlineData(false, true)]
    [InlineData(true, false)]
    [InlineData(false, false)]
    public async Task GetFileWorksCorrectlyAsync(bool isAzure, bool isFailedRequest)
    {
        // Arrange
        var service = this.CreateFileService(isAzure);
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
    [InlineData(true, true)]
    [InlineData(false, true)]
    [InlineData(true, false)]
    [InlineData(false, false)]
    public async Task GetFilesWorksCorrectlyAsync(bool isAzure, bool isFailedRequest)
    {
        // Arrange
        var service = this.CreateFileService(isAzure);
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

    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public async Task GetFileContentWorksCorrectlyAsync(bool isAzure)
    {
        // Arrange
        var data = BinaryData.FromString("Hello AI!");
        var service = this.CreateFileService(isAzure);
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
    [InlineData(true, true)]
    [InlineData(false, true)]
    [InlineData(true, false)]
    [InlineData(false, false)]
    public async Task UploadContentWorksCorrectlyAsync(bool isAzure, bool isFailedRequest)
    {
        // Arrange
        var service = this.CreateFileService(isAzure);
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

        var content = new BinaryContent(stream.ToArray(), "text/plain");

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

    private OpenAIFileService CreateFileService(bool isAzure = false)
    {
        return
            isAzure ?
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
