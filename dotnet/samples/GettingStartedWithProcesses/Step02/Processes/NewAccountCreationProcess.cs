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
public static class NewAccountCreationProcess
{
    public static ProcessBuilder CreateProcess()
    {
        ProcessBuilder process = new("AccountCreationProcess");

        var coreSystemRecordCreationStep = process.AddStepFromType<NewAccountStep>();
        var marketingRecordCreationStep = process.AddStepFromType<NewMarketingEntryStep>();
        var crmRecordStep = process.AddStepFromType<CRMRecordCreationStep>();
        var welcomePacketStep = process.AddStepFromType<WelcomePacketStep>();

        // When the newCustomerForm is completed...
        process
            .OnInputEvent(AccountOpeningEvents.NewCustomerFormCompleted)
            // The information gets passed to the core system record creation step
            .SendEventTo(new ProcessFunctionTargetBuilder(coreSystemRecordCreationStep, functionName: NewAccountStep.ProcessStepFunctions.CreateNewAccount, parameterName: "customerDetails"));

        // When the newCustomerForm is completed, the user interaction transcript with the user is passed to the core system record creation step
        process
            .OnInputEvent(AccountOpeningEvents.CustomerInteractionTranscriptReady)
            .SendEventTo(new ProcessFunctionTargetBuilder(coreSystemRecordCreationStep, functionName: NewAccountStep.ProcessStepFunctions.CreateNewAccount, parameterName: "interactionTranscript"));

        // When the fraudDetectionCheck step passes, the information gets to core system record creation step to kickstart this step
        process
            .OnInputEvent(AccountOpeningEvents.NewAccountVerificationCheckPassed)
            .SendEventTo(new ProcessFunctionTargetBuilder(coreSystemRecordCreationStep, functionName: NewAccountStep.ProcessStepFunctions.CreateNewAccount, parameterName: "previousCheckSucceeded"));

        // When the coreSystemRecordCreation step successfully creates a new accountId, it will trigger the creation of a new marketing entry through the marketingRecordCreation step
        coreSystemRecordCreationStep
            .OnEvent(AccountOpeningEvents.NewMarketingRecordInfoReady)
            .SendEventTo(new ProcessFunctionTargetBuilder(marketingRecordCreationStep, functionName: NewMarketingEntryStep.ProcessStepFunctions.CreateNewMarketingEntry, parameterName: "userDetails"));

        // When the coreSystemRecordCreation step successfully creates a new accountId, it will trigger the creation of a new CRM entry through the crmRecord step
        coreSystemRecordCreationStep
            .OnEvent(AccountOpeningEvents.CRMRecordInfoReady)
            .SendEventTo(new ProcessFunctionTargetBuilder(crmRecordStep, functionName: CRMRecordCreationStep.ProcessStepFunctions.CreateCRMEntry, parameterName: "userInteractionDetails"));

        // ParameterName is necessary when the step has multiple input arguments like welcomePacketStep.CreateWelcomePacketAsync
        // When the coreSystemRecordCreation step successfully creates a new accountId, it will pass the account information details to the welcomePacket step
        coreSystemRecordCreationStep
            .OnEvent(AccountOpeningEvents.NewAccountDetailsReady)
            .SendEventTo(new ProcessFunctionTargetBuilder(welcomePacketStep, parameterName: "accountDetails"));

        // When the marketingRecordCreation step successfully creates a new marketing entry, it will notify the welcomePacket step it is ready
        marketingRecordCreationStep
            .OnEvent(AccountOpeningEvents.NewMarketingEntryCreated)
            .SendEventTo(new ProcessFunctionTargetBuilder(welcomePacketStep, parameterName: "marketingEntryCreated"));

        // When the crmRecord step successfully creates a new CRM entry, it will notify the welcomePacket step it is ready
        crmRecordStep
            .OnEvent(AccountOpeningEvents.CRMRecordInfoEntryCreated)
            .SendEventTo(new ProcessFunctionTargetBuilder(welcomePacketStep, parameterName: "crmRecordCreated"));

        return process;
    }
}
