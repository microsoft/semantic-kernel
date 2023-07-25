// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.IO;
using System.Threading.Tasks;
using Microsoft.Extensions.Configuration;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.Skills.Web;
using Microsoft.SemanticKernel.Skills.Web.Bing;
using Newtonsoft.Json;
using Xunit;
using Xunit.Abstractions;
using static Microsoft.SemanticKernel.Skills.Web.Bing.BingConnector;

namespace SemanticKernel.IntegrationTests.WebSkill;

public sealed class WebSkillTests : IDisposable
{
    private readonly string _bingApiKey;

    public WebSkillTests(ITestOutputHelper output)
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
            .AddUserSecrets<WebSkillTests>()
            .Build();

        string? bingApiKeyCandidate = configuration["Bing:ApiKey"];
        Assert.NotNull(bingApiKeyCandidate);
        this._bingApiKey = bingApiKeyCandidate;
    }

    [Theory(Skip = "Bing search results not consistent enough for testing.")]
    [InlineData("What is generally recognized as the tallest building in Seattle, Washington, USA?", "Columbia Center")]
    public async Task BingSkillSnippetsTestAsync(string prompt, string expectedAnswerContains)
    {
        // Arrange
        IKernel kernel = Kernel.Builder.WithLogger(this._logger).Build();

        using XunitLogger<BingConnector> connectorLogger = new(this._output);
        BingConnector connector = new(this._bingApiKey, logger: connectorLogger);
        Assert.NotEmpty(this._bingApiKey);

        WebSearchEngineSkill skill = new(connector);

        ContextVariables contextVariables = new(prompt);
        contextVariables.Set(WebSearchEngineSkill.Parameters.CountParam, "1");
        contextVariables.Set(WebSearchEngineSkill.Parameters.OffsetParam, "0");

        var search = kernel.ImportSkill(skill, "WebSearchEngine");

        // Act
        SKContext result = await kernel.RunAsync(
            contextVariables,
            search["Search"]
        );

        // Assert
        Assert.Contains(expectedAnswerContains, result.Result, StringComparison.OrdinalIgnoreCase);
    }

    [Theory(Skip = "Bing search results not consistent enough for testing.")]
    [InlineData("What is generally recognized as the tallest building in Seattle, Washington, USA?", "Columbia Center")]
    public async Task BingSkillFullResultTestAsync(string prompt)
    {
        // Arrange
        IKernel kernel = Kernel.Builder.WithLogger(this._logger).Build();

        using XunitLogger<BingConnector> connectorLogger = new(this._output);
        BingConnector connector = new(this._bingApiKey, logger: connectorLogger);
        Assert.NotEmpty(this._bingApiKey);

        WebSearchEngineSkill skill = new(connector);

        ContextVariables contextVariables = new(prompt);
        contextVariables.Set(WebSearchEngineSkill.Parameters.CountParam, "1");
        contextVariables.Set(WebSearchEngineSkill.Parameters.OffsetParam, "0");

        var search = kernel.ImportSkill(skill, "WebSearchEngine");

        // Act
        var task = await kernel.RunAsync(
            contextVariables,
            search["GetSearchResults"]
        );

        var webPages = JsonConvert.DeserializeObject<List<WebPage>>(task.Result);

        // Assert
        Assert.True(webPages != null && webPages.Count > 0);
    }

    [Fact]
    public async Task WebFileDownloadSkillFileTestAsync()
    {
        // Arrange
        IKernel kernel = Kernel.Builder.WithLogger(this._logger).Build();
        using XunitLogger<WebFileDownloadSkill> skillLogger = new(this._output);
        var skill = new WebFileDownloadSkill(skillLogger);
        var download = kernel.ImportSkill(skill, "WebFileDownload");
        string fileWhereToSaveWebPage = Path.GetTempFileName();
        var contextVariables = new ContextVariables("https://www.microsoft.com");
        contextVariables.Set(WebFileDownloadSkill.FilePathParamName, fileWhereToSaveWebPage);

        // Act
        await kernel.RunAsync(contextVariables, download["DownloadToFile"]);

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

    ~WebSkillTests()
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
