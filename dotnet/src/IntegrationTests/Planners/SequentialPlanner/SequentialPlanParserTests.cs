﻿// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.Configuration;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Planning;
using SemanticKernel.IntegrationTests.Fakes;
using SemanticKernel.IntegrationTests.TestSettings;
using Xunit;
using Xunit.Abstractions;

namespace SemanticKernel.IntegrationTests.Planners.Sequential;

public class SequentialPlanParserTests
{
    public SequentialPlanParserTests(ITestOutputHelper output)
    {
        // Load configuration
        this._configuration = new ConfigurationBuilder()
            .AddJsonFile(path: "testsettings.json", optional: false, reloadOnChange: true)
            .AddJsonFile(path: "testsettings.development.json", optional: true, reloadOnChange: true)
            .AddEnvironmentVariables()
            .AddUserSecrets<SequentialPlanParserTests>()
            .Build();
    }

    [Fact]
    public void CanCallToPlanFromXml()
    {
        // Arrange
        AzureOpenAIConfiguration? azureOpenAIConfiguration = this._configuration.GetSection("AzureOpenAI").Get<AzureOpenAIConfiguration>();
        Assert.NotNull(azureOpenAIConfiguration);

        Kernel kernel = Kernel.CreateBuilder()
            .WithAzureOpenAITextGeneration(
                deploymentName: azureOpenAIConfiguration.DeploymentName,
                endpoint: azureOpenAIConfiguration.Endpoint,
                credentials: new AzureCliCredential(),
                serviceId: azureOpenAIConfiguration.ServiceId)
            .Build();
        kernel.ImportPluginFromType<EmailPluginFake>("email");
        TestHelpers.ImportSamplePlugins(kernel, "SummarizePlugin", "WriterPlugin");

        var planString =
            @"<plan>
    <function.SummarizePlugin.Summarize/>
    <function.WriterPlugin.Translate language=""French"" setContextVariable=""TRANSLATED_SUMMARY""/>
    <function.email.GetEmailAddress input=""John Doe"" setContextVariable=""EMAIL_ADDRESS""/>
    <function.email.SendEmail input=""$TRANSLATED_SUMMARY"" email_address=""$EMAIL_ADDRESS""/>
</plan>";
        var goal = "Summarize an input, translate to french, and e-mail to John Doe";

        // Act
        var plan = planString.ToPlanFromXml(goal, kernel.Plugins.GetFunctionCallback());

        // Assert
        Assert.NotNull(plan);
        Assert.Equal((string?)"Summarize an input, translate to french, and e-mail to John Doe", (string?)plan.Description);

        Assert.Equal(4, plan.Steps.Count);
        Assert.Collection<Plan>(plan.Steps,
            step =>
            {
                Assert.Equal("SummarizePlugin", step.PluginName);
                Assert.Equal("Summarize", step.Name);
            },
            step =>
            {
                Assert.Equal("WriterPlugin", step.PluginName);
                Assert.Equal("Translate", step.Name);
                Assert.Equal("French", step.Parameters["language"]);
                Assert.True(step.Outputs.Contains("TRANSLATED_SUMMARY"));
            },
            step =>
            {
                Assert.Equal("email", step.PluginName);
                Assert.Equal("GetEmailAddress", step.Name);
                Assert.Equal("John Doe", step.Parameters["input"]);
                Assert.True(step.Outputs.Contains("EMAIL_ADDRESS"));
            },
            step =>
            {
                Assert.Equal("email", step.PluginName);
                Assert.Equal("SendEmail", step.Name);
                Assert.Equal("$TRANSLATED_SUMMARY", step.Parameters["input"]);
                Assert.Equal("$EMAIL_ADDRESS", step.Parameters["email_address"]);
            }
        );
    }

    private readonly IConfigurationRoot _configuration;
}
