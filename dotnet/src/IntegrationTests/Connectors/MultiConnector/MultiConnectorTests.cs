// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Net.WebSockets;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.AI.TextCompletion;
using Microsoft.SemanticKernel.Connectors.AI.MultiConnector;
using Microsoft.SemanticKernel.Connectors.AI.MultiConnector.Analysis;
using Microsoft.SemanticKernel.Connectors.AI.MultiConnector.PromptSettings;
using Microsoft.SemanticKernel.Connectors.AI.Oobabooga.TextCompletion;
using Microsoft.SemanticKernel.Connectors.AI.OpenAI.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.AI.OpenAI.TextCompletion;
using Microsoft.SemanticKernel.Connectors.AI.OpenAI.Tokenizers;
using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.SemanticKernel.Planning;
using Microsoft.SemanticKernel.Planning.Sequential;
using Microsoft.SemanticKernel.Text;
using SemanticKernel.IntegrationTests.TestSettings;
using Xunit;
using Xunit.Abstractions;

namespace SemanticKernel.IntegrationTests.Connectors.MultiConnector;

/// <summary>
/// Integration tests for <see cref=" OobaboogaTextCompletion"/>.
/// </summary>
public sealed class MultiConnectorTests : IDisposable
{
    private const string StartGoal =
        "The goal of this plan is to evaluate the capabilities of a smaller LLM model. Start by writing a text of about 100 words on a given topic, as the input parameter of the plan. Then use distinct functions from the available skills on the input text and/or the previous functions results, choosing parameters in such a way that you know you will succeed at running each function but a smaller model might not. Try to propose steps of distinct difficulties so that models of distinct capabilities might succeed on some functions and fail on others. In a second phase, you will be asked to evaluate the function answers from smaller models. Please beware of correct Xml tags, attributes, and parameter names when defined and when reused.";

    private const string PlansDirectory = ".\\Connectors\\MultiConnector\\Plans\\";
    private const string TextsDirectory = ".\\Connectors\\MultiConnector\\Texts\\";

    private readonly ILogger _logger;
    private readonly IConfigurationRoot _configuration;
    private readonly List<ClientWebSocket> _webSockets = new();
    private readonly Func<ClientWebSocket> _webSocketFactory;
    private readonly RedirectOutput _testOutputHelper;
    private readonly Func<string, int> _gp3TokenCounter = s => GPT3Tokenizer.Encode(s).Count;
    private readonly Func<string, int> _wordCounter = s => s.Split(' ').Length;
    private readonly string _planDirectory = System.IO.Path.Combine(Environment.CurrentDirectory, PlansDirectory);
    private readonly string _textDirectory = System.IO.Path.Combine(Environment.CurrentDirectory, TextsDirectory);
    private readonly CancellationTokenSource _cleanupToken = new();

    public MultiConnectorTests(ITestOutputHelper output)
    {
        //this._logger = NullLogger.Instance;
        this._logger = new XunitLogger<object>(output);
        this._testOutputHelper = new RedirectOutput(output);

        // Load configuration
        this._configuration = new ConfigurationBuilder()
            .AddJsonFile(path: "testsettings.json", optional: false, reloadOnChange: true)
            .AddJsonFile(path: "testsettings.development.json", optional: true, reloadOnChange: true)
            .AddEnvironmentVariables()
            .AddUserSecrets<MultiConnectorTests>()
            .Build();

        this._webSocketFactory = () =>
        {
            var toReturn = new ClientWebSocket();
            this._webSockets.Add(toReturn);
            return toReturn;
        };
    }

    /// <summary>
    /// This test method uses a plan loaded from a file, an input text of a particular difficulty, and all models configured in settings file
    /// </summary>
    [Theory]
    [InlineData(1, 1, 1, "Summarize.json", "Comm_simple.txt", "Danse_simple.txt", "SummarizeSkill", "MiscSkill")]
    [InlineData(1, 1, 1, "Summarize_Topics_ElementAt.json", "Comm_medium.txt", "Danse_simple.txt", "SummarizeSkill", "MiscSkill")]
    public async Task ChatGptOffloadsToMultipleOobaboogaUsingFileAsync(double durationWeight, double costWeight, int nbPromptTests, string planFileName, string inputTextFileName, string validationTextFileName, params string[] skillNames)
    {
        await this.ChatGptOffloadsToSingleOobaboogaUsingFileAsync("", nbPromptTests, planFileName, inputTextFileName, validationTextFileName, skillNames).ConfigureAwait(false);
    }

    /// <summary>
    /// This test method uses a plan loaded from a file, together with an input text loaded from a file, and adds a single completion model from its name as configured in the settings file.
    /// </summary>
    //[Theory(Skip = "This test is for manual verification.")]
    [Theory]
    //[InlineData("TheBloke_orca_mini_3B-GGML", 1, "Summarize.json", "Comm_simple.txt","Danse_simple.txt", "SummarizeSkill", "MiscSkill")]
    //[InlineData("TheBloke_orca_mini_3B-GGML", 1, "Summarize.json", "Comm_medium.txt", "Danse_medium.txt", "SummarizeSkill", "MiscSkill")]
    //[InlineData("TheBloke_orca_mini_3B-GGML", 1, "Summarize.json", "Comm_hard.txt", "Danse_hard.txt", "SummarizeSkill", "MiscSkill")]
    //[InlineData("TheBloke_StableBeluga-7B-GGML", 1, "Summarize.json", "Comm_simple.txt","Danse_simple.txt", "SummarizeSkill", "MiscSkill")]
    //[InlineData("TheBloke_StableBeluga-7B-GGML", 1, "Summarize.json", "Comm_medium.txt", "Danse_medium.txt", "SummarizeSkill", "MiscSkill")]
    //[InlineData("TheBloke_StableBeluga-7B-GGML", 1, "Summarize.json", "Comm_hard.txt", "Danse_hard.txt", "SummarizeSkill", "MiscSkill")]
    [InlineData("TheBloke_StableBeluga-13B-GGML", 1, "Summarize.json", "Comm_simple.txt", "Danse_simple.txt", "SummarizeSkill", "MiscSkill")]
    [InlineData("TheBloke_StableBeluga-13B-GGML", 1, "Summarize.json", "Comm_medium.txt", "Danse_medium.txt", "SummarizeSkill", "MiscSkill")]
    [InlineData("TheBloke_StableBeluga-13B-GGML", 1, "Summarize.json", "Comm_hard.txt", "Danse_hard.txt", "SummarizeSkill", "MiscSkill")]
    [InlineData("TheBloke_StableBeluga-13B-GGML", 1, "Summarize_Topics_ElementAt.json", "Comm_simple.txt", "Danse_simple.txt", "SummarizeSkill", "MiscSkill")]
    [InlineData("TheBloke_StableBeluga-13B-GGML", 1, "Summarize_Topics_ElementAt.json", "Comm_medium.txt", "Danse_medium.txt", "SummarizeSkill", "MiscSkill")]
    [InlineData("TheBloke_StableBeluga-13B-GGML", 1, "Summarize_Topics_ElementAt.json", "Comm_hard.txt", "Danse_hard.txt", "SummarizeSkill", "MiscSkill")]
    public async Task ChatGptOffloadsToSingleOobaboogaUsingFileAsync(string completion, int nbTests, string planFile, string inputFile, string validationFile, params string[] skills)
    {
        // Load the plan from the provided file path
        var planPath = System.IO.Path.Combine(this._planDirectory, planFile);
        var textPath = System.IO.Path.Combine(this._textDirectory, inputFile);
        var validationTextPath = System.IO.Path.Combine(this._textDirectory, validationFile);

        Func<IKernel, CancellationToken, bool, Task<Plan>> planFactory = async (kernel, token, isValidation) =>
        {
            var planJson = await System.IO.File.ReadAllTextAsync(planPath, token);
            var ctx = kernel.CreateNewContext();
            var plan = Plan.FromJson(planJson, ctx, true);
            var inputPath = textPath;
            if (isValidation)
            {
                inputPath = validationTextPath;
            }

            var input = await System.IO.File.ReadAllTextAsync(inputPath, token);
            plan.State.Update(input);
            return plan;
        };

        List<string>? modelNames = null;
        if (!string.IsNullOrEmpty(completion))
        {
            modelNames = new List<string> { completion };
        }

        await this.ChatGptOffloadsToOobaboogaAsync(planFactory, modelNames, nbTests, skills).ConfigureAwait(false);
    }

    // This test method uses the SequentialPlanner to create a plan based on difficulty
    //[Theory(Skip = "This test is for manual verification.")]
    [Theory()]
    //[InlineData("",  1, "medium", "SummarizeSkill", "MiscSkill")]
    //[InlineData("TheBloke_StableBeluga-13B-GGML", 1, "medium", "SummarizeSkill", "MiscSkill")]
    [InlineData("TheBloke_StableBeluga-13B-GGML", 1, "medium", "WriterSkill", "MiscSkill")]
    public async Task ChatGptOffloadsToOobaboogaUsingPlannerAsync(string completionName, int nbPromptTests, string difficulty, params string[] skillNames)
    {
        // Create a plan using SequentialPlanner based on difficulty
        var modifiedStartGoal = StartGoal.Replace("distinct difficulties", $"{difficulty} difficulties", StringComparison.OrdinalIgnoreCase);

        Func<IKernel, CancellationToken, bool, Task<Plan>> planFactory = async (kernel, token, isValidation) =>
        {
            var planner = new SequentialPlanner(kernel,
                new SequentialPlannerConfig { RelevancyThreshold = 0.65, MaxRelevantFunctions = 30, Memory = kernel.Memory });

            var plan = await planner.CreatePlanAsync(modifiedStartGoal, token);
            return plan;
        };

        List<string>? modelNames = null;
        if (!string.IsNullOrEmpty(completionName))
        {
            modelNames = new List<string> { completionName };
        }

        await this.ChatGptOffloadsToOobaboogaAsync(planFactory, modelNames, nbPromptTests, skillNames).ConfigureAwait(false);
    }

    private async Task ChatGptOffloadsToOobaboogaAsync(Func<IKernel, CancellationToken, bool, Task<Plan>> planFactory, List<string>? modelNames, int nbPromptTests, params string[] skillNames)
    {
        // Arrange

        this._logger.LogTrace("# Starting test in environment directory: {0}\n", Environment.CurrentDirectory);

        var sw = Stopwatch.StartNew();

        var multiConnectorConfiguration = this._configuration.GetSection("MultiConnector").Get<MultiConnectorConfiguration>();
        Assert.NotNull(multiConnectorConfiguration);

        var creditor = new CallRequestCostCreditor();

        //We configure settings to enable analysis, and let the connector discover the best connector settings, updating on the fly and deleting analysis file

        this._logger.LogTrace("\n# Creating MultiTextCompletionSettings\n");

        // The most common settings for a MultiTextCompletion are illustrated below, most of them have default values and are optional
        var settings = new MultiTextCompletionSettings()
        {
            //We start with prompt sampling off to control precisely the prompt types we want to test by enabling this parameter on specific periods
            EnablePromptSampling = false,
            // We only collect one sample per prompt type for tests for now. We'll enable collecting one more sample for final validation on unseen material
            MaxInstanceNb = 1,
            // We'll use a simple creditor to track usage costs
            Creditor = creditor,
            // Prompt type require a signature for identification, and we'll use the first 11 characters of the prompt as signature
            PromptTruncationLength = 11,
            //This optional feature upgrade prompt signature by adjusting prompt starts to the true complete prefix of the template preceding user input. This is useful where many prompt would yield overlapping starts, but it may falsely create new prompt types if some inputs have partially overlapping starts. 
            // Prompts with variable content at the start are currently not accounted for automatically though, and need either a manual regex to avoid creating increasing prompt types, or using the FreezePromptTypes setting but the first alternative is preferred because unmatched prompts will go through the entire settings unless a regex matches them. 
            AdjustPromptStarts = false,
            // Uncomment to enable additional logging of MultiTextCompletion calls, results and/or test sample collection
            LogCallResult = true,
            //LogTestCollection = true,
            // In those tests, we don't have information about the underlying model hosts, so we can't make performance comparisons between models. Instead, arbitrary cost per token are defined in settings, and usage costs are computed.
            ConnectorComparer = MultiTextCompletionSettings.GetWeightedConnectorComparer(0, 1),
            // Adding a simple transform for template-less models, which require a line break at the end of the prompt
            GlobalPromptTransform = new PromptTransform()
            {
                TransformFunction = (s, context) => s.EndsWith("\n", StringComparison.OrdinalIgnoreCase) ? s : s + "\n",
            },
            // Global parameter allow injecting common blocks in various prompts, using named string interpolation tokens
            GlobalParameters = multiConnectorConfiguration.GlobalParameters,
            // Analysis settings are an important part of the main settings, dealing with how to collect samples, conduct tests, evaluate them and update the connector settings
            AnalysisSettings = new MultiCompletionAnalysisSettings()
            {
                // Analysis must be enabled for analysis jobs to be created from sample usage, we'll play with that parameter
                EnableAnalysis = false,
                // This is the number of tests to run and validate for each prompt type before it can be considered able to handle the prompt type
                NbPromptTests = nbPromptTests,
                // Because we only collect one sample, we have to artificially raise the temperature for the test completion request settings, in order to induce diverse results
                TestsTemperatureTransform = d => Math.Max(d, 0.7),
                // We use manual release of analysis task to make sure analysis event is only fired once with the final result
                AnalysisAwaitsManualTrigger = true,
                // Accordingly, delays and periods are also removed
                AnalysisDelay = TimeSpan.Zero,
                TestsPeriod = TimeSpan.Zero,
                EvaluationPeriod = TimeSpan.Zero,
                SuggestionPeriod = TimeSpan.Zero,
                // Secondary connectors usually don't support multiple concurrent requests, default Test parallelism defaults to 1 but you can change that here
                MaxDegreeOfParallelismTests = 1,
                // Change the following settings if you run all models on the same machine and want to limit the number of concurrent connectors
                MaxDegreeOfParallelismConnectorsByTest = 3,
                // Primary connector ChatGPT supports multiple concurrent request, default parallelism is 5 but you can change that here 
                MaxDegreeOfParallelismEvaluations = 5,
                // We update the settings live from suggestion following analysis
                UpdateSuggestedSettings = true,
                // For instrumented data in file format, feel free to uncomment either of the following lines
                DeleteAnalysisFile = false,
                SaveSuggestedSettings = true,
                // In order to spare on fees, you can use self vetting of prompt tests by the tested connector, which may work well depending on the models vetted
                //UseSelfVetting = false,
            },
            // In order to highlight prompts and response in log trace, you can uncomment the following lines
            //PromptLogsJsonEncoded = false,
            //PromptLogTruncationLength = 500,
            //PromptLogTruncationFormat = @"
            //================================= START ====== PROMPT/RESULT =============================================
            //{0}

            //(...)

            //{1}
            //================================== END ====== PROMPT/RESULT =============================================="
        };

        // Cleanup in case the previous test failed to delete the analysis file
        if (File.Exists(settings.AnalysisSettings.AnalysisFilePath))
        {
            this._logger.LogTrace("Deleting preexisting analysis file: {0}\n", settings.AnalysisSettings.AnalysisFilePath);
            File.Delete(settings.AnalysisSettings.AnalysisFilePath);
        }

        var kernel = this.InitializeKernel(settings, modelNames, multiConnectorConfiguration, cancellationToken: this._cleanupToken.Token);

        if (kernel == null)
        {
            return;
        }

        var prepareKernelTimeElapsed = sw.Elapsed;

        this._logger.LogTrace("\n# Loading Skills\n");

        var skills = TestHelpers.GetSkills(kernel, skillNames);

        // Act

        // Create a plan
        this._logger.LogTrace("\n# Loading Test plan\n");
        var plan = await planFactory(kernel, this._cleanupToken.Token, false);
        var planJson = plan.ToJson();

        this._logger.LogDebug("Plan used for multi-connector evaluation: {0}", planJson);

        settings.Creditor!.Reset();

        var planBuildingTimeElapsed = sw.Elapsed;

        // Execute the plan once with primary connector

        var ctx = kernel.CreateNewContext();

        this._logger.LogTrace("\n# 1st Run of plan with primary connector\n");

        //We enable sampling and analysis trigger. There is a lock to prevent automatic analysis starting while the test is running, but we'll manually trigger analysis after the test is done

        settings.EnablePromptSampling = true;

        settings.AnalysisSettings.EnableAnalysis = true;

        var firstResult = await kernel.RunAsync(ctx.Variables, this._cleanupToken.Token, plan).ConfigureAwait(false);

        var planRunOnceTimeElapsed = sw.Elapsed;

        this._logger.LogTrace("\n# 1st run finished\n");

        var firstPassEffectiveCost = settings.Creditor.OngoingCost;

        var firstPassDuration = planRunOnceTimeElapsed - planBuildingTimeElapsed;

        this._logger.LogDebug("Result from primary connector execution of Plan used for multi-connector evaluation with duration {0} and cost {1}:\n {2}\n", firstPassDuration, firstPassEffectiveCost, firstResult);

        // We disable prompt sampling to ensure no other tests are generated
        settings.EnablePromptSampling = false;

        // Create a task completion source to signal the completion of the optimization

        TaskCompletionSource<SuggestionCompletedEventArgs> suggestionCompletedTaskSource = new();

        // Subscribe to the OptimizationCompleted event
        settings.AnalysisSettings.SuggestionCompleted += (sender, args) =>
        {
            // Signal the completion of the optimization
            suggestionCompletedTaskSource.SetResult(args);

            suggestionCompletedTaskSource = new();
        };

        // Subscribe to the OptimizationCompleted event
        settings.AnalysisSettings.AnalysisTaskCrashed += (sender, args) =>
        {
            // Signal the completion of the optimization
            suggestionCompletedTaskSource.SetException(args.CrashEvent.Exception);
        };

        this._logger.LogTrace("\n# Releasing analysis task, waiting for suggestion completed event\n");

        settings.AnalysisSettings.AnalysisAwaitsManualTrigger = false;
        settings.AnalysisSettings.ReleaseAnalysisTasks();

        // Get the optimization results
        var optimizationResults = await suggestionCompletedTaskSource.Task.ConfigureAwait(false);

        var optimizationDoneElapsed = sw.Elapsed;

        settings.AnalysisSettings.EnableAnalysis = false;

        this._logger.LogTrace("\n# Optimization task finished\n");

        this._logger.LogDebug("Optimized with suggested settings: {0}\n", Json.Serialize(optimizationResults.SuggestedSettings));

        //Re execute plan with suggested settings

        this._logger.LogTrace("\n# Preparing plan for second run\n");

        settings.Creditor!.Reset();

        ctx = kernel.CreateNewContext();

        plan = Plan.FromJson(planJson, ctx, true);

        this._logger.LogTrace("\n# 2nd run of plan with updated settings and variable completions\n");

        var secondResult = await kernel.RunAsync(ctx.Variables, this._cleanupToken.Token, plan).ConfigureAwait(false);

        var planRunTwiceElapsed = sw.Elapsed;
        this._logger.LogTrace("\n# 2nd run finished\n");

        var secondPassEffectiveCost = settings.Creditor.OngoingCost;

        var secondPassDuration = planRunTwiceElapsed - optimizationDoneElapsed;

        this._logger.LogDebug("Result from vetted connector execution of Plan used for multi-connector evaluation with duration {0} and cost {1}:\n {2}\n", secondPassDuration, secondPassEffectiveCost, secondResult);

        // We validate the new connector with a new plan with distinct data

        settings.Creditor!.Reset();

        ctx = kernel.CreateNewContext();

        this._logger.LogTrace("\n# Loading validation plan from factory\n");

        plan = await planFactory(kernel, this._cleanupToken.Token, true);

        // 
        settings.EnablePromptSampling = true;
        settings.MaxInstanceNb = 2;

        TaskCompletionSource<SamplesReceivedEventArgs> samplesReceivedTaskSource = new();

        // Subscribe to the OptimizationCompleted event
        settings.AnalysisSettings.SamplesReceived += (sender, args) =>
        {
            // Signal the completion of the optimization
            samplesReceivedTaskSource.SetResult(args);

            samplesReceivedTaskSource = new();
        };

        this._logger.LogTrace("\n# 3rd run: New validation plan with updated settings and variable completions\n");

        var validationResult = await kernel.RunAsync(ctx.Variables, this._cleanupToken.Token, plan).ConfigureAwait(false);

        var planRunThriceElapsed = sw.Elapsed;
        this._logger.LogTrace("\n# 3rd run finished\n");

        var thirdPassEffectiveCost = settings.Creditor.OngoingCost;

        var sampleReceived = await samplesReceivedTaskSource.Task.ConfigureAwait(false);

        this._logger.LogTrace("\n# Start final validation from samples received from 3rd run validating manually with primary connector\n");

        var validationTests = sampleReceived.NewSamples;

        var evaluations = new List<ConnectorPromptEvaluation>();

        foreach (ConnectorTest validationTest in validationTests)
        {
            var evaluation = await settings.AnalysisSettings.EvaluateConnectorTestAsync(validationTest, sampleReceived.AnalysisJob).ConfigureAwait(false);
            if (evaluation == null)
            {
                throw new SKException("Validation of MultiCompletion failed to complete");
            }

            evaluations.Add(evaluation);
        }

        this._logger.LogTrace("\n# End validation, starting Asserts\n");

        // Assert

        this._logger.LogTrace("\n# Assertions \n");

        this._logger.LogTrace("Asserting secondary connectors reduced the original plan cost");

        Assert.True(firstPassEffectiveCost > secondPassEffectiveCost);

        this._logger.LogTrace("Asserting secondary connectors plan capabilities are vetted on a distinct validation input");

        foreach (ConnectorPromptEvaluation evaluation in evaluations)
        {
            Assert.True(evaluation.IsVetted);
        }
    }

    /// <summary>
    /// Configures a kernel with MultiTextCompletion comprising a primary OpenAI connector with parameters defined in main settings for OpenAI integration tests, and Oobabooga secondary connectors with parameters defined in the MultiConnector part of the settings file.
    /// </summary>
    private IKernel? InitializeKernel(MultiTextCompletionSettings multiTextCompletionSettings, List<string>? modelNames, MultiConnectorConfiguration multiConnectorConfiguration, CancellationToken? cancellationToken = null)
    {
        cancellationToken ??= CancellationToken.None;

        var openAIConfiguration = this._configuration.GetSection("OpenAI").Get<OpenAIConfiguration>();
        Assert.NotNull(openAIConfiguration);

        ITextCompletion openAiConnector;

        string testOrChatModelId;
        if (openAIConfiguration.ChatModelId != null)
        {
            testOrChatModelId = openAIConfiguration.ChatModelId;
            openAiConnector = new OpenAIChatCompletion(testOrChatModelId, openAIConfiguration.ApiKey, logger: this._logger);
        }
        else
        {
            testOrChatModelId = openAIConfiguration.ModelId;
            openAiConnector = new OpenAITextCompletion(testOrChatModelId, openAIConfiguration.ApiKey, logger: this._logger);
        }

        var openAiNamedCompletion = new NamedTextCompletion(testOrChatModelId, openAiConnector)
        {
            MaxTokens = 4096,
            CostPer1000Token = 0.0015m,
            TokenCountFunc = this._gp3TokenCounter
        };

        var oobaboogaCompletions = new List<NamedTextCompletion>();

        foreach (var oobaboogaConnector in multiConnectorConfiguration.OobaboogaCompletions)
        {
            if (modelNames != null && !modelNames.Contains(oobaboogaConnector.Name))
            {
                continue;
            }

            var oobaboogaCompletion = new OobaboogaTextCompletion(
                endpoint: new Uri(oobaboogaConnector.EndPoint ?? multiConnectorConfiguration.OobaboogaEndPoint),
                blockingPort: oobaboogaConnector.BlockingPort,
                streamingPort: oobaboogaConnector.StreamingPort,
                webSocketFactory: this._webSocketFactory,
                logger: this._logger);

            Func<string, int> tokeCountFunction;
            switch (oobaboogaConnector.TokenCountFunction)
            {
                case TokenCountFunction.Gpt3Tokenizer:
                    tokeCountFunction = this._gp3TokenCounter;
                    break;
                case TokenCountFunction.WordCount:
                    tokeCountFunction = this._wordCounter;
                    break;
                default:
                    throw new InvalidOperationException("token count function not supported");
            }

            var oobaboogaNamedCompletion = new NamedTextCompletion(oobaboogaConnector.Name, oobaboogaCompletion)
            {
                CostPerRequest = oobaboogaConnector.CostPerRequest,
                CostPer1000Token = oobaboogaConnector.CostPer1000Token,
                TokenCountFunc = tokeCountFunction,
                TemperatureTransform = d => d == 0 ? 0.01 : d,
                PromptTransform = oobaboogaConnector.PromptTransform
                //RequestSettingsTransform = requestSettings =>
                //{
                //    var newRequestSettings = new CompleteRequestSettings()
                //    {
                //        MaxTokens = requestSettings.MaxTokens,
                //        ResultsPerPrompt = requestSettings.ResultsPerPrompt,
                //        ChatSystemPrompt = requestSettings.ChatSystemPrompt,
                //        FrequencyPenalty = requestSettings.FrequencyPenalty,
                //        PresencePenalty = 0.3,
                //        StopSequences = requestSettings.StopSequences,
                //        Temperature = 0.7,
                //        TokenSelectionBiases = requestSettings.TokenSelectionBiases,
                //        TopP = 0.9,
                //    };
                //    return newRequestSettings;
                //}
            };
            oobaboogaCompletions.Add(oobaboogaNamedCompletion);
        }

        if (oobaboogaCompletions.Count == 0)
        {
            this._logger.LogWarning("No Secondary connectors matching test configuration found, aborting test");
            return null;
        }

        var builder = Kernel.Builder
            .WithLogger(this._logger);
        //.WithMemoryStorage(new VolatileMemoryStore());

        builder.WithMultiConnectorCompletionService(
            serviceId: null,
            settings: multiTextCompletionSettings,
            mainTextCompletion: openAiNamedCompletion,
            setAsDefault: true,
            analysisTaskCancellationToken: cancellationToken,
            otherCompletions: oobaboogaCompletions.ToArray());

        var kernel = builder.Build();

        return kernel;
    }

    public void Dispose()
    {
        foreach (ClientWebSocket clientWebSocket in this._webSockets)
        {
            clientWebSocket.Dispose();
        }

        this._cleanupToken.Cancel();
        this._cleanupToken.Dispose();

        this._testOutputHelper.Dispose();
    }
}
