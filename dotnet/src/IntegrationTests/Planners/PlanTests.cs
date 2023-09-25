// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Threading.Tasks;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Memory;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.Planning;
using SemanticKernel.IntegrationTests.Fakes;
using SemanticKernel.IntegrationTests.TestSettings;
using Xunit;
using Xunit.Abstractions;

namespace SemanticKernel.IntegrationTests.Planners;

public sealed class PlanTests : IDisposable
{
    public PlanTests(ITestOutputHelper output)
    {
        this._loggerFactory = NullLoggerFactory.Instance;
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
        Assert.NotEmpty(plan.Name);
        Assert.Equal(nameof(Plan), plan.PluginName);
        Assert.Empty(plan.Steps);
    }

    [Theory]
    [InlineData("This is a story about a dog.", "kai@email.com")]
    public async Task CanExecuteRunSimpleAsync(string inputToEmail, string expectedEmail)
    {
        // Arrange
        IKernel target = this.InitializeKernel();
        var emailFunctions = target.ImportFunctions(new EmailPluginFake());
        var expectedBody = $"Sent email to: {expectedEmail}. Body: {inputToEmail}".Trim();

        var plan = new Plan(emailFunctions["SendEmail"]);

        // Act
        var cv = new ContextVariables();
        cv.Update(inputToEmail);
        cv.Set("email_address", expectedEmail);
        var result = await target.RunAsync(cv, plan);

        // Assert
        Assert.Equal(expectedBody, result.GetValue<string>());
    }

    [Theory]
    [InlineData("This is a story about a dog.", "kai@email.com")]
    public async Task CanExecuteAsChatAsync(string inputToEmail, string expectedEmail)
    {
        // Arrange
        IKernel target = this.InitializeKernel(false, true);

        var emailFunctions = target.ImportFunctions(new EmailPluginFake());
        var expectedBody = $"Sent email to: {expectedEmail}. Body: {inputToEmail}".Trim();

        var plan = new Plan(emailFunctions["SendEmail"]);

        // Act
        var cv = new ContextVariables();
        cv.Update(inputToEmail);
        cv.Set("email_address", expectedEmail);
        var result = await target.RunAsync(cv, plan);

        // Assert
        Assert.Equal(expectedBody, result.GetValue<string>());
    }

    [Theory]
    [InlineData("Send a story to kai.", "This is a story about a dog.", "French", "kai@email.com")]
    public async Task CanExecuteRunSimpleStepsAsync(string goal, string inputToTranslate, string language, string expectedEmail)
    {
        // Arrange
        IKernel target = this.InitializeKernel();
        var emailFunctions = target.ImportFunctions(new EmailPluginFake());
        var writerPlugin = TestHelpers.ImportSamplePlugins(target, "WriterPlugin");
        var expectedBody = $"Sent email to: {expectedEmail}. Body:".Trim();

        var plan = new Plan(goal);
        plan.AddSteps(writerPlugin["Translate"], emailFunctions["SendEmail"]);

        // Act
        var cv = new ContextVariables();
        cv.Update(inputToTranslate);
        cv.Set("email_address", expectedEmail);
        cv.Set("language", language);
        var result = (await target.RunAsync(cv, plan)).GetValue<string>();

        // Assert
        Assert.NotNull(result);
        Assert.Contains(expectedBody, result, StringComparison.OrdinalIgnoreCase);
        Assert.True(expectedBody.Length < result.Length);
    }

    [Fact]
    public async Task CanExecutePlanWithTreeStepsAsync()
    {
        // Arrange
        IKernel target = this.InitializeKernel();
        var goal = "Write a poem or joke and send it in an e-mail to Kai.";
        var plan = new Plan(goal);
        var subPlan = new Plan("Write a poem or joke");

        var emailFunctions = target.ImportFunctions(new EmailPluginFake());

        // Arrange
        var returnContext = target.CreateNewContext();

        subPlan.AddSteps(emailFunctions["WritePoem"], emailFunctions["WritePoem"], emailFunctions["WritePoem"]);
        plan.AddSteps(subPlan, emailFunctions["SendEmail"]);
        plan.State.Set("email_address", "something@email.com");

        // Act
        var result = await target.RunAsync("PlanInput", plan);

        // Assert
        Assert.NotNull(result);
        Assert.Equal(
            "Sent email to: something@email.com. Body: Roses are red, violets are blue, Roses are red, violets are blue, Roses are red, violets are blue, PlanInput is hard, so is this test. is hard, so is this test. is hard, so is this test.",
            result.GetValue<string>());
    }

    [Theory]
    [InlineData("", "Write a poem or joke and send it in an e-mail to Kai.", "")]
    [InlineData("Hello World!", "Write a poem or joke and send it in an e-mail to Kai.", "some_email@email.com")]
    public async Task CanExecuteRunPlanSimpleManualStateAsync(string input, string goal, string email)
    {
        // Arrange
        IKernel target = this.InitializeKernel();
        var emailFunctions = target.ImportFunctions(new EmailPluginFake());

        // Create the input mapping from parent (plan) plan state to child plan (sendEmailPlan) state.
        var cv = new ContextVariables();
        cv.Set("email_address", "$TheEmailFromState");
        var sendEmailPlan = new Plan(emailFunctions["SendEmail"])
        {
            Parameters = cv,
        };

        var plan = new Plan(goal);
        plan.AddSteps(sendEmailPlan);
        plan.State.Set("TheEmailFromState", email); // manually prepare the state

        // Act
        var result = await target.StepAsync(input, plan);

        // Assert
        var expectedBody = string.IsNullOrEmpty(input) ? goal : input;
        Assert.Single(result.Steps);
        Assert.Equal(1, result.NextStepIndex);
        Assert.False(result.HasNextStep);
        Assert.Equal(goal, plan.Description);
        Assert.Equal($"Sent email to: {email}. Body: {expectedBody}".Trim(), plan.State.ToString());
    }

    [Theory]
    [InlineData("", "Write a poem or joke and send it in an e-mail to Kai.", "")]
    [InlineData("Hello World!", "Write a poem or joke and send it in an e-mail to Kai.", "some_email@email.com")]
    public async Task CanExecuteRunPlanSimpleManualStateNoVariableAsync(string input, string goal, string email)
    {
        // Arrange
        IKernel target = this.InitializeKernel();
        var emailFunctions = target.ImportFunctions(new EmailPluginFake());

        // Create the input mapping from parent (plan) plan state to child plan (sendEmailPlan) state.
        var cv = new ContextVariables();
        cv.Set("email_address", string.Empty);
        var sendEmailPlan = new Plan(emailFunctions["SendEmail"])
        {
            Parameters = cv,
        };

        var plan = new Plan(goal);
        plan.AddSteps(sendEmailPlan);
        plan.State.Set("email_address", email); // manually prepare the state

        // Act
        var result = await target.StepAsync(input, plan);

        // Assert
        var expectedBody = string.IsNullOrEmpty(input) ? goal : input;
        Assert.Single(result.Steps);
        Assert.Equal(1, result.NextStepIndex);
        Assert.False(result.HasNextStep);
        Assert.Equal(goal, plan.Description);
        Assert.Equal($"Sent email to: {email}. Body: {expectedBody}".Trim(), plan.State.ToString());
    }

    [Theory]
    [InlineData("", "Write a poem or joke and send it in an e-mail to Kai.", "")]
    [InlineData("Hello World!", "Write a poem or joke and send it in an e-mail to Kai.", "some_email@email.com")]
    public async Task CanExecuteRunPlanManualStateAsync(string input, string goal, string email)
    {
        // Arrange
        IKernel target = this.InitializeKernel();
        var emailFunctions = target.ImportFunctions(new EmailPluginFake());

        // Create the input mapping from parent (plan) plan state to child plan (sendEmailPlan) state.
        var cv = new ContextVariables();
        cv.Set("email_address", "$TheEmailFromState");
        var sendEmailPlan = new Plan(emailFunctions["SendEmail"])
        {
            Parameters = cv
        };

        var plan = new Plan(goal);
        plan.AddSteps(sendEmailPlan);
        plan.State.Set("TheEmailFromState", email); // manually prepare the state

        // Act
        var result = await target.StepAsync(input, plan);

        // Assert
        var expectedBody = string.IsNullOrEmpty(input) ? goal : input;
        Assert.False(plan.HasNextStep);
        Assert.Equal(goal, plan.Description);
        Assert.Equal($"Sent email to: {email}. Body: {expectedBody}".Trim(), plan.State.ToString());
    }

    [Theory]
    [InlineData("Summarize an input, translate to french, and e-mail to Kai", "This is a story about a dog.", "French", "Kai", "Kai@example.com")]
    public async Task CanExecuteRunPlanAsync(string goal, string inputToSummarize, string inputLanguage, string inputName, string expectedEmail)
    {
        // Arrange
        IKernel target = this.InitializeKernel();

        var summarizePlugin = TestHelpers.ImportSamplePlugins(target, "SummarizePlugin");
        var writerPlugin = TestHelpers.ImportSamplePlugins(target, "WriterPlugin");
        var emailFunctions = target.ImportFunctions(new EmailPluginFake());

        var expectedBody = $"Sent email to: {expectedEmail}. Body:".Trim();

        var summarizePlan = new Plan(summarizePlugin["Summarize"]);

        var cv = new ContextVariables();
        cv.Set("language", inputLanguage);
        var outputs = new List<string>
        {
            "TRANSLATED_SUMMARY"
        };
        var translatePlan = new Plan(writerPlugin["Translate"])
        {
            Parameters = cv,
            Outputs = outputs,
        };

        cv = new ContextVariables();
        cv.Update(inputName);
        outputs = new List<string>
        {
            "TheEmailFromState"
        };
        var getEmailPlan = new Plan(emailFunctions["GetEmailAddress"])
        {
            Parameters = cv,
            Outputs = outputs,
        };

        cv = new ContextVariables();
        cv.Set("email_address", "$TheEmailFromState");
        cv.Set("input", "$TRANSLATED_SUMMARY");
        var sendEmailPlan = new Plan(emailFunctions["SendEmail"])
        {
            Parameters = cv
        };

        var plan = new Plan(goal);
        plan.AddSteps(summarizePlan, translatePlan, getEmailPlan, sendEmailPlan);

        // Act
        var result = await target.StepAsync(inputToSummarize, plan);
        Assert.Equal(4, result.Steps.Count);
        Assert.Equal(1, result.NextStepIndex);
        Assert.True(result.HasNextStep);
        result = await target.StepAsync(result);
        Assert.Equal(4, result.Steps.Count);
        Assert.Equal(2, result.NextStepIndex);
        Assert.True(result.HasNextStep);
        result = await target.StepAsync(result);
        Assert.Equal(4, result.Steps.Count);
        Assert.Equal(3, result.NextStepIndex);
        Assert.True(result.HasNextStep);
        result = await target.StepAsync(result);

        // Assert
        Assert.Equal(4, result.Steps.Count);
        Assert.Equal(4, result.NextStepIndex);
        Assert.False(result.HasNextStep);
        Assert.Equal(goal, plan.Description);
        Assert.Contains(expectedBody, plan.State.ToString(), StringComparison.OrdinalIgnoreCase);
        Assert.True(expectedBody.Length < plan.State.ToString().Length);
    }

    [Theory]
    [InlineData("Summarize an input, translate to french, and e-mail to Kai", "This is a story about a dog.", "French", "Kai", "Kai@example.com")]
    public async Task CanExecuteRunSequentialAsync(string goal, string inputToSummarize, string inputLanguage, string inputName, string expectedEmail)
    {
        // Arrange
        IKernel target = this.InitializeKernel();
        var summarizePlugin = TestHelpers.ImportSamplePlugins(target, "SummarizePlugin");
        var writerPlugin = TestHelpers.ImportSamplePlugins(target, "WriterPlugin");
        var emailFunctions = target.ImportFunctions(new EmailPluginFake());

        var expectedBody = $"Sent email to: {expectedEmail}. Body:".Trim();

        var summarizePlan = new Plan(summarizePlugin["Summarize"]);

        var cv = new ContextVariables();
        cv.Set("language", inputLanguage);
        var outputs = new List<string>
        {
            "TRANSLATED_SUMMARY"
        };

        var translatePlan = new Plan(writerPlugin["Translate"])
        {
            Parameters = cv,
            Outputs = outputs,
        };

        cv = new ContextVariables();
        cv.Update(inputName);
        outputs = new List<string>
        {
            "TheEmailFromState"
        };
        var getEmailPlan = new Plan(emailFunctions["GetEmailAddress"])
        {
            Parameters = cv,
            Outputs = outputs,
        };

        cv = new ContextVariables();
        cv.Set("email_address", "$TheEmailFromState");
        cv.Set("input", "$TRANSLATED_SUMMARY");
        var sendEmailPlan = new Plan(emailFunctions["SendEmail"])
        {
            Parameters = cv
        };

        var plan = new Plan(goal);
        plan.AddSteps(summarizePlan, translatePlan, getEmailPlan, sendEmailPlan);

        // Act
        var result = (await target.RunAsync(inputToSummarize, plan)).GetValue<string>();

        // Assert
        Assert.NotNull(result);
        Assert.Contains(expectedBody, result, StringComparison.OrdinalIgnoreCase);
        Assert.True(expectedBody.Length < result.Length);
    }

    [Theory]
    [InlineData("Summarize an input, translate to french, and e-mail to Kai", "This is a story about a dog.", "French", "Kai", "Kai@example.com")]
    public async Task CanExecuteRunSequentialOnDeserializedPlanAsync(string goal, string inputToSummarize, string inputLanguage, string inputName,
        string expectedEmail)
    {
        // Arrange
        IKernel target = this.InitializeKernel();
        var summarizePlugin = TestHelpers.ImportSamplePlugins(target, "SummarizePlugin");
        var writerPlugin = TestHelpers.ImportSamplePlugins(target, "WriterPlugin");
        var emailFunctions = target.ImportFunctions(new EmailPluginFake());

        var expectedBody = $"Sent email to: {expectedEmail}. Body:".Trim();

        var summarizePlan = new Plan(summarizePlugin["Summarize"]);

        var cv = new ContextVariables();
        cv.Set("language", inputLanguage);
        var outputs = new List<string>
        {
            "TRANSLATED_SUMMARY"
        };

        var translatePlan = new Plan(writerPlugin["Translate"])
        {
            Parameters = cv,
            Outputs = outputs,
        };

        cv = new ContextVariables();
        cv.Update(inputName);
        outputs = new List<string>
        {
            "TheEmailFromState"
        };
        var getEmailPlan = new Plan(emailFunctions["GetEmailAddress"])
        {
            Parameters = cv,
            Outputs = outputs,
        };

        cv = new ContextVariables();
        cv.Set("email_address", "$TheEmailFromState");
        cv.Set("input", "$TRANSLATED_SUMMARY");
        var sendEmailPlan = new Plan(emailFunctions["SendEmail"])
        {
            Parameters = cv
        };

        var plan = new Plan(goal);
        plan.AddSteps(summarizePlan, translatePlan, getEmailPlan, sendEmailPlan);

        // Act
        var serializedPlan = plan.ToJson();
        var deserializedPlan = Plan.FromJson(serializedPlan, target.Functions);
        var result = (await target.RunAsync(inputToSummarize, deserializedPlan)).GetValue<string>();

        // Assert
        Assert.NotNull(result);
        Assert.Contains(expectedBody, result, StringComparison.OrdinalIgnoreCase);
        Assert.True(expectedBody.Length < result.Length);
    }

    [Theory]
    [InlineData("Summarize an input, translate to french, and e-mail to Kai", "This is a story about a dog.", "French", "kai@email.com")]
    public async Task CanExecuteRunSequentialFunctionsAsync(string goal, string inputToSummarize, string inputLanguage, string expectedEmail)
    {
        // Arrange
        IKernel target = this.InitializeKernel();

        var summarizePlugin = TestHelpers.ImportSamplePlugins(target, "SummarizePlugin");
        var writerPlugin = TestHelpers.ImportSamplePlugins(target, "WriterPlugin");
        var emailFunctions = target.ImportFunctions(new EmailPluginFake());

        var expectedBody = $"Sent email to: {expectedEmail}. Body:".Trim();

        var summarizePlan = new Plan(summarizePlugin["Summarize"]);
        var translatePlan = new Plan(writerPlugin["Translate"]);
        var sendEmailPlan = new Plan(emailFunctions["SendEmail"]);

        var plan = new Plan(goal);
        plan.AddSteps(summarizePlan, translatePlan, sendEmailPlan);

        // Act
        var cv = new ContextVariables();
        cv.Update(inputToSummarize);
        cv.Set("email_address", expectedEmail);
        cv.Set("language", inputLanguage);
        var result = await target.RunAsync(cv, plan);

        // Assert
        Assert.Contains(expectedBody, result.GetValue<string>(), StringComparison.OrdinalIgnoreCase);
    }

    [Theory]
    [InlineData("computers")]
    public async Task CanImportAndRunPlanAsync(string input)
    {
        // Arrange
        IKernel target = this.InitializeKernel();
        var emailFunctions = target.ImportFunctions(new EmailPluginFake());

        var plan = new Plan("Write a poem about a topic and send in an email.");

        var writePoem = new Plan(emailFunctions["WritePoem"]);
        // fileStep.Parameters["input"] = "$INPUT";
        writePoem.Outputs.Add("POEM");

        var sendEmail = new Plan(emailFunctions["SendEmail"]);
        sendEmail.Parameters["input"] = "$POEM";
        sendEmail.Outputs.Add("EMAIL_RESULT");

        plan.AddSteps(writePoem, sendEmail);
        plan.Outputs.Add("EMAIL_RESULT");

        //Act
        var t = target.ImportPlan(plan);

        var result = await t.InvokeAsync(input, target);

        // Assert
        Assert.NotNull(result);
        Assert.Equal($"Sent email to: default@email.com. Body: Roses are red, violets are blue, {input} is hard, so is this test.", result.GetValue<string>());
    }

    private IKernel InitializeKernel(bool useEmbeddings = false, bool useChatModel = false)
    {
        AzureOpenAIConfiguration? azureOpenAIConfiguration = this._configuration.GetSection("AzureOpenAI").Get<AzureOpenAIConfiguration>();
        Assert.NotNull(azureOpenAIConfiguration);

        AzureOpenAIConfiguration? azureOpenAIEmbeddingsConfiguration = this._configuration.GetSection("AzureOpenAIEmbeddings").Get<AzureOpenAIConfiguration>();
        Assert.NotNull(azureOpenAIEmbeddingsConfiguration);

        var builder = Kernel.Builder.WithLoggerFactory(this._loggerFactory);

        if (useChatModel)
        {
            builder.WithAzureChatCompletionService(
                deploymentName: azureOpenAIConfiguration.ChatDeploymentName!,
                endpoint: azureOpenAIConfiguration.Endpoint,
                apiKey: azureOpenAIConfiguration.ApiKey);
        }
        else
        {
            builder.WithAzureTextCompletionService(
                deploymentName: azureOpenAIConfiguration.DeploymentName,
                endpoint: azureOpenAIConfiguration.Endpoint,
                apiKey: azureOpenAIConfiguration.ApiKey);
        }

        if (useEmbeddings)
        {
            builder
                .WithAzureTextEmbeddingGenerationService(
                    deploymentName: azureOpenAIEmbeddingsConfiguration.DeploymentName,
                    endpoint: azureOpenAIEmbeddingsConfiguration.Endpoint,
                    apiKey: azureOpenAIEmbeddingsConfiguration.ApiKey)
                .WithMemoryStorage(new VolatileMemoryStore());
        }

        var kernel = builder.Build();

        // Import all sample plugins available for demonstration purposes.
        TestHelpers.ImportAllSamplePlugins(kernel);

        kernel.ImportFunctions(new EmailPluginFake());
        return kernel;
    }

    private readonly ILoggerFactory _loggerFactory;
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
            if (this._loggerFactory is IDisposable ld)
            {
                ld.Dispose();
            }

            this._testOutputHelper.Dispose();
        }
    }
}
