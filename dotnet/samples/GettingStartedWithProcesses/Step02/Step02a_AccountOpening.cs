// Copyright (c) Microsoft. All rights reserved.

using Events;
using Microsoft.SemanticKernel;
using SharedSteps;
using Step02.Models;
using Step02.Steps;

namespace Step02;

/// <summary>
/// Demonstrate creation of <see cref="KernelProcess"/> and
/// eliciting its response to five explicit user messages.<br/>
/// For each test there is a different set of user messages that will cause different steps to be triggered using the same pipeline.<br/>
/// For visual reference of the process check the <see href="https://github.com/microsoft/semantic-kernel/tree/main/dotnet/samples/GettingStartedWithProcesses/README.md#step02a_accountOpening" >diagram</see>.
/// </summary>
public class Step02a_AccountOpening(ITestOutputHelper output) : BaseTest(output, redirectSystemConsoleOutput: true)
{
    // Target Open AI Services
    protected override bool ForceOpenAI => true;

    private KernelProcess SetupAccountOpeningProcess<TUserInputStep>() where TUserInputStep : ScriptedUserInputStep
    {
        ProcessBuilder process = new("AccountOpeningProcess");
        var newCustomerFormStep = process.AddStepFromType<CompleteNewCustomerFormStep>();
        var userInputStep = process.AddStepFromType<TUserInputStep>();
        var displayAssistantMessageStep = process.AddStepFromType<DisplayAssistantMessageStep>();
        var customerCreditCheckStep = process.AddStepFromType<CreditScoreCheckStep>();
        var fraudDetectionCheckStep = process.AddStepFromType<FraudDetectionStep>();
        var mailServiceStep = process.AddStepFromType<MailServiceStep>();
        var coreSystemRecordCreationStep = process.AddStepFromType<NewAccountStep>();
        var marketingRecordCreationStep = process.AddStepFromType<NewMarketingEntryStep>();
        var crmRecordStep = process.AddStepFromType<CRMRecordCreationStep>();
        var welcomePacketStep = process.AddStepFromType<WelcomePacketStep>();

        process.OnInputEvent(AccountOpeningEvents.StartProcess)
            .SendEventTo(new ProcessFunctionTargetBuilder(newCustomerFormStep, CompleteNewCustomerFormStep.ProcessStepFunctions.NewAccountWelcome));

        // When the welcome message is generated, send message to displayAssistantMessageStep
        newCustomerFormStep
            .OnEvent(AccountOpeningEvents.NewCustomerFormWelcomeMessageComplete)
            .SendEventTo(new ProcessFunctionTargetBuilder(displayAssistantMessageStep, DisplayAssistantMessageStep.ProcessStepFunctions.DisplayAssistantMessage));

        // When the userInput step emits a user input event, send it to the newCustomerForm step
        // Function names are necessary when the step has multiple public functions like CompleteNewCustomerFormStep: NewAccountWelcome and NewAccountProcessUserInfo
        userInputStep
            .OnEvent(CommonEvents.UserInputReceived)
            .SendEventTo(new ProcessFunctionTargetBuilder(newCustomerFormStep, CompleteNewCustomerFormStep.ProcessStepFunctions.NewAccountProcessUserInfo));

        userInputStep
            .OnEvent(CommonEvents.Exit)
            .StopProcess();

        // When the newCustomerForm step emits needs more details, send message to displayAssistantMessage step
        newCustomerFormStep
            .OnEvent(AccountOpeningEvents.NewCustomerFormNeedsMoreDetails)
            .SendEventTo(new ProcessFunctionTargetBuilder(displayAssistantMessageStep, DisplayAssistantMessageStep.ProcessStepFunctions.DisplayAssistantMessage));

        // After any assistant message is displayed, user input is expected to the next step is the userInputStep
        displayAssistantMessageStep
            .OnEvent(CommonEvents.AssistantResponseGenerated)
            .SendEventTo(new ProcessFunctionTargetBuilder(userInputStep, ScriptedUserInputStep.ProcessStepFunctions.GetUserInput));

        // When the newCustomerForm is completed...
        newCustomerFormStep
            .OnEvent(AccountOpeningEvents.NewCustomerFormCompleted)
            // The information gets passed to the credit check step record creation step
            .SendEventTo(new ProcessFunctionTargetBuilder(customerCreditCheckStep, functionName: CreditScoreCheckStep.ProcessStepFunctions.DetermineCreditScore));

        // When the creditScoreCheck step results in Rejection, the information gets to the mailService step to notify the user about the state of the application and the reasons
        customerCreditCheckStep
            .OnEvent(AccountOpeningEvents.CreditScoreCheckRejected)
            .SendEventTo(new ProcessFunctionTargetBuilder(mailServiceStep));

        process
            .ListenFor()
            .AllOf([
                // When the newCustomerForm is completed the information gets passed to the fraud detection step for validation
                new(AccountOpeningEvents.NewCustomerFormCompleted, newCustomerFormStep),
               // When the creditScoreCheck step results in Approval, the information gets to the fraudDetection step to kickstart this step
                new(AccountOpeningEvents.CreditScoreCheckApproved, customerCreditCheckStep)
            ])
            .SendEventTo(new ProcessStepTargetBuilder(fraudDetectionCheckStep, inputMapping: (inputEvents) =>
            {
                return new()
                {
                    { "customerDetails", inputEvents[newCustomerFormStep.GetFullEventId(AccountOpeningEvents.NewCustomerFormCompleted)] },
                    { "previousCheckSucceeded", inputEvents[customerCreditCheckStep.GetFullEventId(AccountOpeningEvents.CreditScoreCheckApproved)] },
                };
            }));

        // When the fraudDetectionCheck step fails, the information gets to the mailService step to notify the user about the state of the application and the reasons
        fraudDetectionCheckStep
            .OnEvent(AccountOpeningEvents.FraudDetectionCheckFailed)
            .SendEventTo(new ProcessFunctionTargetBuilder(mailServiceStep));

        process
            .ListenFor()
            .AllOf(
            [
                // When the newCustomerForm is completed, the information gets passed to the core system record creation step
                new(AccountOpeningEvents.NewCustomerFormCompleted, newCustomerFormStep),
                // When the newCustomerForm is completed, the user interaction transcript with the user is passed to the core system record creation step
                new(AccountOpeningEvents.CustomerInteractionTranscriptReady, newCustomerFormStep),
                // When the fraudDetectionCheck step passes, the information gets to core system record creation step to kickstart this step
                new(AccountOpeningEvents.FraudDetectionCheckPassed, fraudDetectionCheckStep),
            ]).SendEventTo(new ProcessStepTargetBuilder(coreSystemRecordCreationStep, inputMapping: (inputEvents) =>
            {
                return new()
                {
                    { "customerDetails", inputEvents[newCustomerFormStep.GetFullEventId(AccountOpeningEvents.NewCustomerFormCompleted)] },
                    { "interactionTranscript", inputEvents[newCustomerFormStep.GetFullEventId(AccountOpeningEvents.CustomerInteractionTranscriptReady)] },
                    { "previousCheckSucceeded", inputEvents[fraudDetectionCheckStep.GetFullEventId(AccountOpeningEvents.FraudDetectionCheckPassed)] },
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

        // After crmRecord and marketing gets created, a welcome packet is created to then send information to the user with the mailService step
        welcomePacketStep
            .OnEvent(AccountOpeningEvents.WelcomePacketCreated)
            .SendEventTo(new ProcessFunctionTargetBuilder(mailServiceStep));

        // All possible paths end up with the user being notified about the account creation decision throw the mailServiceStep completion
        mailServiceStep
            .OnEvent(AccountOpeningEvents.MailServiceSent)
            .StopProcess();

        KernelProcess kernelProcess = process.Build();

        return kernelProcess;
    }

    /// <summary>
    /// This test uses a specific userId and DOB that makes the creditScore and Fraud detection to pass
    /// </summary>
    [Fact]
    public async Task UseAccountOpeningProcessSuccessfulInteractionAsync()
    {
        Kernel kernel = CreateKernelWithChatCompletion();
        KernelProcess kernelProcess = SetupAccountOpeningProcess<UserInputSuccessfulInteractionStep>();
        await using var runningProcess = await kernelProcess.StartAsync(kernel, new KernelProcessEvent() { Id = AccountOpeningEvents.StartProcess, Data = null });
    }

    /// <summary>
    /// This test uses a specific DOB that makes the creditScore to fail
    /// </summary>
    [Fact]
    public async Task UseAccountOpeningProcessFailureDueToCreditScoreFailureAsync()
    {
        Kernel kernel = CreateKernelWithChatCompletion();
        KernelProcess kernelProcess = SetupAccountOpeningProcess<UserInputCreditScoreFailureInteractionStep>();
        await using var runningProcess = await kernelProcess.StartAsync(kernel, new KernelProcessEvent() { Id = AccountOpeningEvents.StartProcess, Data = null });
    }

    /// <summary>
    /// This test uses a specific userId that makes the fraudDetection to fail
    /// </summary>
    [Fact]
    public async Task UseAccountOpeningProcessFailureDueToFraudFailureAsync()
    {
        Kernel kernel = CreateKernelWithChatCompletion();
        KernelProcess kernelProcess = SetupAccountOpeningProcess<UserInputFraudFailureInteractionStep>();
        await using var runningProcess = await kernelProcess.StartAsync(kernel, new KernelProcessEvent() { Id = AccountOpeningEvents.StartProcess, Data = null });
    }
}
