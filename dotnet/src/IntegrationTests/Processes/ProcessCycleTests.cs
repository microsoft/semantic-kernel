// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;
using System.Threading.Tasks;
using System;
using Microsoft.Extensions.Configuration;
using SemanticKernel.IntegrationTests.TestSettings;
using Xunit;
using SemanticKernel.IntegrationTests.Agents;

namespace SemanticKernel.IntegrationTests.Processes;

public sealed class ProcessCycleTests
{
    private readonly IKernelBuilder _kernelBuilder = Kernel.CreateBuilder();
    private readonly IConfigurationRoot _configuration = new ConfigurationBuilder()
            .AddJsonFile(path: "testsettings.json", optional: true, reloadOnChange: true)
            .AddJsonFile(path: "testsettings.development.json", optional: true, reloadOnChange: true)
            .AddEnvironmentVariables()
            .AddUserSecrets<OpenAIAssistantAgentTests>()
            .Build();

    /// <summary>
    /// Tests a process which cycles a fixed number of times and then exits.
    /// </summary>
    /// <returns>A <see cref="Task"/></returns>
    [Fact]
    public async Task TestCycleAndExitWithFanInAsync()
    {
        // Arrange
        OpenAIConfiguration configuration = this._configuration.GetSection("OpenAI").Get<OpenAIConfiguration>()!;
        this._kernelBuilder.AddOpenAIChatCompletion(
            modelId: configuration.ModelId!,
            apiKey: configuration.ApiKey);

        Kernel kernel = this._kernelBuilder.Build();

        ProcessBuilder process = new("Test Process");

        var kickoffStep = process.AddStepFromType<KickoffStep>();
        var myAStep = process.AddStepFromType<AStep>();
        var myBStep = process.AddStepFromType<BStep>();
        var myCStep = process.AddStepFromType<CStep>();

        process
            .OnInputEvent(CommonEvents.StartProcess)
            .SendEventTo(new ProcessFunctionTargetBuilder(kickoffStep));

        kickoffStep
            .OnEvent(CommonEvents.StartARequested)
            .SendEventTo(new ProcessFunctionTargetBuilder(myAStep));

        kickoffStep
            .OnEvent(CommonEvents.StartBRequested)
            .SendEventTo(new ProcessFunctionTargetBuilder(myBStep));

        myAStep
            .OnEvent(CommonEvents.AStepDone)
            .SendEventTo(new ProcessFunctionTargetBuilder(myCStep, parameterName: "astepdata"));

        myBStep
            .OnEvent(CommonEvents.BStepDone)
            .SendEventTo(new ProcessFunctionTargetBuilder(myCStep, parameterName: "bstepdata"));

        myCStep
            .OnEvent(CommonEvents.CStepDone)
            .SendEventTo(new ProcessFunctionTargetBuilder(kickoffStep));

        myCStep
            .OnEvent(CommonEvents.ExitRequested)
            .StopProcess();

        KernelProcess kernelProcess = process.Build();

        Console.WriteLine("starting");
        await kernelProcess.StartAsync(kernel, new KernelProcessEvent() { Id = CommonEvents.StartProcess, Data = "foo" });
        Console.WriteLine("finished");
    }

#pragma warning disable CA1812 // Avoid uninstantiated internal classes
    // These classes are dynamically instantiated by the processes used in tests.

    /// <summary>
    /// Kick off step for the process.
    /// </summary>
    private sealed class KickoffStep : KernelProcessStep
    {
        public static class Functions
        {
            public const string KickOff = nameof(KickOff);
        }

        [KernelFunction(Functions.KickOff)]
        public async ValueTask PrintWelcomeMessageAsync(KernelProcessStepContext context)
        {
            await context.EmitEventAsync(new() { Id = CommonEvents.StartARequested, Data = "Get Going A" });
            await context.EmitEventAsync(new() { Id = CommonEvents.StartBRequested, Data = "Get Going B" });
        }
    }

    /// <summary>
    /// A step in the process.
    /// </summary>
    private sealed class AStep : KernelProcessStep
    {
        [KernelFunction]
        public async ValueTask DoItAsync(KernelProcessStepContext context)
        {
            await Task.Delay(TimeSpan.FromSeconds(1));
            await context.EmitEventAsync(new() { Id = CommonEvents.AStepDone });
        }
    }

    /// <summary>
    /// A step in the process.
    /// </summary>
    private sealed class BStep : KernelProcessStep
    {
        [KernelFunction]
        public async ValueTask DoItAsync(KernelProcessStepContext context)
        {
            await Task.Delay(TimeSpan.FromSeconds(2));
            await context.EmitEventAsync(new() { Id = CommonEvents.BStepDone });
        }
    }

    /// <summary>
    /// A step in the process.
    /// </summary>
    private sealed class CStep : KernelProcessStep
    {
        private int CurrentCycle { get; set; } = 0;

        public CStep()
        {
            this.CurrentCycle = 0;
        }

        [KernelFunction]
        public async ValueTask DoItAsync(KernelProcessStepContext context, string astepdata, string bstepdata)
        {
            this.CurrentCycle++;
            if (this.CurrentCycle == 3)
            {
                // Exit the processes
                await context.EmitEventAsync(new() { Id = CommonEvents.ExitRequested });
                return;
            }

            // Cycle back to the start
            await context.EmitEventAsync(new() { Id = CommonEvents.CStepDone });
        }
    }

    /// <summary>
    /// Common Events used in the process.
    /// </summary>
    private static class CommonEvents
    {
        public const string UserInputReceived = nameof(UserInputReceived);
        public const string CompletionResponseGenerated = nameof(CompletionResponseGenerated);
        public const string WelcomeDone = nameof(WelcomeDone);
        public const string AStepDone = nameof(AStepDone);
        public const string BStepDone = nameof(BStepDone);
        public const string CStepDone = nameof(CStepDone);
        public const string StartARequested = nameof(StartARequested);
        public const string StartBRequested = nameof(StartBRequested);
        public const string ExitRequested = nameof(ExitRequested);
        public const string StartProcess = nameof(StartProcess);
    }
#pragma warning restore CA1812 // Avoid uninstantiated internal classes
}
