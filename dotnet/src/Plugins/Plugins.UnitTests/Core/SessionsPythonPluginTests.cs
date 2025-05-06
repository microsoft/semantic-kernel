// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Net;
using System.Net.Http;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Http;
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
    private readonly static string s_assemblyVersion = typeof(Kernel).Assembly.GetName().Version!.ToString();

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
                       Status:
                       "Succeeded"
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

        Task<string> tokenProviderAsync(CancellationToken _)
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
        Assert.Contains(expectedSessionId, multiMessageHandlerStub.RequestUris[0]!.Query, StringComparison.OrdinalIgnoreCase);
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
        var files = await plugin.ListFilesAsync();

        // Assert
        Assert.Equal(2, files.Count);

        var firstFile = files[0];
        Assert.Equal("test-file.txt", firstFile.Name);
        Assert.Equal(516, firstFile.SizeInBytes);
        Assert.Equal("file", firstFile.Type);
        Assert.Equal("text/plain; charset=utf-8", firstFile.ContentType);
        Assert.Equal(638585580822423944, firstFile.LastModifiedAt.Ticks);

        var secondFile = files[1];
        Assert.Equal("test-file2.txt", secondFile.Name);
        Assert.Equal(211, secondFile.SizeInBytes);
        Assert.Equal("file", secondFile.Type);
        Assert.Equal("text/plain; charset=utf-8", secondFile.ContentType);
        Assert.Equal(638585580822423944, secondFile.LastModifiedAt.Ticks);
    }

    [Fact]
    public async Task ItShouldUploadFileAsync()
    {
        // Arrange
        var responseContent = await File.ReadAllTextAsync(UpdaloadFileTestDataFilePath);
        var requestPayload = await File.ReadAllBytesAsync(FileTestDataFilePath);

        var expectedResponse = new SessionsRemoteFileMetadata()
        {
            Name = "test-file.txt",
            SizeInBytes = 516,
            Type = "file",
            LastModifiedAt = new DateTime(638585526384228269),
            ContentType = "text/plain; charset=utf-8",
        };

        this._messageHandlerStub.ResponseToReturn = new HttpResponseMessage(HttpStatusCode.OK)
        {
            Content = new StringContent(responseContent),
        };

        var plugin = new SessionsPythonPlugin(this._defaultSettings, this._httpClientFactory);

        // Act
        var result = await plugin.UploadFileAsync("test-file.txt", FileTestDataFilePath);

        // Assert
        Assert.Equal(expectedResponse.Name, result.Name);
        Assert.Equal(expectedResponse.SizeInBytes, result.SizeInBytes);
        Assert.Equal(expectedResponse.LastModifiedAt, result.LastModifiedAt);
        Assert.Equal(expectedResponse.Type, result.Type);
        Assert.Equal(expectedResponse.ContentType, result.ContentType);
        Assert.Equal(this._messageHandlerStub.FirstMultipartContent, requestPayload);
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

    /// <summary>
    /// Test the allowed domains for the endpoint.
    /// </summary>
    /// <remarks>
    /// Considering that the functionality which verifies endpoints against the allowed domains is located in one private method,
    /// and the method is reused for all operations of the plugin, we test it only for one operation (ListFilesAsync).
    /// </remarks>
    [Theory]
    [InlineData("fake-test-host.io", "https://fake-test-host.io/subscriptions/123/rg/456/sps/test-pool", true)]
    [InlineData("prod.fake-test-host.io", "https://prod.fake-test-host.io/subscriptions/123/rg/456/sps/test-pool", true)]
    [InlineData("www.fake-test-host.io", "https://www.fake-test-host.io/subscriptions/123/rg/456/sps/test-pool", true)]
    [InlineData("www.prod.fake-test-host.io", "https://www.prod.fake-test-host.io/subscriptions/123/rg/456/sps/test-pool", true)]
    [InlineData("fake-test-host.io", "https://fake-test-host-1.io/subscriptions/123/rg/456/sps/test-pool", false)]
    [InlineData("fake-test-host.io", "https://www.fake-test-host.io/subscriptions/123/rg/456/sps/test-pool", false)]
    [InlineData("www.fake-test-host.io", "https://fake-test-host.io/subscriptions/123/rg/456/sps/test-pool", false)]
    public async Task ItShouldRespectAllowedDomainsAsync(string allowedDomain, string actualEndpoint, bool isAllowed)
    {
        // Arrange
        this._defaultSettings.AllowedDomains = [allowedDomain];
        this._defaultSettings.Endpoint = new Uri(actualEndpoint);

        this._messageHandlerStub.ResponseToReturn = new HttpResponseMessage(HttpStatusCode.OK)
        {
            Content = new StringContent(File.ReadAllText(ListFilesTestDataFilePath)),
        };

        var sut = new SessionsPythonPlugin(this._defaultSettings, this._httpClientFactory);

        // Act
#pragma warning disable CA1031 // Do not catch general exception types
        try
        {
            await sut.ListFilesAsync();
        }
        catch when (!isAllowed)
        {
            // Ignore exception if the endpoint is not allowed since we expect it
        }
#pragma warning restore CA1031 // Do not catch general exception types
    }

    [Fact]
    public async Task ItShouldAddHeadersAsync()
    {
        // Arrange
        var responseContent = await File.ReadAllTextAsync(UpdaloadFileTestDataFilePath);

        this._messageHandlerStub.ResponseToReturn = new HttpResponseMessage(HttpStatusCode.OK)
        {
            Content = new StringContent(responseContent),
        };

        var plugin = new SessionsPythonPlugin(this._defaultSettings, this._httpClientFactory, (_) => Task.FromResult("test-auth-token"));

        // Act
        var result = await plugin.UploadFileAsync("test-file.txt", FileTestDataFilePath);

        // Assert
        Assert.NotNull(this._messageHandlerStub.RequestHeaders);

        var userAgentHeaderValues = this._messageHandlerStub.RequestHeaders.GetValues("User-Agent").ToArray();
        Assert.Equal(2, userAgentHeaderValues.Length);
        Assert.Equal($"{HttpHeaderConstant.Values.UserAgent}/{s_assemblyVersion}", userAgentHeaderValues[0]);
        Assert.Equal("(Language=dotnet)", userAgentHeaderValues[1]);

        var authorizationHeaderValues = this._messageHandlerStub.RequestHeaders.GetValues("Authorization");
        Assert.Single(authorizationHeaderValues, value => value == "Bearer test-auth-token");
    }

    public void Dispose()
    {
        this._httpClient.Dispose();
        this._messageHandlerStub.Dispose();
    }
}
