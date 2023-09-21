// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Memory;
using Microsoft.SemanticKernel.Planning.Flow;
using Microsoft.SemanticKernel.Plugins.Core;
using Microsoft.SemanticKernel.Plugins.Web;
using Microsoft.SemanticKernel.Plugins.Web.Bing;
using SemanticKernel.IntegrationTests.TestSettings;
using Xunit;
using Xunit.Abstractions;

namespace SemanticKernel.IntegrationTests.Planning.FlowPlanner;

public sealed class FlowPlannerTests : IDisposable
{
    private readonly string _bingApiKey;

    public FlowPlannerTests(ITestOutputHelper output)
    {
        this._logger = NullLoggerFactory.Instance;
        this._testOutputHelper = new RedirectOutput(output);

        // Load configuration
        this._configuration = new ConfigurationBuilder()
            .AddJsonFile(path: "testsettings.json", optional: false, reloadOnChange: true)
            .AddJsonFile(path: "testsettings.development.json", optional: true, reloadOnChange: true)
            .AddEnvironmentVariables()
            .AddUserSecrets<FlowPlannerTests>()
            .Build();

        string? bingApiKeyCandidate = this._configuration["Bing:ApiKey"];
        Assert.NotNull(bingApiKeyCandidate);
        this._bingApiKey = bingApiKeyCandidate;
    }

    [Fact]
    public async void CanExecuteFlowAsync()
    {
        // Arrange
        KernelBuilder builder = this.InitializeKernelBuilder();
        var bingConnector = new BingConnector(this._bingApiKey);
        var webSearchEngineSkill = new WebSearchEnginePlugin(bingConnector);
        var sessionId = Guid.NewGuid().ToString();
        string email = "abc@xyz.com";

        Dictionary<object, string?> skills = new()
        {
            { webSearchEngineSkill, "WebSearch" },
            { new TimePlugin(), "time" }
        };

        Flow flow = FlowSerializer.DeserializeFromYaml(@"
goal: answer question and sent email
steps:
  - goal: Who is the current president of the United States? What is his current age divided by 2
    skills:
      - WebSearchEngineSkill
      - TimeSkill
    provides:
      - answer
  - goal: Collect email address
    skills:
      - CollectEmailSkill
    provides:
      - email_address
  - goal: Send email
    skills:
      - SendEmail
    requires:
      - email_address
      - answer
    provides:
      - email
");

        var planner = new Microsoft.SemanticKernel.Planning.FlowPlanner(builder, new FlowStatusProvider(new VolatileMemoryStore()), skills);

        // Act
        var result = await planner.ExecuteFlowAsync(flow, sessionId, "Who is the current president of the United States? What is his current age divided by 2");

        // Assert
        // Loose assertion -- make sure that the plan was executed and pause when it needs interact with user to get more input
        Assert.Contains("email", result.Result, StringComparison.InvariantCultureIgnoreCase);

        // Act
        result = await planner.ExecuteFlowAsync(flow, sessionId, $"my email is {email}");

        // Assert
        var emailPayload = result.Variables["email"];
        Assert.Contains(email, emailPayload, StringComparison.InvariantCultureIgnoreCase);
        Assert.Contains("biden", emailPayload, StringComparison.InvariantCultureIgnoreCase);
    }

    private KernelBuilder InitializeKernelBuilder()
    {
        AzureOpenAIConfiguration? azureOpenAIConfiguration = this._configuration.GetSection("AzureOpenAI").Get<AzureOpenAIConfiguration>();
        Assert.NotNull(azureOpenAIConfiguration);

        var builder = Kernel.Builder.WithLoggerFactory(this._logger);

        builder.WithAzureChatCompletionService(
            deploymentName: azureOpenAIConfiguration.ChatDeploymentName!,
            endpoint: azureOpenAIConfiguration.Endpoint,
            apiKey: azureOpenAIConfiguration.ApiKey,
            alsoAsTextCompletion: true);

        return builder;
    }

    private readonly ILoggerFactory _logger;
    private readonly RedirectOutput _testOutputHelper;
    private readonly IConfigurationRoot _configuration;

    public void Dispose()
    {
        this.Dispose(true);
        GC.SuppressFinalize(this);
    }

    ~FlowPlannerTests()
    {
        this.Dispose(false);
    }

    private void Dispose(bool disposing)
    {
        if (disposing)
        {
            if (this._logger is IDisposable ld)
            {
                ld.Dispose();
            }

            this._testOutputHelper.Dispose();
        }
    }
}
