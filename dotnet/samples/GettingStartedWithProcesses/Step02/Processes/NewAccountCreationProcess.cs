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
            .ListenFor()
            .AllOf(
            [
                // When the newCustomerForm is completed, the new user form is passed to the core system record creation step
                new(AccountOpeningEvents.NewCustomerFormCompleted, process),
                // When the newCustomerForm is completed, the user interaction transcript with the user is passed to the core system record creation step
                new(AccountOpeningEvents.CustomerInteractionTranscriptReady, process),
                // When the fraudDetectionCheck step passes, the information gets to core system record creation step to kickstart this step
                new(AccountOpeningEvents.NewAccountVerificationCheckPassed, process)
            ]).SendEventTo(new ProcessStepTargetBuilder(coreSystemRecordCreationStep, inputMapping: (inputEvents) =>
            {
                return new()
                {
                    { "customerDetails", inputEvents[process.GetFullEventId(AccountOpeningEvents.NewCustomerFormCompleted)] },
                    { "interactionTranscript", inputEvents[process.GetFullEventId(AccountOpeningEvents.CustomerInteractionTranscriptReady)] },
                    { "previousCheckSucceeded", inputEvents[process.GetFullEventId(AccountOpeningEvents.NewAccountVerificationCheckPassed)] },
                };
            }));

        // When the coreSystemRecordCreation step successfully creates a new accountId, it will trigger the creation of a new marketing entry through the marketingRecordCreation step
        coreSystemRecordCreationStep
            .OnEvent(AccountOpeningEvents.NewMarketingRecordInfoReady)
            .SendEventTo(new ProcessFunctionTargetBuilder(marketingRecordCreationStep));

        // When the coreSystemRecordCreation step successfully creates a new accountId, it will trigger the creation of a new CRM entry through the crmRecord step
        coreSystemRecordCreationStep
            .OnEvent(AccountOpeningEvents.CRMRecordInfoReady)
            .SendEventTo(new ProcessFunctionTargetBuilder(crmRecordStep));

        process
            .ListenFor()
            .AllOf([
                // When the coreSystemRecordCreation step successfully creates a new accountId, it will pass the account information details to the welcomePacket step
                new(AccountOpeningEvents.NewAccountDetailsReady, coreSystemRecordCreationStep),
                // When the marketingRecordCreation step successfully creates a new marketing entry, it will notify the welcomePacket step it is ready
                new(AccountOpeningEvents.NewMarketingEntryCreated, marketingRecordCreationStep),
                // When the crmRecord step successfully creates a new CRM entry, it will notify the welcomePacket step it is ready
                new(AccountOpeningEvents.CRMRecordInfoEntryCreated, crmRecordStep)
            ])
            .SendEventTo(new ProcessStepTargetBuilder(welcomePacketStep, inputMapping: (inputEvents) =>
            {
                return new()
                {
                    { "accountDetails", inputEvents[coreSystemRecordCreationStep.GetFullEventId(AccountOpeningEvents.NewAccountDetailsReady)] },
                    { "marketingEntryCreated", inputEvents[marketingRecordCreationStep.GetFullEventId(AccountOpeningEvents.NewMarketingEntryCreated)] },
                    { "crmRecordCreated", inputEvents[crmRecordStep.GetFullEventId(AccountOpeningEvents.CRMRecordInfoEntryCreated)] },
                };
            }));

        return process;
    }
}
