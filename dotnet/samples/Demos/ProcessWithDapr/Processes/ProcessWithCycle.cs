// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;
using ProcessWithDapr.ProcessSteps;

namespace ProcessWithDapr.Processes;

internal static class ProcessWithCycle
{
    internal static string Key = "ProcessWithCycle";

    internal static KernelProcess Build()
    {
        // Create the process builder.
        ProcessBuilder processBuilder = new(ProcessWithCycle.Key);

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

        // When step A and step B have finished, trigger the CStep.
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
                        { "astepdata", inputEvents[$"{nameof(AStep)}.{CommonEvents.AStepDone}"] },
                        { "bstepdata", inputEvents[$"{nameof(BStep)}.{CommonEvents.BStepDone}"] }
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

        return processBuilder.Build();
    }
}
