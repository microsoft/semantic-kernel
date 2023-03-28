// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading.Tasks;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.CoreSkills;
using Microsoft.SemanticKernel.Memory;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.SkillDefinition;
using SemanticKernel.IntegrationTests.AI;
using SemanticKernel.IntegrationTests.TestSettings;
using Xunit;
using Xunit.Abstractions;

namespace SemanticKernel.IntegrationTests.CoreSkills;

public sealed class PlannerSkillTests : IDisposable
{
    public PlannerSkillTests(ITestOutputHelper output)
    {
        this._logger = new XunitLogger<object>(output);
        this._testOutputHelper = new RedirectOutput(output);

        // Load configuration
        this._configuration = new ConfigurationBuilder()
            .AddJsonFile(path: "testsettings.json", optional: false, reloadOnChange: true)
            .AddJsonFile(path: "testsettings.development.json", optional: true, reloadOnChange: true)
            .AddEnvironmentVariables()
            .AddUserSecrets<OpenAICompletionTests>()
            .Build();
    }

    [Theory]
    [InlineData("Write a poem or joke and send it in an e-mail to Kai.", "function._GLOBAL_FUNCTIONS_.SendEmail")]
    public async Task CreatePlanWithEmbeddingsTestAsync(string prompt, string expectedAnswerContains)
    {
        // Arrange
        AzureOpenAIConfiguration? azureOpenAIConfiguration = this._configuration.GetSection("AzureOpenAI").Get<AzureOpenAIConfiguration>();
        Assert.NotNull(azureOpenAIConfiguration);

        AzureOpenAIConfiguration? azureOpenAIEmbeddingsConfiguration = this._configuration.GetSection("AzureOpenAIEmbeddings").Get<AzureOpenAIConfiguration>();
        Assert.NotNull(azureOpenAIEmbeddingsConfiguration);

        IKernel target = Kernel.Builder
            .WithLogger(this._logger)
            .Configure(config =>
            {
                config.AddAzureOpenAICompletionBackend(
                    label: azureOpenAIConfiguration.Label,
                    deploymentName: azureOpenAIConfiguration.DeploymentName,
                    endpoint: azureOpenAIConfiguration.Endpoint,
                    apiKey: azureOpenAIConfiguration.ApiKey);

                config.AddAzureOpenAIEmbeddingsBackend(
                    label: azureOpenAIEmbeddingsConfiguration.Label,
                    deploymentName: azureOpenAIEmbeddingsConfiguration.DeploymentName,
                    endpoint: azureOpenAIEmbeddingsConfiguration.Endpoint,
                    apiKey: azureOpenAIEmbeddingsConfiguration.ApiKey);

                config.SetDefaultCompletionBackend(azureOpenAIConfiguration.Label);
            })
            .WithMemoryStorage(new VolatileMemoryStore())
            .Build();

        // Import all sample skills available for demonstration purposes.
        TestHelpers.ImportSampleSkills(target);

        var emailSkill = target.ImportSkill(new EmailSkill());

        var plannerSKill = target.ImportSkill(new PlannerSkill(target));

        // Act
        ContextVariables variables = new(prompt);
        variables.Set(PlannerSkill.Parameters.ExcludedSkills, "IntentDetectionSkill,FunSkill");
        variables.Set(PlannerSkill.Parameters.ExcludedFunctions, "EmailTo");
        variables.Set(PlannerSkill.Parameters.IncludedFunctions, "Continue");
        variables.Set(PlannerSkill.Parameters.MaxRelevantFunctions, "9");
        variables.Set(PlannerSkill.Parameters.RelevancyThreshold, "0.77");
        SKContext actual = await target.RunAsync(variables, plannerSKill["CreatePlan"]).ConfigureAwait(true);

        // Assert
        Assert.Empty(actual.LastErrorDescription);
        Assert.False(actual.ErrorOccurred);
        Assert.Contains(expectedAnswerContains, actual.Result, StringComparison.InvariantCultureIgnoreCase);
    }

    private readonly XunitLogger<object> _logger;
    private readonly RedirectOutput _testOutputHelper;
    private readonly IConfigurationRoot _configuration;

    public void Dispose()
    {
        this.Dispose(true);
        GC.SuppressFinalize(this);
    }

    ~PlannerSkillTests()
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

    internal class EmailSkill
    {
        [SKFunction("Given an e-mail and message body, send an email")]
        [SKFunctionInput(Description = "The body of the email message to send.")]
        [SKFunctionContextParameter(Name = "email_address", Description = "The email address to send email to.")]
        public Task<SKContext> SendEmailAsync(string input, SKContext context)
        {
            context.Variables.Update($"Sent email to: {context.Variables["email_address"]}. Body: {input}");
            return Task.FromResult(context);
        }

        [SKFunction("Given a name, find email address")]
        [SKFunctionInput(Description = "The name of the person to email.")]
        public Task<SKContext> GetEmailAddressAsync(string input, SKContext context)
        {
            context.Log.LogDebug("Returning hard coded email for {0}", input);
            context.Variables.Update("johndoe1234@example.com");
            return Task.FromResult(context);
        }

        [SKFunction("Write a short poem for an e-mail")]
        [SKFunctionInput(Description = "The topic of the poem.")]
        public Task<SKContext> WritePoemAsync(string input, SKContext context)
        {
            context.Variables.Update($"Roses are red, violets are blue, {input} is hard, so is this test.");
            return Task.FromResult(context);
        }
    }
}
