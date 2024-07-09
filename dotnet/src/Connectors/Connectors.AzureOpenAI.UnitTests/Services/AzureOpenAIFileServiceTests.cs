// Copyright (c) Microsoft. All rights reserved.

using System;
using System.IO;
using System.Linq;
using System.Net.Http;
using System.Text;
using System.Threading.Tasks;
using Azure.AI.OpenAI;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.AzureOpenAI;
using Moq;

namespace SemanticKernel.Connectors.OpenAI.UnitTests.Services;

/// <summary>
/// Unit tests for <see cref="AzureOpenAIFileService"/> class.
/// </summary>
public sealed class AzureOpenAIFileServiceTests : IDisposable
{
    private readonly HttpMessageHandlerStub _messageHandlerStub;
    private readonly HttpClient _httpClient;
    private readonly Mock<ILoggerFactory> _mockLoggerFactory;

    public AzureOpenAIFileServiceTests()
    {
        this._messageHandlerStub = new HttpMessageHandlerStub();
        this._httpClient = new HttpClient(this._messageHandlerStub, false);
        this._mockLoggerFactory = new Mock<ILoggerFactory>();
    }

    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public void ConstructorWithEndpointWorksCorrectly(bool includeLoggerFactory)
    {
        // Arrange & Act
        var _ = includeLoggerFactory ?
            new AzureOpenAIFileService(new Uri("https://localhost"), "api-key", loggerFactory: this._mockLoggerFactory.Object) :
            new AzureOpenAIFileService(new Uri("https://localhost"), "api-key");
    }

    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public void ConstructorWithOpenAIClientWorksCorrectly(bool includeLoggerFactory)
    {
        // Arrange & Act
        var client = new AzureOpenAIClient(new Uri("http://host"), "key");
        var _ = includeLoggerFactory ?
            new AzureOpenAIFileService(client, loggerFactory: this._mockLoggerFactory.Object) :
            new AzureOpenAIFileService(client);
    }

    [Fact]
    public async Task DeleteFileWorksCorrectlyAsync()
    {
        // Arrange
        var service = new AzureOpenAIFileService(new Uri("https://localhost"), "api-key", httpClient: this._httpClient);
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

    [Fact]
    public async Task DeleteFileFailsAsExpectedAsync()
    {
        // Arrange
        var service = new AzureOpenAIFileService(new Uri("https://localhost"), "api-key", httpClient: this._httpClient);
        using var response = this.CreateFailedResponse();

        this._messageHandlerStub.ResponseToReturn = response;

        // Act & Assert
        await Assert.ThrowsAsync<HttpOperationException>(() => service.DeleteFileAsync("file-id"));
    }

    [Fact]
    public async Task GetFileWorksCorrectlyAsync()
    {
        // Arrange
        var service = new AzureOpenAIFileService(new Uri("https://localhost"), "api-key", httpClient: this._httpClient);
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

    [Fact]
    public async Task GetFileFailsAsExpectedAsync()
    {
        // Arrange
        var service = new AzureOpenAIFileService(new Uri("https://localhost"), "api-key", httpClient: this._httpClient);
        using var response = this.CreateFailedResponse();
        this._messageHandlerStub.ResponseToReturn = response;

        // Act & Assert
        await Assert.ThrowsAsync<HttpOperationException>(() => service.GetFileAsync("file-id"));
    }

    [Fact(Skip = "Temporarily skipped until the issue 'Value cannot be null. (Parameter 'purpose')' is fixed. See: https://github.com/microsoft/semantic-kernel/issues/7167")]
    public async Task GetFilesWorksCorrectlyAsync()
    {
        // Arrange
        var service = new AzureOpenAIFileService(new Uri("https://localhost"), "api-key", httpClient: this._httpClient);
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
        var files = (await service.GetFilesAsync(filePurpose: null)).ToArray();
        Assert.NotNull(files);
        Assert.NotEmpty(files);
    }

    [Fact(Skip = "Temporarily skipped until the issue 'Value cannot be null. (Parameter 'purpose')' is fixed. See: https://github.com/microsoft/semantic-kernel/issues/7167")]
    public async Task GetFilesFailsAsExpectedAsync()
    {
        // Arrange
        var service = new AzureOpenAIFileService(new Uri("https://localhost"), "api-key", httpClient: this._httpClient);
        using var response = this.CreateFailedResponse();

        this._messageHandlerStub.ResponseToReturn = response;

        await Assert.ThrowsAsync<HttpOperationException>(() => service.GetFilesAsync());
    }

    [Fact]
    public async Task GetFileContentWorksCorrectlyAsync()
    {
        // Arrange
        var data = BinaryData.FromString("Hello AI!");
        var service = new AzureOpenAIFileService(new Uri("https://localhost"), "api-key", httpClient: this._httpClient);
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

    [Fact]
    public async Task UploadContentWorksCorrectlyAsync()
    {
        // Arrange
        var service = new AzureOpenAIFileService(new Uri("https://localhost"), "api-key", httpClient: this._httpClient);
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

        var settings = new AzureOpenAIFileUploadExecutionSettings("test.txt", AzureOpenAIFileUploadPurpose.Assistants);

        await using var stream = new MemoryStream();
        await using (var writer = new StreamWriter(stream, leaveOpen: true))
        {
            await writer.WriteLineAsync("test");
            await writer.FlushAsync();
        }

        stream.Position = 0;

        var content = new BinaryContent(stream.ToArray(), "text/plain");

        // Act & Assert
        var file = await service.UploadContentAsync(content, settings);
        Assert.NotNull(file);
        Assert.NotEqual(string.Empty, file.Id);
        Assert.NotEqual(string.Empty, file.FileName);
        Assert.NotEqual(DateTime.MinValue, file.CreatedTimestamp);
        Assert.NotEqual(0, file.SizeInBytes);
    }

    [Fact]
    public async Task UploadContentFailsAsExpectedAsync()
    {
        // Arrange
        var service = new AzureOpenAIFileService(new Uri("https://localhost"), "api-key", httpClient: this._httpClient);

        using var response = this.CreateFailedResponse();

        this._messageHandlerStub.ResponseToReturn = response;

        var settings = new AzureOpenAIFileUploadExecutionSettings("test.txt", AzureOpenAIFileUploadPurpose.Assistants);

        await using var stream = new MemoryStream();
        await using (var writer = new StreamWriter(stream, leaveOpen: true))
        {
            await writer.WriteLineAsync("test");
            await writer.FlushAsync();
        }

        stream.Position = 0;

        var content = new BinaryContent(stream.ToArray(), "text/plain");

        // Act & Assert
        await Assert.ThrowsAsync<HttpOperationException>(() => service.UploadContentAsync(content, settings));
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
