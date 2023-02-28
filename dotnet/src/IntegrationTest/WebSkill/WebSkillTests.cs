// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading.Tasks;
using Microsoft.Extensions.Configuration;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.Skills.Web;
using Microsoft.SemanticKernel.Skills.Web.Bing;
using Xunit;
using Xunit.Abstractions;

namespace IntegrationTests.WebSkill;

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

    [Theory]
    [InlineData("What is generally recognized as the tallest building in Seattle, Washington, USA?", "Columbia Center")]
    public async Task BingSkillTestAsync(string prompt, string expectedAnswerContains)
    {
        // Arrange
        IKernel kernel = Kernel.Builder.WithLogger(this._logger).Build();

        using XunitLogger<BingConnector> connectorLogger = new(this._output);
        using BingConnector connector = new(this._bingApiKey, connectorLogger);

        WebSearchEngineSkill skill = new(connector);
        var search = kernel.ImportSkill(skill, "WebSearchEngine");

        // Act
        SKContext result = await kernel.RunAsync(
            prompt,
            search["SearchAsync"]
        );

        // Assert
        Assert.Contains(expectedAnswerContains, result.Result, StringComparison.InvariantCultureIgnoreCase);
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
