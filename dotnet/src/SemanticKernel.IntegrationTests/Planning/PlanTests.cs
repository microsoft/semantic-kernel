// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading.Tasks;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Memory;
using Microsoft.SemanticKernel.Orchestration;
using SemanticKernel.IntegrationTests.Fakes;
using SemanticKernel.IntegrationTests.TestSettings;
using Xunit;
using Xunit.Abstractions;

namespace SemanticKernel.IntegrationTests.Planning;

public sealed class PlanTests : IDisposable
{
    public PlanTests(ITestOutputHelper output)
    {
        this._logger = NullLogger.Instance; //new XunitLogger<object>(output);
        this._testOutputHelper = new RedirectOutput(output);

        // Load configuration
        this._configuration = new ConfigurationBuilder()
            .AddJsonFile(path: "testsettings.json", optional: false, reloadOnChange: true)
            .AddJsonFile(path: "testsettings.development.json", optional: true, reloadOnChange: true)
            .AddEnvironmentVariables()
            .AddUserSecrets<PlanTests>()
            .Build();
    }

    [Theory]
    [InlineData("Write a poem or joke and send it in an e-mail to Kai.")]
    public void CreatePlan(string prompt)
    {
        // Arrange

        // Act
        var plan = new Plan(prompt);

        // Assert
        Assert.Equal(prompt, plan.Description);
        Assert.Equal(prompt, plan.Name);
        Assert.Equal("Microsoft.SemanticKernel.Orchestration.Plan", plan.SkillName);
        Assert.Empty(plan.Steps);
    }

    [Theory]
    [InlineData("This is a story about a dog.", "kai@email.com")]
    public async Task CanExecuteRunSimpleAsync(string inputToEmail, string expectedEmail)
    {
        // Arrange
        IKernel target = this.InitializeKernel();
        var emailSkill = target.ImportSkill(new EmailSkillFake());
        var expectedBody = $"Sent email to: {expectedEmail}. Body: {inputToEmail}".Trim();

        var plan = new Plan(emailSkill["SendEmailAsync"]);

        // Act
        var cv = new ContextVariables();
        cv.Update(inputToEmail);
        cv.Set("email_address", expectedEmail);
        var result = await target.RunAsync(cv, plan);

        // Assert
        Assert.Equal(expectedBody, result.Result);
    }

    [Theory]
    [InlineData("Send a story to kai.", "This is a story about a dog.", "French", "kai@email.com")]
    public async Task CanExecuteRunSimpleStepsAsync(string goal, string inputToTranslate, string language, string expectedEmail)
    {
        // Arrange
        IKernel target = this.InitializeKernel();
        var emailSkill = target.ImportSkill(new EmailSkillFake());
        var writerSkill = TestHelpers.GetSkill("WriterSkill", target);
        var expectedBody = $"Sent email to: {expectedEmail}. Body:".Trim();

        var plan = new Plan(goal);
        plan.AddSteps(writerSkill["Translate"], emailSkill["SendEmailAsync"]);

        // Act
        var cv = new ContextVariables();
        cv.Update(inputToTranslate);
        cv.Set("email_address", expectedEmail);
        cv.Set("language", language);
        var result = await target.RunAsync(cv, plan);

        // Assert
        Assert.Contains(expectedBody, result.Result, StringComparison.OrdinalIgnoreCase);
        Assert.True(expectedBody.Length < result.Result.Length);
    }

    [Fact]
    public async Task CanExecutePanWithTreeStepsAsync()
    {
        // Arrange
        IKernel target = this.InitializeKernel();
        var goal = "Write a poem or joke and send it in an e-mail to Kai.";
        var plan = new Plan(goal);
        var subPlan = new Plan("Write a poem or joke");

        var emailSkill = target.ImportSkill(new EmailSkillFake());

        // Arrange
        var returnContext = target.CreateNewContext();

        subPlan.AddSteps(emailSkill["WritePoemAsync"], emailSkill["WritePoemAsync"], emailSkill["WritePoemAsync"]);
        plan.AddSteps(subPlan, emailSkill["SendEmailAsync"]);
        plan.State.Set("email_address", "something@email.com");

        // Act
        var result = await target.RunAsync("PlanInput", plan);

        // Assert
        Assert.NotNull(result);
        Assert.Equal(
            $"Sent email to: something@email.com. Body: Roses are red, violets are blue, Roses are red, violets are blue, Roses are red, violets are blue, PlanInput is hard, so is this test. is hard, so is this test. is hard, so is this test.",
            result.Result);
    }

    private IKernel InitializeKernel(bool useEmbeddings = false)
    {
        AzureOpenAIConfiguration? azureOpenAIConfiguration = this._configuration.GetSection("AzureOpenAI").Get<AzureOpenAIConfiguration>();
        Assert.NotNull(azureOpenAIConfiguration);

        AzureOpenAIConfiguration? azureOpenAIEmbeddingsConfiguration = this._configuration.GetSection("AzureOpenAIEmbeddings").Get<AzureOpenAIConfiguration>();
        Assert.NotNull(azureOpenAIEmbeddingsConfiguration);

        var builder = Kernel.Builder
            .WithLogger(this._logger)
            .Configure(config =>
            {
                config.AddAzureTextCompletionService(
                    serviceId: azureOpenAIConfiguration.ServiceId,
                    deploymentName: azureOpenAIConfiguration.DeploymentName,
                    endpoint: azureOpenAIConfiguration.Endpoint,
                    apiKey: azureOpenAIConfiguration.ApiKey);

                if (useEmbeddings)
                {
                    config.AddAzureTextEmbeddingGenerationService(
                        serviceId: azureOpenAIEmbeddingsConfiguration.ServiceId,
                        deploymentName: azureOpenAIEmbeddingsConfiguration.DeploymentName,
                        endpoint: azureOpenAIEmbeddingsConfiguration.Endpoint,
                        apiKey: azureOpenAIEmbeddingsConfiguration.ApiKey);
                }

                config.SetDefaultTextCompletionService(azureOpenAIConfiguration.ServiceId);
            });

        if (useEmbeddings)
        {
            builder = builder.WithMemoryStorage(new VolatileMemoryStore());
        }

        var kernel = builder.Build();

        // Import all sample skills available for demonstration purposes.
        TestHelpers.ImportSampleSkills(kernel);

        var emailSkill = kernel.ImportSkill(new EmailSkillFake());
        return kernel;
    }

    private readonly ILogger _logger;
    private readonly RedirectOutput _testOutputHelper;
    private readonly IConfigurationRoot _configuration;

    public void Dispose()
    {
        this.Dispose(true);
        GC.SuppressFinalize(this);
    }

    ~PlanTests()
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
