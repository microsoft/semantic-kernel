// Copyright (c) Microsoft. All rights reserved.

using System;
using System.IO;
using System.Net;
using System.Net.Http;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Plugins.Core;
using Microsoft.SemanticKernel.Plugins.Core.CodeInterpreter;
using Moq;
using Moq.Protected;
using Xunit;

namespace SemanticKernel.Plugins.UnitTests.Core;

public sealed class SessionsPythonPluginTests : IDisposable
{
    private readonly HttpClient _httpClient;
    private readonly HttpMessageHandlerStub _messageHandlerStub;
    private const string CodeExecutionTestDataFilePath = "./TestData/sessions_python_plugin_code_execution.json";
    private const string ListFilesTestDataFilePath = "./TestData/sessions_python_plugin_file_list.json";
    private const string UpdaloadFileTestDataFilePath = "./TestData/sessions_python_plugin_file_upload.json";
    private const string FileTestDataFilePath = "./TestData/sessions_python_plugin_file.txt";

    private readonly SessionPythonSettings _defaultSettings = new()
    {
        Endpoint = new Uri("http://localhost:8888"),
        CodeExecutionType = SessionPythonSettings.CodeExecutionTypeSetting.Synchronous,
        CodeInputType = SessionPythonSettings.CodeInputTypeSetting.Inline
    };

    private readonly IHttpClientFactory _httpClientFactory;

    public SessionsPythonPluginTests()
    {
        this._messageHandlerStub = new HttpMessageHandlerStub();
        this._httpClient = new HttpClient(this._messageHandlerStub, false);

        var httpClientFactoryMock = new Mock<IHttpClientFactory>();
        httpClientFactoryMock.Setup(f => f.CreateClient(It.IsAny<string>())).Returns(this._httpClient);

        this._httpClientFactory = httpClientFactoryMock.Object;
    }
    private readonly HttpResponseMessage _response = new()
    {
        StatusCode = HttpStatusCode.OK,
        Content = new StringContent("hello world"),
    };

    [Fact]
    public void ItCanBeInstantiated()
    {
        // Act - Assert no exception occurs
        _ = new SessionsPythonPlugin(this._defaultSettings, () => Task.FromResult(string.Empty), this._httpClientFactory);
    }

    [Fact]
    public void ItCanBeImported()
    {
        var plugin = new SessionsPythonPlugin(this._defaultSettings, () => Task.FromResult(string.Empty), this._httpClientFactory);

        // Act - Assert no exception occurs e.g. due to reflection
        Assert.NotNull(KernelPluginFactory.CreateFromObject(plugin));
    }

    [Fact]
    public async Task ItShouldExecuteCodeAsync()
    {
        var responseContent = File.ReadAllText(CodeExecutionTestDataFilePath);
        this._messageHandlerStub.ResponseToReturn = new HttpResponseMessage(HttpStatusCode.OK)
        {
            Content = new StringContent(responseContent),
        };
        var expectedResult = """
                       Result:
                       ""
                       Stdout:
                       "Hello World!\n"
                       Stderr:
                       ""
                       """;
        // Arrange
        var plugin = new SessionsPythonPlugin(this._defaultSettings, () => Task.FromResult(string.Empty), this._httpClientFactory);

        // Act
        var result = await plugin.ExecuteCodeAsync("print('hello world')");

        // Assert
        Assert.Equal(expectedResult, result);
    }

    [Fact]
    public async Task ItShouldListFilesAsync()
    {
        var responseContent = File.ReadAllText(ListFilesTestDataFilePath);
        this._messageHandlerStub.ResponseToReturn = new HttpResponseMessage(HttpStatusCode.OK)
        {
            Content = new StringContent(responseContent),
        };

        // Arrange
        var plugin = new SessionsPythonPlugin(this._defaultSettings, () => Task.FromResult(string.Empty), this._httpClientFactory);

        // Act
        var result = await plugin.ListFilesAsync();

        // Assert
        Assert.Contains<SessionRemoteFileMetadata>(result, (item) =>
            item.Filename == "test.txt" &&
            item.Size == 680 &&
            item.LastModifiedTime!.Value.Ticks == 638508470494918207);

        Assert.Contains<SessionRemoteFileMetadata>(result, (item) =>
            item.Filename == "test2.txt" &&
            item.Size == 1074 &&
            item.LastModifiedTime!.Value.Ticks == 638508471084916062);
    }

    [Fact]
    public async Task ItShouldUploadFileAsync()
    {
        // Arrange
        var responseContent = await File.ReadAllTextAsync(UpdaloadFileTestDataFilePath);
        var requestPayload = await File.ReadAllBytesAsync(FileTestDataFilePath);

        var expectedResponse = new SessionRemoteFileMetadata("test.txt", 680)
        {
            LastModifiedTime = new DateTime(638508470494918207),
        };

        this._messageHandlerStub.ResponseToReturn = new HttpResponseMessage(HttpStatusCode.OK)
        {
            Content = new StringContent(responseContent),
        };

        var plugin = new SessionsPythonPlugin(this._defaultSettings, () => Task.FromResult(string.Empty), this._httpClientFactory);

        // Act
        var result = await plugin.UploadFileAsync(".test.txt", FileTestDataFilePath);

        // Assert
        Assert.Equal(result.Filename, expectedResponse.Filename);
        Assert.Equal(result.Size, expectedResponse.Size);
        Assert.Equal(result.LastModifiedTime, expectedResponse.LastModifiedTime);
        Assert.Equal(requestPayload, this._messageHandlerStub.FirstMultipartContent);
    }

    [Fact]
    public async Task ItShouldDownloadFileWithoutSavingInDiskAsync()
    {
        // Arrange
        var responseContent = await File.ReadAllBytesAsync(FileTestDataFilePath);
        this._messageHandlerStub.ResponseToReturn = new HttpResponseMessage(HttpStatusCode.OK)
        {
            Content = new ByteArrayContent(responseContent),
        };

        var plugin = new SessionsPythonPlugin(this._defaultSettings, () => Task.FromResult(string.Empty), this._httpClientFactory);

        // Act
        var result = await plugin.DownloadFileAsync("test.txt");

        // Assert
        Assert.Equal(responseContent, result);
    }

    [Fact]
    public async Task ItShouldDownloadFileSavingInDiskAsync()
    {
        // Arrange
        var responseContent = await File.ReadAllBytesAsync(FileTestDataFilePath);
        var downloadDiskPath = FileTestDataFilePath.Replace(".txt", "_download.txt", StringComparison.InvariantCultureIgnoreCase);
        if (File.Exists(downloadDiskPath))
        {
            File.Delete(downloadDiskPath);
        }

        this._messageHandlerStub.ResponseToReturn = new HttpResponseMessage(HttpStatusCode.OK)
        {
            Content = new ByteArrayContent(responseContent),
        };

        var plugin = new SessionsPythonPlugin(this._defaultSettings, () => Task.FromResult(string.Empty), this._httpClientFactory);

        // Act
        var result = await plugin.DownloadFileAsync("test.txt", downloadDiskPath);

        // Assert
        Assert.Equal(responseContent, result);
        Assert.True(File.Exists(downloadDiskPath));
        Assert.Equal(responseContent, await File.ReadAllBytesAsync(downloadDiskPath));
    }

    public void Dispose()
    {
        this._httpClient.Dispose();
        this._messageHandlerStub.Dispose();
    }
}
