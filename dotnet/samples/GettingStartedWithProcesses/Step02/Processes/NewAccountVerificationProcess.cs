// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;
using Step02.Models;
using Step02.Steps;

namespace Step02.Processes;

/// <summary>
/// Demonstrate creation of <see cref="KernelProcess"/> and
/// eliciting its response to five explicit user messages.<br/>
/// For each test there is a different set of user messages that will cause different steps to be triggered using the same pipeline.<br/>
/// For visual reference of the process check the <see href="https://github.com/microsoft/semantic-kernel/tree/main/dotnet/samples/GettingStartedWithProcesses/README.md#step02b_accountOpening" >diagram</see>.
/// </summary>
public static class NewAccountVerificationProcess
{
    /// <summary>
    /// Process events allow to only expose the relevant events that have interactions with external components to this process as input or output events.<br/>
    /// This way when using the process as a step in another process it can be seen as:
    /// <code>
    ///         PROCESS INPUTS                                PROCESS OUTPUTS
    ///                               ┌─────────┐
    ///                               │         │───► OnNewUserFraudCheckFailed
    ///                               │         │
    /// OnNewCusotmerFormCompleted ──►│ Process │───► OnNewAccountVerificationSucceeded
    ///                               │         │
    ///                               │         │───► OnNewUserCreditCheckFailed
    ///                               └─────────┘
    /// </code>
    /// </summary>
    public enum ProcessEvents
    {
        // Process Input Events
        OnNewCustomerFormCompleted,
        // Process Output Events
        OnNewAccountVerificationSucceeded,
        OnNewUserFraudCheckFailed,
        OnNewUserCreditCheckFailed
    }

    public static ProcessBuilder<ProcessEvents> CreateProcess()
    {
        var process = new ProcessBuilder<ProcessEvents>("AccountVerificationProcess");

        var customerCreditCheckStep = process.AddStepFromType<CreditScoreCheckStep>();
        var fraudDetectionCheckStep = process.AddStepFromType<FraudDetectionStep>();

        // When the newCustomerForm is completed...
        process
            .OnInputEvent(ProcessEvents.OnNewCustomerFormCompleted)
            // The information gets passed to the core system record creation step
            .SendEventTo(new ProcessFunctionTargetBuilder(customerCreditCheckStep, functionName: CreditScoreCheckStep.Functions.DetermineCreditScore, parameterName: "customerDetails"))
            // The information gets passed to the fraud detection step for validation
            .SendEventTo(new ProcessFunctionTargetBuilder(fraudDetectionCheckStep, functionName: FraudDetectionStep.Functions.FraudDetectionCheck, parameterName: "customerDetails"));

        // When the creditScoreCheck step results in Approval, the information gets to the fraudDetection step to kickstart this step
        customerCreditCheckStep
            .OnEvent(AccountOpeningEvents.CreditScoreCheckApproved)
            .SendEventTo(new ProcessFunctionTargetBuilder(fraudDetectionCheckStep, functionName: FraudDetectionStep.Functions.FraudDetectionCheck, parameterName: "previousCheckSucceeded"));

        customerCreditCheckStep
            .OnEvent(AccountOpeningEvents.CreditScoreCheckRejected)
            .EmitAsProcessEvent(process.GetProcessEvent(ProcessEvents.OnNewUserCreditCheckFailed));

        fraudDetectionCheckStep
            .OnEvent(AccountOpeningEvents.FraudDetectionCheckPassed)
            .EmitAsProcessEvent(process.GetProcessEvent(ProcessEvents.OnNewAccountVerificationSucceeded));

        fraudDetectionCheckStep
            .OnEvent(AccountOpeningEvents.FraudDetectionCheckFailed)
            .EmitAsProcessEvent(process.GetProcessEvent(ProcessEvents.OnNewUserFraudCheckFailed));

        return process;
    }
}
