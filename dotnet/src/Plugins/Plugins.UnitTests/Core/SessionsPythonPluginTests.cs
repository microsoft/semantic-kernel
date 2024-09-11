// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.IO;
using System.Net;
using System.Net.Http;
using System.Text;
using System.Text.Json;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Plugins.Core.CodeInterpreter;
using Moq;
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

    private readonly SessionsPythonSettings _defaultSettings = new(
        sessionId: Guid.NewGuid().ToString(),
        endpoint: new Uri("http://localhost:8888"))
    {
        CodeExecutionType = SessionsPythonSettings.CodeExecutionTypeSetting.Synchronous,
        CodeInputType = SessionsPythonSettings.CodeInputTypeSetting.Inline
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

    [Fact]
    public void ItCanBeInstantiated()
    {
        // Act - Assert no exception occurs
        _ = new SessionsPythonPlugin(this._defaultSettings, this._httpClientFactory);
    }

    [Fact]
    public void ItCanBeImported()
    {
        var plugin = new SessionsPythonPlugin(this._defaultSettings, this._httpClientFactory);

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
        var plugin = new SessionsPythonPlugin(this._defaultSettings, this._httpClientFactory);

        // Act
        var result = await plugin.ExecuteCodeAsync("print('hello world')");

        // Assert
        Assert.Equal(expectedResult, result);
    }

    [Theory]
    [InlineData(nameof(SessionsPythonPlugin.DownloadFileAsync))]
    [InlineData(nameof(SessionsPythonPlugin.ListFilesAsync))]
    [InlineData(nameof(SessionsPythonPlugin.UploadFileAsync))]
    public async Task ItShouldCallTokenProviderWhenProvidedAsync(string methodName)
    {
        // Arrange
        var tokenProviderCalled = false;

        Task<string> tokenProviderAsync()
        {
            tokenProviderCalled = true;
            return Task.FromResult("token");
        }

        this._messageHandlerStub.ResponseToReturn = new HttpResponseMessage(HttpStatusCode.OK)
        {
            Content = new StringContent(""),
        };

        var plugin = new SessionsPythonPlugin(this._defaultSettings, this._httpClientFactory, tokenProviderAsync);

        // Act
        try
        {
            switch (methodName)
            {
                case nameof(SessionsPythonPlugin.DownloadFileAsync):
                    await plugin.DownloadFileAsync("test.txt");
                    break;
                case nameof(SessionsPythonPlugin.ListFilesAsync):
                    await plugin.ListFilesAsync();
                    break;
                case nameof(SessionsPythonPlugin.UploadFileAsync):
                    await plugin.UploadFileAsync(".test.txt", FileTestDataFilePath);
                    break;
            }
        }
        catch (JsonException)
        {
            // Ignore response serialization exceptions
        }

        // Assert
        Assert.True(tokenProviderCalled);
    }

    [Fact]
    public async Task ItShouldUseSameSessionIdAcrossMultipleCallsAsync()
    {
        // Arrange

        using var multiMessageHandlerStub = new MultipleHttpMessageHandlerStub();
        multiMessageHandlerStub.AddJsonResponse(File.ReadAllText(CodeExecutionTestDataFilePath));
        multiMessageHandlerStub.AddJsonResponse(File.ReadAllText(ListFilesTestDataFilePath));
        multiMessageHandlerStub.AddJsonResponse(File.ReadAllText(UpdaloadFileTestDataFilePath));
        multiMessageHandlerStub.ResponsesToReturn.Add(new HttpResponseMessage(HttpStatusCode.OK));

        List<HttpClient> httpClients = [];
        var httpClientFactoryMock = new Mock<IHttpClientFactory>();
        httpClientFactoryMock.Setup(f => f.CreateClient(It.IsAny<string>())).Returns(() =>
        {
            var targetClient = new HttpClient(multiMessageHandlerStub, false);
            httpClients.Add(targetClient);

            return targetClient;
        });

        var expectedSessionId = Guid.NewGuid().ToString();
        this._defaultSettings.SessionId = expectedSessionId;

        var plugin = new SessionsPythonPlugin(this._defaultSettings, httpClientFactoryMock.Object);

        // Act
        await plugin.ExecuteCodeAsync("print('hello world')");
        await plugin.ListFilesAsync();
        await plugin.UploadFileAsync(".test.txt", FileTestDataFilePath);

        // Assert
        Assert.Contains(expectedSessionId, Encoding.UTF8.GetString(multiMessageHandlerStub.RequestContents[0]!), StringComparison.OrdinalIgnoreCase);
        Assert.Contains(expectedSessionId, multiMessageHandlerStub.RequestUris[1]!.Query, StringComparison.OrdinalIgnoreCase);
        Assert.Contains(expectedSessionId, multiMessageHandlerStub.RequestUris[2]!.Query, StringComparison.OrdinalIgnoreCase);

        foreach (var httpClient in httpClients)
        {
            httpClient.Dispose();
        }
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
        var plugin = new SessionsPythonPlugin(this._defaultSettings, this._httpClientFactory);

        // Act
        var result = await plugin.ListFilesAsync();

        // Assert
        Assert.Contains<SessionsRemoteFileMetadata>(result, (item) =>
            item.Filename == "test-file.txt" &&
            item.Size == 516 &&
            item.LastModifiedTime!.Value.Ticks == 638585580822423944);

        Assert.Contains<SessionsRemoteFileMetadata>(result, (item) =>
            item.Filename == "test-file2.txt" &&
            item.Size == 211 &&
            item.LastModifiedTime!.Value.Ticks == 638585580822423944);
    }

    [Fact]
    public async Task ItShouldUploadFileAsync()
    {
        // Arrange
        var responseContent = await File.ReadAllTextAsync(UpdaloadFileTestDataFilePath);
        var requestPayload = await File.ReadAllBytesAsync(FileTestDataFilePath);

        var expectedResponse = new SessionsRemoteFileMetadata("test-file.txt", 516)
        {
            LastModifiedTime = new DateTime(638585526384228269)
        };

        this._messageHandlerStub.ResponseToReturn = new HttpResponseMessage(HttpStatusCode.OK)
        {
            Content = new StringContent(responseContent),
        };

        var plugin = new SessionsPythonPlugin(this._defaultSettings, this._httpClientFactory);

        // Act
        var result = await plugin.UploadFileAsync("test-file.txt", FileTestDataFilePath);

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

        var plugin = new SessionsPythonPlugin(this._defaultSettings, this._httpClientFactory);

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

        var plugin = new SessionsPythonPlugin(this._defaultSettings, this._httpClientFactory);

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
