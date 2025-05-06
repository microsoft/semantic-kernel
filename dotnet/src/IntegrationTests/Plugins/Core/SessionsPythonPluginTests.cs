// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Net.Http;
using System.Threading;
using System.Threading.Tasks;
using Azure.Core;
using Azure.Identity;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.AzureOpenAI;
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
    private readonly IConfigurationRoot _configurationRoot;

    public SessionsPythonPluginTests()
    {
        this._configurationRoot = new ConfigurationBuilder()
            .AddJsonFile(path: "testsettings.json", optional: true, reloadOnChange: true)
            .AddJsonFile(path: "testsettings.development.json", optional: true, reloadOnChange: true)
            .AddEnvironmentVariables()
            .AddUserSecrets<SessionsPythonPluginTests>()
            .Build();

        var _spConfiguration = this._configurationRoot
            .GetSection("AzureContainerAppSessionPool")
            .Get<AzureContainerAppSessionPoolConfiguration>()!;

        this._settings = new(sessionId: Guid.NewGuid().ToString(), endpoint: new Uri(_spConfiguration.Endpoint))
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
        Assert.Equal("test_file.txt", result.Name);
        Assert.Equal(322, result.SizeInBytes);
        Assert.Equal("file", result.Type);
        Assert.Equal("text/plain; charset=utf-8", result.ContentType);
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
        Assert.Equal("test_file_1.txt", firstFile.Name);
        Assert.Equal(322, firstFile.SizeInBytes);
        Assert.Equal("file", firstFile.Type);
        Assert.Equal("text/plain; charset=utf-8", firstFile.ContentType);

        var secondFile = files[1];
        Assert.Equal("test_file_2.txt", secondFile.Name);
        Assert.Equal(336, secondFile.SizeInBytes);
        Assert.Equal("file", secondFile.Type);
        Assert.Equal("text/plain; charset=utf-8", secondFile.ContentType);
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
        Assert.Contains("Succeeded", result);
    }

    [Fact(Skip = SkipReason)]
    public async Task LlmShouldUploadFileAndAccessItFromCodeInterpreterAsync()
    {
        // Arrange
        Kernel kernel = this.InitializeKernel();
        kernel.Plugins.AddFromObject(this._sut);

        var chatCompletionService = kernel.Services.GetRequiredService<IChatCompletionService>();

        AzureOpenAIPromptExecutionSettings settings = new()
        {
            FunctionChoiceBehavior = FunctionChoiceBehavior.Auto()
        };

        ChatHistory chatHistory = [];
        chatHistory.AddUserMessage(@"Upload the local file TestData\SessionsPythonPlugin\file_to_upload_1.txt and use python code to count number of words in it.");

        // Act
        var result = await chatCompletionService.GetChatMessageContentAsync(chatHistory, settings, kernel);

        // Assert
        Assert.Contains("52", result.ToString());
    }

    /// <summary>
    /// Acquires authentication token for the Azure Container App Session pool.
    /// </summary>
    private static async Task<string> GetAuthTokenAsync(CancellationToken cancellationToken)
    {
        string resource = "https://acasessions.io/.default";

        var credential = new AzureCliCredential();

        AccessToken token = await credential.GetTokenAsync(new Azure.Core.TokenRequestContext([resource]), cancellationToken).ConfigureAwait(false);

        return token.Token;
    }

    private Kernel InitializeKernel()
    {
        var azureOpenAIConfiguration = this._configurationRoot.GetSection("AzureOpenAI").Get<AzureOpenAIConfiguration>();
        Assert.NotNull(azureOpenAIConfiguration);
        Assert.NotNull(azureOpenAIConfiguration.ChatDeploymentName);
        Assert.NotNull(azureOpenAIConfiguration.Endpoint);

        var kernelBuilder = Kernel.CreateBuilder();

        kernelBuilder.AddAzureOpenAIChatCompletion(
            deploymentName: azureOpenAIConfiguration.ChatDeploymentName,
            modelId: azureOpenAIConfiguration.ChatModelId,
            endpoint: azureOpenAIConfiguration.Endpoint,
            credentials: new AzureCliCredential());

        return kernelBuilder.Build();
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
