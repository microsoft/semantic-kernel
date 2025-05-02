// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Net.Http;
using System.Threading.Tasks;
using Azure.Core;
using Azure.Identity;
using Microsoft.Extensions.Configuration;
using Microsoft.SemanticKernel.Plugins.Core.CodeInterpreter;
using SemanticKernel.IntegrationTests.TestSettings;
using Xunit;

namespace SemanticKernel.IntegrationTests.Plugins.Core;

public sealed class SessionsPythonPluginTests : IDisposable
{
    private const string SkipReason = "For manual verification only";

    private readonly SessionsPythonSettings _settings;
    private readonly HttpClientFactory _httpClientFactory;
    private readonly SessionsPythonPlugin _sut;

    public SessionsPythonPluginTests()
    {
        var configurationRoot = new ConfigurationBuilder()
            .AddJsonFile(path: "testsettings.json", optional: true, reloadOnChange: true)
            .AddJsonFile(path: "testsettings.development.json", optional: true, reloadOnChange: true)
            .AddEnvironmentVariables()
            .AddUserSecrets<SessionsPythonPluginTests>()
            .Build();

        var _configuration = configurationRoot
            .GetSection("AzureContainerAppSessionPool")
            .Get<AzureContainerAppSessionPoolConfiguration>()!;

        this._settings = new(sessionId: Guid.NewGuid().ToString(), endpoint: new Uri(_configuration.Endpoint))
        {
            CodeExecutionType = SessionsPythonSettings.CodeExecutionTypeSetting.Synchronous,
            CodeInputType = SessionsPythonSettings.CodeInputTypeSetting.Inline
        };

        this._httpClientFactory = new HttpClientFactory();

        this._sut = new SessionsPythonPlugin(this._settings, this._httpClientFactory, GetAuthTokenAsync);
    }

    [Fact(Skip = SkipReason)]
    public async Task ItShouldUploadFileAsync()
    {
        // Act
        var result = await this._sut.UploadFileAsync("test_file.txt", @"TestData\SessionsPythonPlugin\file_to_upload_1.txt");

        // Assert
        Assert.Equal("test_file.txt", result.Filename);
        Assert.Equal(322, result.Size);
        Assert.NotNull(result.LastModifiedTime);
        Assert.Equal("/mnt/data/test_file.txt", result.FullPath);
    }

    [Fact(Skip = SkipReason)]
    public async Task ItShouldDownloadFileAsync()
    {
        // Arrange
        await this._sut.UploadFileAsync("test_file.txt", @"TestData\SessionsPythonPlugin\file_to_upload_1.txt");

        // Act
        var fileContent = await this._sut.DownloadFileAsync("test_file.txt");

        // Assert
        Assert.Equal(322, fileContent.Length);
    }

    [Fact(Skip = SkipReason)]
    public async Task ItShouldListFilesAsync()
    {
        // Arrange
        await this._sut.UploadFileAsync("test_file_1.txt", @"TestData\SessionsPythonPlugin\file_to_upload_1.txt");
        await this._sut.UploadFileAsync("test_file_2.txt", @"TestData\SessionsPythonPlugin\file_to_upload_2.txt");

        // Act
        var files = await this._sut.ListFilesAsync();

        // Assert
        Assert.Equal(2, files.Count);

        var firstFile = files[0];
        Assert.Equal("test_file_1.txt", firstFile.Filename);
        Assert.Equal(322, firstFile.Size);
        Assert.NotNull(firstFile.LastModifiedTime);
        Assert.Equal("/mnt/data/test_file_1.txt", firstFile.FullPath);

        var secondFile = files[1];
        Assert.Equal("test_file_2.txt", secondFile.Filename);
        Assert.Equal(336, secondFile.Size);
        Assert.NotNull(secondFile.LastModifiedTime);
        Assert.Equal("/mnt/data/test_file_2.txt", secondFile.FullPath);
    }

    [Fact(Skip = SkipReason)]
    public async Task ItShouldExecutePythonCodeAsync()
    {
        // Arrange
        string code = "result = 5 + 3\nprint(result)";

        // Act
        var result = await this._sut.ExecuteCodeAsync(code);

        // Assert
        Assert.Contains("8", result);
        Assert.Contains("Success", result);
    }

    /// <summary>
    /// Acquires authentication token for the Azure Container App Session pool.
    /// </summary>
    private static async Task<string> GetAuthTokenAsync()
    {
        string resource = "https://acasessions.io/.default";

        var credential = new AzureCliCredential();

        AccessToken token = await credential.GetTokenAsync(new Azure.Core.TokenRequestContext([resource])).ConfigureAwait(false);

        return token.Token;
    }

    public void Dispose()
    {
        this._httpClientFactory.Dispose();
    }

    private sealed class HttpClientFactory : IHttpClientFactory, IDisposable
    {
        private readonly List<HttpClient> _httpClients = [];

        public HttpClient CreateClient(string name)
        {
            var client = new HttpClient();
            this._httpClients.Add(client);
            return client;
        }

        public void Dispose()
        {
            this._httpClients.ForEach(client => client.Dispose());
        }
    }
}
