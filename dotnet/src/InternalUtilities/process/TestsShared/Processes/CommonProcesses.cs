// Copyright (c) Microsoft. All rights reserved.
using System.Collections.Generic;
using Microsoft.SemanticKernel;

namespace SemanticKernel.Process.TestsShared.Steps;

#pragma warning disable CS1591 // Missing XML comment for publicly visible type or member

/// <summary>
/// Collection of common steps used by UnitTests and IntegrationUnitTests
/// </summary>
public static class CommonProcesses
{
    public static class ProcessEvents
    {
        /// <summary>
        /// Start Process Event
        /// </summary>
        public const string StartProcess = nameof(StartProcess);
    }

    public static class ProcessKeys
    {
        public const string CounterProcess = nameof(CounterProcess);
        public const string CounterWithEvenNumberDetectionProcess = nameof(CounterWithEvenNumberDetectionProcess);
    }

    public static KernelProcess GetCounterProcess(string processName = "counterProcess")
    {
        ProcessBuilder process = new(processName);

        var counterStep = process.AddStepFromType<CommonSteps.CountStep>(id: "counterStep");
        var echoStep = process.AddStepFromType<CommonSteps.EchoStep>(id: nameof(CommonSteps.EchoStep));

        process
            .OnInputEvent(ProcessEvents.StartProcess)
            .SendEventTo(new(counterStep));

        counterStep
            .OnFunctionResult()
            .SendEventTo(new(echoStep));

        return process.Build();
    }

    public static KernelProcess GetCounterWithEventDetectionProcess(string processName = "counterWithEventDetectionProcess")
    {
        ProcessBuilder process = new(processName);

        var counterStep = process.AddStepFromType<CommonSteps.CountStep>(id: "counterStep");
        var evenNumberStep = process.AddStepFromType<CommonSteps.EvenNumberDetectorStep>(id: nameof(CommonSteps.EvenNumberDetectorStep));
        var echoStep = process.AddStepFromType<CommonSteps.EchoStep>(id: nameof(CommonSteps.EchoStep));

        process
            .OnInputEvent(ProcessEvents.StartProcess)
            .SendEventTo(new(counterStep));

        counterStep
            .OnFunctionResult()
            .SendEventTo(new(evenNumberStep));

        evenNumberStep
            .OnEvent(CommonSteps.EvenNumberDetectorStep.OutputEvents.EvenNumber)
            .SendEventTo(new(echoStep));

        return process.Build();
    }

    public static IReadOnlyDictionary<string, KernelProcess> GetCommonProcessesKeyedDictionary()
    {
        return new Dictionary<string, KernelProcess>() {
            { ProcessKeys.CounterProcess, GetCounterProcess() },
            { ProcessKeys.CounterWithEvenNumberDetectionProcess, GetCounterWithEventDetectionProcess() },
        };
    }
}
