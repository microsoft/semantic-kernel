// Copyright (c) Microsoft. All rights reserved.
using System;
using System.Collections.Generic;
using System.Text.Json;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Process.Models;
using Xunit;

namespace Microsoft.SemanticKernel.Process.UnitTests;

/// <summary>
/// Unit testing of <see cref="Microsoft.SemanticKernel.Process.Models"/>
/// and associated operations.
/// </summary>
public class KernelProcessSerializationTests
{
    private static readonly JsonSerializerOptions s_serializerOptions = new() { WriteIndented = true };

    /// <summary>
    /// Verify serialization of process with step.
    /// </summary>
    [Fact]
    public void KernelProcessSerialization()
    {
        // Arrange
        ProcessBuilder processBuilder = new(nameof(KernelProcessSerialization));
        processBuilder.AddStepFromType<SimpleStep>("SimpleStep");
        processBuilder.AddStepFromType<StatefulStep, StepState>(new StepState { Id = Guid.NewGuid() }, "StatefulStep");
        KernelProcess process = processBuilder.Build();

        // Act
        KernelProcessStateMetadata processState = process.ToProcessStateMetadata();

        // Assert
        AssertProcessState(process, processState);

        // Act
        string json = JsonSerializer.Serialize(processState, s_serializerOptions);
        KernelProcessStateMetadata? copyState = JsonSerializer.Deserialize<KernelProcessStateMetadata>(json);

        // Assert
        Assert.NotNull(copyState);
        AssertProcessState(process, copyState);

        // Arrange
        ProcessBuilder anotherBuilder = new(nameof(KernelProcessSerialization));
        anotherBuilder.AddStepFromType<SimpleStep>("SimpleStep");
        anotherBuilder.AddStepFromType<StatefulStep>("StatefulStep");
        KernelProcess another = anotherBuilder.Build();

        AssertProcess(process, another);
    }

    /// <summary>
    /// Verify serialization of process with subprocess.
    /// </summary>
    [Fact]
    public void KernelSubProcessSerialization()
    {
        // Arrange
        ProcessBuilder processBuilder = new(nameof(KernelProcessSerialization));
        ProcessBuilder subProcessBuilder = new("subprocess");
        subProcessBuilder.AddStepFromType<SimpleStep>("SimpleStep");
        subProcessBuilder.AddStepFromType<StatefulStep, StepState>(new StepState { Id = Guid.NewGuid() }, "StatefulStep");
        processBuilder.AddStepFromProcess(subProcessBuilder);
        KernelProcess process = processBuilder.Build();

        // Act
        KernelProcessStateMetadata processState = process.ToProcessStateMetadata();

        // Assert
        AssertProcessState(process, processState);

        // Act
        string json = JsonSerializer.Serialize(processState, s_serializerOptions);
        KernelProcessStateMetadata? copyState = JsonSerializer.Deserialize<KernelProcessStateMetadata>(json);

        // Assert
        Assert.NotNull(copyState);
        AssertProcessState(process, copyState);

        // Arrange
        ProcessBuilder anotherBuilder = new(nameof(KernelProcessSerialization));
        ProcessBuilder anotherSubBuilder = new("subprocess");
        anotherSubBuilder.AddStepFromType<SimpleStep>("SimpleStep");
        anotherSubBuilder.AddStepFromType<StatefulStep>("StatefulStep");
        anotherBuilder.AddStepFromProcess(anotherSubBuilder);
        KernelProcess another = anotherBuilder.Build();

        AssertProcess(process, another);
    }

    /// <summary>
    /// Verify serialization of process with map-step.
    /// </summary>
    [Fact]
    public void KernelProcessMapSerialization()
    {
        ProcessBuilder processBuilder = new(nameof(KernelProcessSerialization));
        processBuilder.AddMapStepFromType<StatefulStep, StepState>(new StepState { Id = Guid.NewGuid() }, "StatefulStep");
        KernelProcess process = processBuilder.Build();

        // Act
        KernelProcessStateMetadata processState = process.ToProcessStateMetadata();

        // Assert
        AssertProcessState(process, processState);

        // Act
        string json = JsonSerializer.Serialize(processState, s_serializerOptions);
        KernelProcessStateMetadata? copyState = JsonSerializer.Deserialize<KernelProcessStateMetadata>(json);

        // Assert
        Assert.NotNull(copyState);
        AssertProcessState(process, copyState);

        // Arrange
        ProcessBuilder anotherBuilder = new(nameof(KernelProcessSerialization));
        anotherBuilder.AddMapStepFromType<StatefulStep>("StatefulStep");
        KernelProcess another = anotherBuilder.Build();

        AssertProcess(process, another);
    }

    private static void AssertProcess(KernelProcess expectedProcess, KernelProcess anotherProcess)
    {
        Assert.Equal(expectedProcess.State.StepId, anotherProcess.State.StepId);
        Assert.Equal(expectedProcess.State.Version, anotherProcess.State.Version);
        Assert.Equal(expectedProcess.Steps.Count, anotherProcess.Steps.Count);

        for (int index = 0; index < expectedProcess.Steps.Count; ++index)
        {
            AssertStep(expectedProcess.Steps[index], anotherProcess.Steps[index]);
        }
    }

    private static void AssertStep(KernelProcessStepInfo expectedStep, KernelProcessStepInfo actualStep)
    {
        Assert.Equal(expectedStep.InnerStepType, actualStep.InnerStepType);
        Assert.Equal(expectedStep.State.StepId, actualStep.State.StepId);
        Assert.Equal(expectedStep.State.Version, actualStep.State.Version);

        if (expectedStep is KernelProcessMap mapStep)
        {
            Assert.IsType<KernelProcessMap>(actualStep);
            AssertStep(mapStep.Operation, ((KernelProcessMap)actualStep).Operation);
        }
        else if (expectedStep is KernelProcess subProcess)
        {
            Assert.IsType<KernelProcess>(actualStep);
            AssertProcess(subProcess, (KernelProcess)actualStep);
        }
        else if (expectedStep.State is KernelProcessStepState<StepState> stepState)
        {
            Assert.IsType<KernelProcessStepState<StepState>>(actualStep.State);
            KernelProcessStepState<StepState> actualState = (KernelProcessStepState<StepState>)actualStep.State;
            Assert.NotNull(stepState.State);
            Assert.NotNull(actualState.State);
            //Assert.Equal(stepState.State.Id, actualState.State.Id);
        }
    }

    private static void AssertProcessState(KernelProcess process, KernelProcessStateMetadata? savedProcess)
    {
        Assert.NotNull(savedProcess);
        Assert.Equal(process.State.RunId, savedProcess.Id);
        Assert.Equal(process.State.StepId, savedProcess.Name);
        Assert.Equal(process.State.Version, savedProcess.VersionInfo);
        Assert.NotNull(savedProcess.StepsState);
        Assert.Equal(process.Steps.Count, savedProcess.StepsState.Count);

        foreach (KernelProcessStepInfo step in process.Steps)
        {
            AssertStepState(step, savedProcess.StepsState);
        }
    }

    private static void AssertStepState(KernelProcessStepInfo step, Dictionary<string, KernelProcessStepStateMetadata> savedSteps)
    {
        Assert.True(savedSteps.ContainsKey(step.State.StepId));
        KernelProcessStepStateMetadata savedStep = savedSteps[step.State.StepId];
        Assert.Equal(step.State.RunId, savedStep.Id);
        Assert.Equal(step.State.StepId, savedStep.Name);
        Assert.Equal(step.State.Version, savedStep.VersionInfo);

        if (step is KernelProcessMap mapStep)
        {
            Assert.IsType<KernelProcessMapStateMetadata>(savedStep);
            KernelProcessMapStateMetadata mapState = (KernelProcessMapStateMetadata)savedStep;
            Assert.NotNull(mapState.OperationState);
            Assert.NotNull(mapState.OperationState.Name);
            AssertStepState(mapStep.Operation, new() { { mapState.OperationState.Name, mapState.OperationState } });
        }
        else if (step is KernelProcess subProcess)
        {
            Assert.IsType<KernelProcessStateMetadata>(savedStep);
            AssertProcessState(subProcess, (KernelProcessStateMetadata)savedStep);
        }
        else if (step.State is KernelProcessStepState<StepState> stepState)
        {
            Assert.NotNull(savedStep.State);
            if (savedStep.State is JsonElement jsonState)
            {
                StepState? savedState = jsonState.Deserialize<StepState>();
                Assert.NotNull(savedState);
                Assert.NotNull(stepState.State);
                Assert.Equal(stepState.State.Id, savedState.Id);
            }
            else
            {
                Assert.Equal(stepState.State, (StepState)savedStep.State);
            }
        }
    }

    private sealed class SimpleStep : KernelProcessStep
    {
        [KernelFunction]
        public void RunSimple()
        {
        }
    }

    private sealed class StepState
    {
        public Guid Id { get; set; } = Guid.Empty;
    }

    private sealed class StatefulStep : KernelProcessStep<StepState>
    {
        private StepState? _state;

        public override ValueTask ActivateAsync(KernelProcessStepState<StepState> state)
        {
            this._state = state.State;
            return default;
        }

        [KernelFunction]
        public void RunStateful()
        {
        }
    }
}
