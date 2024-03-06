// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.Extensions.Configuration;
using Xunit;
using Xunit.Abstractions;

namespace SemanticKernel.IntegrationTests.WebPlugin;

public sealed class WebPluginTests : IDisposable
{
    private readonly string _bingApiKey;

    public WebPluginTests(ITestOutputHelper output)
    {
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

    #region internals

    private readonly ITestOutputHelper _output;
    private readonly RedirectOutput _testOutputHelper;

    public void Dispose()
    {
        this._testOutputHelper.Dispose();
    }

    #endregion
}
