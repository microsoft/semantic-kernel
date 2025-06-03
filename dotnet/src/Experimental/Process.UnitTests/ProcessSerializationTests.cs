// Copyright (c) Microsoft. All rights reserved.

using System;
using System.IO;
using System.Linq;
using System.Reflection;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Process.UnitTests.Steps;
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

        var stepKickoff = process.Steps.FirstOrDefault(s => s.State.Id == "kickoff");
        var stepA = process.Steps.FirstOrDefault(s => s.State.Id == "a_step");
        var stepB = process.Steps.FirstOrDefault(s => s.State.Id == "b_step");
        var stepC = process.Steps.FirstOrDefault(s => s.State.Id == "c_step");

        Assert.NotNull(stepKickoff);
        Assert.NotNull(stepA);
        Assert.NotNull(stepB);
        Assert.NotNull(stepC);

        // kickoff step has outgoing edge to aStep and bStep on event startAStep
        Assert.Single(stepKickoff.Edges);
        var kickoffStartEdges = stepKickoff.Edges["kickoff.StartARequested"];
        Assert.Equal(2, kickoffStartEdges.Count);
        Assert.Contains(kickoffStartEdges, e => (e.OutputTarget as KernelProcessFunctionTarget)!.StepId == "a_step");
        Assert.Contains(kickoffStartEdges, e => (e.OutputTarget as KernelProcessFunctionTarget)!.StepId == "b_step");

        // aStep and bStep have grouped outgoing edges to cStep on event aStepDone and bStepDone
        Assert.Single(stepA.Edges);
        var aStepDoneEdges = stepA.Edges["a_step.AStepDone"];
        Assert.Single(aStepDoneEdges);
        var aStepDoneEdge = aStepDoneEdges.First();
        Assert.Equal("c_step", (aStepDoneEdge.OutputTarget as KernelProcessFunctionTarget)!.StepId);
        Assert.NotEmpty(aStepDoneEdge.GroupId ?? "");

        Assert.Single(stepB.Edges);
        var bStepDoneEdges = stepB.Edges["b_step.BStepDone"];
        Assert.Single(bStepDoneEdges);
        var bStepDoneEdge = bStepDoneEdges.First();
        Assert.Equal("c_step", (bStepDoneEdge.OutputTarget as KernelProcessFunctionTarget)!.StepId);
        Assert.NotEmpty(bStepDoneEdge.GroupId ?? "");

        // cStep has outgoing edge to kickoff step on event cStepDone and one to end the process on event exitRequested
        Assert.Equal(2, stepC.Edges.Count);
        var cStepDoneEdges = stepC.Edges["c_step.CStepDone"];
        Assert.Single(cStepDoneEdges);
        var cStepDoneEdge = cStepDoneEdges.First();
        Assert.Equal("kickoff", (cStepDoneEdge.OutputTarget as KernelProcessFunctionTarget)!.StepId);
        Assert.Null(cStepDoneEdge.GroupId);

        var exitRequestedEdges = stepC.Edges["Microsoft.SemanticKernel.Process.EndStep"];
        Assert.Single(exitRequestedEdges);
        var exitRequestedEdge = exitRequestedEdges.First();
        Assert.Equal("Microsoft.SemanticKernel.Process.EndStep", (exitRequestedEdge.OutputTarget as KernelProcessFunctionTarget)!.StepId);

        // edges to cStep are in the same group
        Assert.Equal(aStepDoneEdge.GroupId, bStepDoneEdge.GroupId);
    }

    /// <summary>
    /// Verify initialization of <see cref="KernelProcessState"/> from a YAML file that contains foundry_agents
    /// </summary>
    /// <returns></returns>
    [Fact]
    public async Task KernelProcessFromScenario1YamlAsync()
    {
        // Arrange
        var yaml = this.ReadResource("scenario1.yaml");
        // Act
        var process = await ProcessBuilder.LoadFromYamlAsync(yaml);
        // Assert
        Assert.NotNull(process);
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

    /// <summary>
    /// Verify initialization of <see cref="KernelProcessState"/> from a YAML file that contains references to C# class and chat completion agent.
    /// </summary>
    [Fact]
    public async Task KernelProcessFromCombinedWorkflowYamlAsync()
    {
        // Arrange
        var yaml = this.ReadResource("combined-workflow.yaml");

        // Act
        var process = await ProcessBuilder.LoadFromYamlAsync(yaml);

        // Assert
        Assert.NotNull(process);
        Assert.Contains(process.Steps, step => step.State.Id == "GetProductInfo");
        Assert.Contains(process.Steps, step => step.State.Id == "Summarize");
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
        var myCStep = processBuilder.AddStepFromType<CStep, CStep.CStepState>(initialState: new() { CurrentCycle = 1 });

        // Setup the input event that can trigger the process to run and specify which step and function it should be routed to.
        processBuilder
            .OnInputEvent(CommonEvents.StartProcess)
            .SendEventTo(new ProcessFunctionTargetBuilder(kickoffStep));

        // When the kickoff step is finished, trigger both AStep and BStep.
        kickoffStep
            .OnEvent(CommonEvents.StartARequested)
            .SendEventTo(new ProcessFunctionTargetBuilder(myAStep))
            .SendEventTo(new ProcessFunctionTargetBuilder(myBStep));

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
}
