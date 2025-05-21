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
        public const string OtherEvent = nameof(OtherEvent);
    }

    public static class ProcessKeys
    {
        public const string CounterProcess = nameof(CounterProcess);
        public const string CounterWithEvenNumberDetectionProcess = nameof(CounterWithEvenNumberDetectionProcess);
        public const string NestedCounterWithEvenDetectionAndMergeProcess = nameof(NestedCounterWithEvenDetectionAndMergeProcess);
        public const string InternalNestedCounterWithEvenDetectionAndMergeProcess = nameof(InternalNestedCounterWithEvenDetectionAndMergeProcess);
        public const string DelayedMergeProcess = nameof(DelayedMergeProcess);
        public const string SimpleMergeProcess = nameof(SimpleMergeProcess);
    }

    public static KernelProcess GetCounterProcess(string processName = ProcessKeys.CounterProcess)
    {
        ProcessBuilder process = new(processName);

        var counterStep = process.AddStepFromType<CommonSteps.CountStep>(id: "counterStep");
        var echoStep = process.AddStepFromType<CommonSteps.EchoStep>(id: nameof(CommonSteps.EchoStep));

        process
            .OnInputEvent(ProcessEvents.StartProcess)
            .SendEventTo(new(counterStep));

        counterStep
            .OnFunctionResult()
            .SendEventTo(new ProcessFunctionTargetBuilder(echoStep));

        return process.Build();
    }

    public static ProcessBuilder GetCounterWithEvenDetectionProcess(string processName = ProcessKeys.CounterWithEvenNumberDetectionProcess)
    {
        ProcessBuilder process = new(processName);

        var counterStep = process.AddStepFromType<CommonSteps.SimpleCountStep>(id: "counterStep");
        var evenNumberStep = process.AddStepFromType<CommonSteps.EvenNumberDetectorStep>(id: nameof(CommonSteps.EvenNumberDetectorStep));

        process
            .OnInputEvent(ProcessEvents.StartProcess)
            .SendEventTo(new ProcessFunctionTargetBuilder(counterStep));

        counterStep
            .OnFunctionResult()
            .SendEventTo(new ProcessFunctionTargetBuilder(evenNumberStep));

        return process;
    }

    /// <summary>
    /// <code>
    ///                                                                                                     ┌───────┐
    ///                                                                                                     │       │
    ///                            ┌───────────────────────────────────────────────────────────────────────►│       │
    ///                            │                                                                        │       │
    ///                            │                                 EvenNumber Event                       │       │   ┌───────────┐
    ///                            │                     ┌─────────────────────────────────────────────────►│ merge ├──►│ finalEcho │
    ///                            │                     │                                                  │       │   └───────────┘
    ///                            │                     │   ┌─────────────────────────────────────┐        │       │
    ///                            │                     │   │ innerCounterProcess                 │    ┌──►│       │
    ///  Start       ┌───────────┐ │  ┌──────────────┐   │   │  ┌───────────┐    ┌──────────────┐  │    │   │       │
    /// Process ────►│   outer   ├─┴─►│    outer     ├───┴──►│  │  counter  ├───►│ evenDetector ├──┼────┘   └───────┘
    ///  Event       │  counter  │    │ evenDetector │       │  └───────────┘    └──────────────┘  │  EvenNumber
    ///              └───────────┘    └──────────────┘       └─────────────────────────────────────┘    Event
    ///</code>
    /// </summary>
    /// <param name="processName"></param>
    /// <returns></returns>
    public static ProcessBuilder GetNestedCounterWithEvenDetectionAndMergeProcess(string processName = ProcessKeys.NestedCounterWithEvenDetectionAndMergeProcess)
    {
        ProcessBuilder process = new(processName);

        var outerCounterStep = process.AddStepFromType<CommonSteps.SimpleCountStep>(id: "outerCounterStep");
        var outerEvenNumberStep = process.AddStepFromType<CommonSteps.EvenNumberDetectorStep>(id: $"outer{nameof(CommonSteps.EvenNumberDetectorStep)}");
        var innerCounterProcess = process.AddStepFromProcess(GetCounterWithEvenDetectionProcess("innerCounterProcess"));
        var mergeStep = process.AddStepFromType<CommonSteps.MergeStringsStep>(id: nameof(CommonSteps.MergeStringsStep));
        var finalEchoStep = process.AddStepFromType<CommonSteps.EchoStep>(id: nameof(CommonSteps.EchoStep));

        process
            .OnInputEvent(ProcessEvents.StartProcess)
            .SendEventTo(new ProcessFunctionTargetBuilder(outerCounterStep));

        outerCounterStep
            .OnFunctionResult()
            .SendEventTo(new ProcessFunctionTargetBuilder(outerEvenNumberStep));

        outerEvenNumberStep
            .OnEvent(CommonSteps.EvenNumberDetectorStep.OutputEvents.EvenNumber)
            .SendEventTo(innerCounterProcess.WhereInputEventIs(ProcessEvents.StartProcess));

        // merging inputs
        process
            .ListenFor()
            .AllOf([
                new(messageType: outerCounterStep.GetFunctionResultEventId(), outerCounterStep),
                new(messageType: CommonSteps.EvenNumberDetectorStep.OutputEvents.EvenNumber, outerEvenNumberStep),
                new(messageType: CommonSteps.EvenNumberDetectorStep.OutputEvents.EvenNumber, innerCounterProcess),
            ])
            .SendEventTo(new ProcessStepTargetBuilder(mergeStep, inputMapping: (inputEvents) =>
            {
                return new()
                {
                    { "str1", inputEvents[outerCounterStep.GetFullEventId()] },
                    { "str2", inputEvents[outerEvenNumberStep.GetFullEventId(CommonSteps.EvenNumberDetectorStep.OutputEvents.EvenNumber)] },
                    { "str3", inputEvents[innerCounterProcess.GetFullEventId(CommonSteps.EvenNumberDetectorStep.OutputEvents.EvenNumber)] },
                };
            }));

        mergeStep
            .OnFunctionResult()
            .SendEventTo(new ProcessFunctionTargetBuilder(finalEchoStep));

        return process;
    }

    /// <summary>
    /// Process that merges string from process onInput and nested AllOf triggered events from a nested process.
    /// <code>
    ///                                             ┌───────┐
    ///                                             │       │
    ///            ┌───────────────────────────────►│       │
    ///            │                                │       │
    ///            │                                │       │   ┌───────────┐
    ///            │                            ┌──►│ merge ├──►│ finalEcho │
    ///            │                            │   │       │   └───────────┘
    ///            │                            │   │       │
    ///            │  ┌───────────────┐         ├──►│       │
    ///  Start     │  │    Nested     │         │   │       │
    /// Process ───┴─►│    Counter    ├─────────┘   └───────┘
    ///  Event        │    Process    │  Echo
    ///               └───────────────┘  Event
    /// </code>
    /// </summary>
    /// <param name="processName"></param>
    /// <returns></returns>
    public static KernelProcess GetInternalNestedCounterWithEvenDetectionAndMergeProcess(string processName = ProcessKeys.InternalNestedCounterWithEvenDetectionAndMergeProcess)
    {
        ProcessBuilder process = new(processName);

        var internalNestedCounterProcess = process.AddStepFromProcess(GetNestedCounterWithEvenDetectionAndMergeProcess("internalNestedCounterProcess"));
        var mergeStep = process.AddStepFromType<CommonSteps.MergeStringsStep>(id: nameof(CommonSteps.MergeStringsStep));
        var finalEchoStep = process.AddStepFromType<CommonSteps.EchoStep>(id: nameof(CommonSteps.EchoStep));

        process
            .OnInputEvent(ProcessEvents.StartProcess)
            .SendEventTo(internalNestedCounterProcess.WhereInputEventIs(ProcessEvents.StartProcess));

        // merging inputs
        process.ListenFor()
            .AllOf([
                new(messageType: ProcessEvents.StartProcess, process),
                new(messageType: CommonSteps.EchoStep.OutputEvents.EchoMessage, internalNestedCounterProcess),
            ])
            .SendEventTo(new ProcessStepTargetBuilder(mergeStep, inputMapping: (inputEvents) =>
            {
                return new()
                {
                    { "str1", inputEvents[process.GetFullEventId(ProcessEvents.StartProcess)] },
                    { "str2", inputEvents[internalNestedCounterProcess.GetFullEventId(CommonSteps.EchoStep.OutputEvents.EchoMessage)] },
                    { "str3", inputEvents[internalNestedCounterProcess.GetFullEventId(CommonSteps.EchoStep.OutputEvents.EchoMessage)] },
                };
            }));

        mergeStep
            .OnFunctionResult()
            .SendEventTo(new ProcessFunctionTargetBuilder(finalEchoStep));

        return process.Build();
    }

    /// <summary>
    /// Process that merges string from process onInput events when they are all available.
    /// Helps test make use of ListenFor() and AllOf() methods with events from process.
    /// <code>
    /// Other ───┐   ┌───────┐
    ///          │   │       │
    ///          └──►│       │
    ///              │       │
    ///              │       │    ┌───────────┐
    ///    ┌────────►│ merge ├───►│ finalEcho │
    ///    │         │       │    └───────────┘
    /// Start        │       │
    /// Process  ┌──►│       │
    ///    │     │   │       │
    ///    └─────┘   └───────┘
    /// </code>
    /// </summary>
    /// <param name="processName"></param>
    /// <returns></returns>
    public static KernelProcess GetSimpleMergeProcess(string processName = ProcessKeys.SimpleMergeProcess)
    {
        ProcessBuilder process = new(processName);

        var mergeStep = process.AddStepFromType<CommonSteps.MergeStringsStep>(id: nameof(CommonSteps.MergeStringsStep));

        var finalEchoStep = process.AddStepFromType<CommonSteps.EchoStep>(id: nameof(CommonSteps.EchoStep));

        // merging inputs
        process
            .ListenFor()
            .AllOf([
                new(messageType: ProcessEvents.StartProcess, process),
                new(messageType: ProcessEvents.StartProcess, process),
                new(messageType: ProcessEvents.OtherEvent, process),
            ])
            .SendEventTo(new ProcessStepTargetBuilder(mergeStep, inputMapping: (inputEvents) =>
            {
                return new()
                {
                    { "str1", inputEvents[process.GetFullEventId(ProcessEvents.StartProcess)] },
                    { "str2", inputEvents[process.GetFullEventId(ProcessEvents.StartProcess)] },
                    { "str3", inputEvents[process.GetFullEventId(ProcessEvents.OtherEvent)] },
                };
            }));

        mergeStep
            .OnFunctionResult()
            .SendEventTo(new ProcessFunctionTargetBuilder(finalEchoStep));

        return process.Build();
    }

    /// <summary>
    /// Process that delays the merge of three strings until all three are available.
    /// Helps test make use of ListenFor() and AllOf() methods with events from steps.
    /// <code>
    ///         ┌────────┐
    /// Other ─►│ echo1  ├───────────────────────────────┐   ┌───────┐
    ///         └────────┘                               │   │       │
    ///                                                  └──►│       │
    ///                                                      │       │
    ///         ┌────────┐     ┌────────┐                    │       │    ┌───────────┐
    ///    ┌──► │ echo21 ├────►│ echo22 ├───────────────────►│ merge ├───►│ finalEcho │
    ///    │    └────────┘     └────────┘                    │       │    └───────────┘
    /// Start                                                │       │
    /// Process                                          ┌──►│       │
    ///    │    ┌────────┐     ┌────────┐    ┌────────┐  │   │       │
    ///    └──► │ echo31 ├────►│ echo32 ├───►│ echo33 ├──┘   └───────┘
    ///         └────────┘     └────────┘    └────────┘
    /// </code>
    /// </summary>
    /// <param name="processName"></param>
    /// <returns></returns>
    public static KernelProcess GetDelayedMergeProcess(string processName = ProcessKeys.DelayedMergeProcess)
    {
        ProcessBuilder process = new(processName);

        var echoStep1 = process.AddStepFromType<CommonSteps.DelayedEchoStep>(id: $"{nameof(CommonSteps.DelayedEchoStep)}1");
        var echoStep21 = process.AddStepFromType<CommonSteps.DelayedEchoStep>(id: $"{nameof(CommonSteps.DelayedEchoStep)}21");
        var echoStep22 = process.AddStepFromType<CommonSteps.DelayedEchoStep>(id: $"{nameof(CommonSteps.DelayedEchoStep)}22");
        var echoStep31 = process.AddStepFromType<CommonSteps.DelayedEchoStep>(id: $"{nameof(CommonSteps.DelayedEchoStep)}31");
        var echoStep32 = process.AddStepFromType<CommonSteps.DelayedEchoStep>(id: $"{nameof(CommonSteps.DelayedEchoStep)}32");
        var echoStep33 = process.AddStepFromType<CommonSteps.DelayedEchoStep>(id: $"{nameof(CommonSteps.DelayedEchoStep)}33");

        var mergeStep = process.AddStepFromType<CommonSteps.MergeStringsStep>(id: nameof(CommonSteps.MergeStringsStep));

        var finalEchoStep = process.AddStepFromType<CommonSteps.EchoStep>(id: nameof(CommonSteps.EchoStep));

        process
            .OnInputEvent(ProcessEvents.StartProcess)
            //.SendEventTo(new(echoStep1))
            .SendEventTo(new(echoStep21))
            .SendEventTo(new(echoStep31));

        process
            .OnInputEvent(ProcessEvents.OtherEvent)
            .SendEventTo(new ProcessFunctionTargetBuilder(echoStep1));

        echoStep21
            .OnFunctionResult()
            .SendEventTo(new ProcessFunctionTargetBuilder(echoStep22));

        echoStep31
            .OnFunctionResult()
            .SendEventTo(new ProcessFunctionTargetBuilder(echoStep32));

        echoStep32
            .OnFunctionResult()
            .SendEventTo(new ProcessFunctionTargetBuilder(echoStep33));

        // merging inputs
        process
            .ListenFor()
            .AllOf([
                new(messageType: CommonSteps.DelayedEchoStep.OutputEvents.DelayedEcho, echoStep1),
                new(messageType: CommonSteps.DelayedEchoStep.OutputEvents.DelayedEcho, echoStep22),
                new(messageType: CommonSteps.DelayedEchoStep.OutputEvents.DelayedEcho, echoStep33),
            ])
            .SendEventTo(new ProcessStepTargetBuilder(mergeStep, inputMapping: (inputEvents) =>
            {
                return new()
                {
                    { "str1", inputEvents[echoStep1.GetFullEventId(CommonSteps.DelayedEchoStep.OutputEvents.DelayedEcho)] },
                    { "str2", inputEvents[echoStep22.GetFullEventId(CommonSteps.DelayedEchoStep.OutputEvents.DelayedEcho)] },
                    { "str3", inputEvents[echoStep33.GetFullEventId(CommonSteps.DelayedEchoStep.OutputEvents.DelayedEcho)] },
                };
            }));

        mergeStep
            .OnFunctionResult()
            .SendEventTo(new ProcessFunctionTargetBuilder(finalEchoStep));

        return process.Build();
    }

    public static IReadOnlyDictionary<string, KernelProcess> GetCommonProcessesKeyedDictionary()
    {
        return new Dictionary<string, KernelProcess>() {
            { ProcessKeys.CounterProcess, GetCounterProcess() },
            { ProcessKeys.CounterWithEvenNumberDetectionProcess, GetCounterWithEvenDetectionProcess().Build() },
            { ProcessKeys.NestedCounterWithEvenDetectionAndMergeProcess, GetNestedCounterWithEvenDetectionAndMergeProcess().Build() },
            { ProcessKeys.InternalNestedCounterWithEvenDetectionAndMergeProcess, GetInternalNestedCounterWithEvenDetectionAndMergeProcess() },
            { ProcessKeys.DelayedMergeProcess, GetDelayedMergeProcess() },
            { ProcessKeys.SimpleMergeProcess, GetSimpleMergeProcess() },
        };
    }
}
