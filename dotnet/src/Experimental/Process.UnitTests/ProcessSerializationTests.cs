// Copyright (c) Microsoft. All rights reserved.

using System;
using System.IO;
using System.Linq;
using System.Reflection;
using System.Runtime.Serialization;
using System.Threading.Tasks;
using Xunit;

namespace Microsoft.SemanticKernel.Process.UnitTests;

/// <summary>
/// Unit testing of <see cref="KernelProcessState"/>.
/// </summary>
public class ProcessSerializationTests
{
    /// <summary>
    /// Verify initialization of <see cref="KernelProcessState"/>.
    /// </summary>
    [Fact(Skip = "More work left to do.")]
    public async Task KernelProcessFromYamlWorksAsync()
    {
        // Arrange
        var yaml = this.ReadResource("workflow1.yaml");

        // Act
        var process = await ProcessBuilder.LoadFromYamlAsync(yaml);

        // Assert
        Assert.NotNull(process);
    }

    /// <summary>
    /// Verify initialization of <see cref="KernelProcessState"/> from a YAML file that contains only a .NET workflow.
    /// </summary>
    /// <returns></returns>
    [Fact]
    public async Task KernelProcessFromDotnetOnlyWorkflow1YamlAsync()
    {
        // Arrange
        var yaml = this.ReadResource("dotnetOnlyWorkflow1.yaml");

        // Act
        var process = await ProcessBuilder.LoadFromYamlAsync(yaml);

        // Assert
        Assert.NotNull(process);

        var stepKickoff = process.Steps.FirstOrDefault(s => s.State.Id == "kickoff_agent");
        var stepA = process.Steps.FirstOrDefault(s => s.State.Id == "a_step_agent");
        var stepB = process.Steps.FirstOrDefault(s => s.State.Id == "b_step_agent");
        var stepC = process.Steps.FirstOrDefault(s => s.State.Id == "c_step_agent");

        Assert.NotNull(stepKickoff);
        Assert.NotNull(stepA);
        Assert.NotNull(stepB);
        Assert.NotNull(stepC);

        // kickoff step has outgoing edge to aStep and bStep on event startAStep
        Assert.Single(stepKickoff.Edges);
        var kickoffStartEdges = stepKickoff.Edges["kickoff_agent.StartARequested"];
        Assert.Equal(2, kickoffStartEdges.Count);
        Assert.Contains(kickoffStartEdges, e => e.OutputTarget.StepId == "a_step_agent");
        Assert.Contains(kickoffStartEdges, e => e.OutputTarget.StepId == "b_step_agent");

        // aStep and bStep have grouped outgoing edges to cStep on event aStepDone and bStepDone
        Assert.Single(stepA.Edges);
        var aStepDoneEdges = stepA.Edges["a_step_agent.AStepDone"];
        Assert.Single(aStepDoneEdges);
        var aStepDoneEdge = aStepDoneEdges.First();
        Assert.Equal("c_step_agent", aStepDoneEdge.OutputTarget.StepId);
        Assert.NotEmpty(aStepDoneEdge.GroupId ?? "");

        Assert.Single(stepB.Edges);
        var bStepDoneEdges = stepB.Edges["b_step_agent.BStepDone"];
        Assert.Single(bStepDoneEdges);
        var bStepDoneEdge = bStepDoneEdges.First();
        Assert.Equal("c_step_agent", bStepDoneEdge.OutputTarget.StepId);
        Assert.NotEmpty(bStepDoneEdge.GroupId ?? "");

        Assert.Single(stepC.Edges);
        var cStepDoneEdges = stepC.Edges["c_step_agent.CStepDone"];
        Assert.Single(cStepDoneEdges);
        var cStepDoneEdge = cStepDoneEdges.First();
        Assert.Equal("kickoff_agent", cStepDoneEdge.OutputTarget.StepId);
        Assert.Null(cStepDoneEdge.GroupId);

        // edges to cStep are in the same group
        Assert.Equal(aStepDoneEdge.GroupId, bStepDoneEdge.GroupId);
    }

    /// <summary>
    /// Verify that the process can be serialized to YAML and deserialized back to a workflow.
    /// </summary>
    /// <returns></returns>
    [Fact]
    public async Task ProcessToWorkflowWorksAsync()
    {
        var process = this.GetProcess();
        var workflow = await WorkflowBuilder.BuildWorkflow(process);
        string yaml = WorkflowSerializer.SerializeToYaml(workflow);

        Assert.NotNull(workflow);
    }

    private KernelProcess GetProcess()
    {
        // Create the process builder.
        ProcessBuilder processBuilder = new("ProcessWithDapr");

        // Add some steps to the process.
        var kickoffStep = processBuilder.AddStepFromType<KickoffStep>();
        var myAStep = processBuilder.AddStepFromType<AStep>();
        var myBStep = processBuilder.AddStepFromType<BStep>();

        // ########## Configuring initial state on steps in a process ###########
        // For demonstration purposes, we add the CStep and configure its initial state with a CurrentCycle of 1.
        // Initializing state in a step can be useful for when you need a step to start out with a predetermines
        // configuration that is not easily accomplished with dependency injection.
        var myCStep = processBuilder.AddStepFromType<CStep, CStepState>(initialState: new() { CurrentCycle = 1 });

        // Setup the input event that can trigger the process to run and specify which step and function it should be routed to.
        processBuilder
            .OnInputEvent(CommonEvents.StartProcess)
            .SendEventTo(new ProcessFunctionTargetBuilder(kickoffStep));

        // When the kickoff step is finished, trigger both AStep and BStep.
        kickoffStep
            .OnEvent(CommonEvents.StartARequested)
            .SendEventTo(new ProcessFunctionTargetBuilder(myAStep))
            .SendEventTo(new ProcessFunctionTargetBuilder(myBStep));

        //// When AStep finishes, send its output to CStep.
        //myAStep
        //    .OnEvent(CommonEvents.AStepDone)
        //    .SendEventTo(new ProcessFunctionTargetBuilder(myCStep, parameterName: "astepdata"));

        //// When BStep finishes, send its output to CStep also.
        //myBStep
        //    .OnEvent(CommonEvents.BStepDone)
        //    .SendEventTo(new ProcessFunctionTargetBuilder(myCStep, parameterName: "bstepdata"));

        processBuilder
            .ListenFor()
                .AllOf(new()
                {
                    new(messageType: CommonEvents.AStepDone, source: myAStep),
                    new(messageType: CommonEvents.BStepDone, source: myBStep)
                })
                .SendEventTo(new ProcessStepTargetBuilder(myCStep, inputMapping: (inputEvents) =>
                {
                    // Map the input events to the CStep's input parameters.
                    // In this case, we are mapping the output of AStep to the first input parameter of CStep
                    // and the output of BStep to the second input parameter of CStep.
                    return new()
                    {
                        { "astepdata", inputEvents[$"aStep.{CommonEvents.AStepDone}"] },
                        { "bstepdata", inputEvents[$"bStep.{CommonEvents.BStepDone}"] }
                    };
                }));

        // When CStep has finished without requesting an exit, activate the Kickoff step to start again.
        myCStep
            .OnEvent(CommonEvents.CStepDone)
            .SendEventTo(new ProcessFunctionTargetBuilder(kickoffStep));

        // When the CStep has finished by requesting an exit, stop the process.
        myCStep
            .OnEvent(CommonEvents.ExitRequested)
            .StopProcess();

        var process = processBuilder.Build();
        return process;
    }

    private string ReadResource(string name)
    {
        // Get the current assembly
        Assembly assembly = Assembly.GetExecutingAssembly();

        // Specify the resource name
        string resourceName = $"SemanticKernel.Process.UnitTests.Resources.{name}";

        // Get the resource stream
        using (Stream? resourceStream = assembly.GetManifestResourceStream(resourceName))
        {
            if (resourceStream != null)
            {
                using (StreamReader reader = new(resourceStream))
                {
                    string content = reader.ReadToEnd();
                    return content;
                }
            }
            else
            {
                throw new InvalidOperationException($"Resource {resourceName} not found in assembly {assembly.FullName}");
            }
        }
    }

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
            Console.WriteLine("##### Kickoff ran.");
            await context.EmitEventAsync(new() { Id = CommonEvents.StartARequested, Data = "Get Going" });
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
            Console.WriteLine("##### AStep ran.");
            await Task.Delay(TimeSpan.FromSeconds(1));
            await context.EmitEventAsync(CommonEvents.AStepDone, "I did A");
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
            Console.WriteLine("##### BStep ran.");
            await Task.Delay(TimeSpan.FromSeconds(2));
            await context.EmitEventAsync(new() { Id = CommonEvents.BStepDone, Data = "I did B" });
        }
    }

    /// <summary>
    /// A stateful step in the process. This step uses <see cref="CStepState"/> as the persisted
    /// state object and overrides the ActivateAsync method to initialize the state when activated.
    /// </summary>
    private sealed class CStep : KernelProcessStep<CStepState>
    {
        private CStepState? _state;

        // ################ Using persisted state #################
        // CStep has state that we want to be persisted in the process. To ensure that the step always
        // starts with the previously persisted or configured state, we need to override the ActivateAsync
        // method and use the state object it provides.
        public override ValueTask ActivateAsync(KernelProcessStepState<CStepState> state)
        {
            this._state = state.State!;
            Console.WriteLine($"##### CStep activated with Cycle = '{state.State?.CurrentCycle}'.");
            return base.ActivateAsync(state);
        }

        [KernelFunction]
        public async ValueTask DoItAsync(KernelProcessStepContext context, string astepdata, string bstepdata)
        {
            // ########### This method will restart the process in a loop until CurrentCycle >= 3 ###########
            this._state!.CurrentCycle++;
            if (this._state.CurrentCycle >= 3)
            {
                // Exit the processes
                Console.WriteLine("##### CStep run cycle 3 - exiting.");
                await context.EmitEventAsync(new() { Id = CommonEvents.ExitRequested });
                return;
            }

            // Cycle back to the start
            Console.WriteLine($"##### CStep run cycle {this._state.CurrentCycle}.");
            await context.EmitEventAsync(new() { Id = CommonEvents.CStepDone });
        }
    }

    /// <summary>
    /// A state object for the CStep.
    /// </summary>
    [DataContract]
    private sealed record CStepState
    {
        [DataMember]
        public int CurrentCycle { get; set; }
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
