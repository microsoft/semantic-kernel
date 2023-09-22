// Copyright (c) Microsoft. All rights reserved.

using System;
using System.IO;
using System.Threading.Tasks;
using Microsoft.Extensions.Configuration;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.Plugins.Web;
using Microsoft.SemanticKernel.Plugins.Web.Bing;
using Xunit;
using Xunit.Abstractions;

namespace SemanticKernel.IntegrationTests.WebPlugin;

public sealed class WebPluginTests : IDisposable
{
    private readonly string _bingApiKey;

    public WebPluginTests(ITestOutputHelper output)
    {
        this._logger = new XunitLogger<Kernel>(output);
        this._output = output;

        this._testOutputHelper = new RedirectOutput(output);
        Console.SetOut(this._testOutputHelper);

        // Load configuration
        IConfigurationRoot configuration = new ConfigurationBuilder()
            .AddJsonFile(path: "testsettings.json", optional: false, reloadOnChange: true)
            .AddJsonFile(path: "testsettings.development.json", optional: true, reloadOnChange: true)
            .AddEnvironmentVariables()
            .AddUserSecrets<WebPluginTests>()
            .Build();

        string? bingApiKeyCandidate = configuration["Bing:ApiKey"];
        Assert.NotNull(bingApiKeyCandidate);
        this._bingApiKey = bingApiKeyCandidate;
    }

    [Theory(Skip = "Bing search results not consistent enough for testing.")]
    [InlineData("What is generally recognized as the tallest building in Seattle, Washington, USA?", "Columbia Center")]
    public async Task BingPluginTestAsync(string prompt, string expectedAnswerContains)
    {
        // Arrange
        IKernel kernel = Kernel.Builder.WithLoggerFactory(this._logger).Build();

        using XunitLogger<BingConnector> connectorLogger = new(this._output);
        BingConnector connector = new(this._bingApiKey, connectorLogger);
        Assert.NotEmpty(this._bingApiKey);

        WebSearchEnginePlugin plugin = new(connector);
        var searchFunctions = kernel.ImportFunctions(plugin, "WebSearchEngine");

        // Act
        SKContext result = await kernel.RunAsync(
            prompt,
            searchFunctions["Search"]
        );

        // Assert
        Assert.Contains(expectedAnswerContains, result.Result, StringComparison.OrdinalIgnoreCase);
    }

    [Fact]
    public async Task WebFileDownloadPluginFileTestAsync()
    {
        // Arrange
        IKernel kernel = Kernel.Builder.WithLoggerFactory(this._logger).Build();
        using XunitLogger<WebFileDownloadPlugin> pluginLogger = new(this._output);
        var plugin = new WebFileDownloadPlugin(pluginLogger);
        var downloadFunctions = kernel.ImportFunctions(plugin, "WebFileDownload");
        string fileWhereToSaveWebPage = Path.GetTempFileName();
        var contextVariables = new ContextVariables("https://www.microsoft.com");
        contextVariables.Set(WebFileDownloadPlugin.FilePathParamName, fileWhereToSaveWebPage);

        // Act
        await kernel.RunAsync(contextVariables, downloadFunctions["DownloadToFile"]);

        // Assert
        var fileInfo = new FileInfo(fileWhereToSaveWebPage);
        Assert.True(fileInfo.Length > 0);

        File.Delete(fileWhereToSaveWebPage);
    }

    #region internals

    private readonly ITestOutputHelper _output;
    private readonly XunitLogger<Kernel> _logger;
    private readonly RedirectOutput _testOutputHelper;

    public void Dispose()
    {
        this.Dispose(true);
        GC.SuppressFinalize(this);
    }

    ~WebPluginTests()
    {
        this.Dispose(false);
    }

    private void Dispose(bool disposing)
    {
        if (disposing)
        {
            this._logger.Dispose();
            this._testOutputHelper.Dispose();
        }
    }

    #endregion
}
