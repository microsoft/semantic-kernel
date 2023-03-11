// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.IO;
using System.Reflection;
using System.Threading.Tasks;
using IntegrationTests.AI;
using IntegrationTests.TestSettings;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.CoreSkills;
using Microsoft.SemanticKernel.KernelExtensions;
using Microsoft.SemanticKernel.Memory;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.SkillDefinition;
using Xunit;
using Xunit.Abstractions;

namespace IntegrationTests.CoreSkills;

public sealed class PlannerSkillTests : IDisposable
{
    private readonly IConfigurationRoot _configuration;

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

        var memoryStorage = new VolatileMemoryStore();
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
            .WithMemoryStorage(memoryStorage)
            .Build();

        var chatSkill = GetSkill("ChatSkill", target);
        var summarizeSkill = GetSkill("SummarizeSkill", target);
        var writerSkill = GetSkill("WriterSkill", target);
        var calendarSkill = GetSkill("CalendarSkill", target);
        var childrensBookSkill = GetSkill("ChildrensBookSkill", target);
        var classificationSkill = GetSkill("ClassificationSkill", target);
        var codingSkill = GetSkill("CodingSkill", target);
        var funSkill = GetSkill("FunSkill", target);
        var intentDetectionSkill = GetSkill("IntentDetectionSkill", target);
        var miscSkill = GetSkill("MiscSkill", target);
        var openApiSkill = GetSkill("OpenApiSkill", target);
        var qaSkill = GetSkill("QASkill", target);
        var emailSkill = target.ImportSkill(new EmailSkill());

        var plannerSKill = target.ImportSkill(new PlannerSkill(target));

        // Act
        ContextVariables variables = new(prompt);
        variables.Set(PlannerSkill.Parameters.ExcludedSkills, "IntentDetectionSkill,FunSkill");
        variables.Set(PlannerSkill.Parameters.ExcludedFunctions, "EmailTo");
        variables.Set(PlannerSkill.Parameters.IncludedFunctions, "Continue");
        variables.Set(PlannerSkill.Parameters.MaxFunctions, "9");
        variables.Set(PlannerSkill.Parameters.RelevancyThreshold, "0.77");
        SKContext actual = await target.RunAsync(variables, plannerSKill["CreatePlan"]).ConfigureAwait(true);

        // Assert
        Assert.Empty(actual.LastErrorDescription);
        Assert.False(actual.ErrorOccurred);
        Assert.Contains(expectedAnswerContains, actual.Result, StringComparison.InvariantCultureIgnoreCase);
    }

    private static IDictionary<string, ISKFunction> GetSkill(string skillName, IKernel target)
    {
        string? currentAssemblyDirectory = Path.GetDirectoryName(Assembly.GetExecutingAssembly().Location);
        if (string.IsNullOrWhiteSpace(currentAssemblyDirectory))
        {
            throw new InvalidOperationException("Unable to determine current assembly directory.");
        }

        string skillParentDirectory = Path.GetFullPath(Path.Combine(currentAssemblyDirectory, "../../../../../../samples/skills"));

        IDictionary<string, ISKFunction> skill = target.ImportSemanticSkillFromDirectory(skillParentDirectory, skillName);
        return skill;
    }

    private readonly XunitLogger<object> _logger;
    private readonly RedirectOutput _testOutputHelper;

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
