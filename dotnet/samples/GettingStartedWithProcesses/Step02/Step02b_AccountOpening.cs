// Copyright (c) Microsoft. All rights reserved.

using Events;
using Microsoft.SemanticKernel;
using SharedSteps;
using Step02.Models;
using Step02.Processes;
using Step02.Steps;
using Step02.Utils;

namespace Step02;

/// <summary>
/// Demonstrate creation of <see cref="KernelProcess"/> and
/// eliciting its response to five explicit user messages.<br/>
/// For each test there is a different set of user messages that will cause different steps to be triggered using the same pipeline.<br/>
/// For visual reference of the process check the <see href="https://github.com/microsoft/semantic-kernel/tree/main/dotnet/samples/GettingStartedWithProcesses/README.md#step02b_accountOpening" >diagram</see>.
/// </summary>
public class Step02b_AccountOpening(ITestOutputHelper output) : BaseTest(output, redirectSystemConsoleOutput: true)
{
    // Target Open AI Services
    protected override bool ForceOpenAI => true;

    private KernelProcess SetupAccountOpeningProcess<TUserInputStep>() where TUserInputStep : ScriptedUserInputStep
    {
        ProcessBuilder process = new("AccountOpeningProcessWithSubprocesses");
        var newCustomerFormStep = process.AddStepFromType<CompleteNewCustomerFormStep>();
        var userInputStep = process.AddStepFromType<TUserInputStep>();
        var displayAssistantMessageStep = process.AddStepFromType<DisplayAssistantMessageStep>();

        var accountVerificationStep = (ProcessBuilder<NewAccountVerificationProcess.ProcessEvents>)process.AddStepFromProcess(NewAccountVerificationProcess.CreateProcess());
        var accountCreationStep = (ProcessBuilder<NewAccountCreationProcess.ProcessEvents>)process.AddStepFromProcess(NewAccountCreationProcess.CreateProcess());

        var mailServiceStep = process.AddStepFromType<MailServiceStep>();

        process
            .OnInputEvent(AccountOpeningEvents.StartProcess)
            .SendEventTo(new ProcessFunctionTargetBuilder(newCustomerFormStep, CompleteNewCustomerFormStep.Functions.NewAccountWelcome));

        // When the welcome message is generated, send message to displayAssistantMessageStep
        newCustomerFormStep
            .OnEvent(AccountOpeningEvents.NewCustomerFormWelcomeMessageComplete)
            .SendEventTo(new ProcessFunctionTargetBuilder(displayAssistantMessageStep, DisplayAssistantMessageStep.Functions.DisplayAssistantMessage));

        // When the userInput step emits a user input event, send it to the newCustomerForm step
        // Function names are necessary when the step has multiple public functions like CompleteNewCustomerFormStep: NewAccountWelcome and NewAccountProcessUserInfo
        userInputStep
            .OnEvent(CommonEvents.UserInputReceived)
            .SendEventTo(new ProcessFunctionTargetBuilder(newCustomerFormStep, CompleteNewCustomerFormStep.Functions.NewAccountProcessUserInfo, "userMessage"));

        userInputStep
            .OnEvent(CommonEvents.Exit)
            .StopProcess();

        // When the newCustomerForm step emits needs more details, send message to displayAssistantMessage step
        newCustomerFormStep
            .OnEvent(AccountOpeningEvents.NewCustomerFormNeedsMoreDetails)
            .SendEventTo(new ProcessFunctionTargetBuilder(displayAssistantMessageStep, DisplayAssistantMessageStep.Functions.DisplayAssistantMessage));

        // After any assistant message is displayed, user input is expected to the next step is the userInputStep
        displayAssistantMessageStep
            .OnEvent(CommonEvents.AssistantResponseGenerated)
            .SendEventTo(new ProcessFunctionTargetBuilder(userInputStep, ScriptedUserInputStep.Functions.GetUserInput));

        // When the newCustomerForm is completed...
        newCustomerFormStep
            .OnEvent(AccountOpeningEvents.NewCustomerFormCompleted)
            // The information gets passed to the account verificatino step
            .SendEventTo(accountVerificationStep.WhereInputEventIs(NewAccountVerificationProcess.ProcessEvents.OnNewCustomerFormCompleted))
            // The information gets passed to the validation process step
            .SendEventTo(accountCreationStep.WhereInputEventIs(NewAccountCreationProcess.ProcessEvents.OnNewCustomerFormCompleted));

        // When the newCustomerForm is completed, the user interaction transcript with the user is passed to the core system record creation step
        newCustomerFormStep
            .OnEvent(AccountOpeningEvents.CustomerInteractionTranscriptReady)
            .SendEventTo(accountCreationStep.WhereInputEventIs(NewAccountCreationProcess.ProcessEvents.OnCustomerTranscriptReady));

        // When the creditScoreCheck step results in Rejection, the information gets to the mailService step to notify the user about the state of the application and the reasons
        accountVerificationStep
            // .OnEvent(AccountOpeningEvents.CreditScoreCheckRejected) // if using OnEvent the event name must match exactly the name emitted by the inner step
            .OnProcessEvent(NewAccountVerificationProcess.ProcessEvents.OnNewUserCreditCheckFailed)
            .SendEventTo(new ProcessFunctionTargetBuilder(mailServiceStep));

        // When the fraudDetectionCheck step fails, the information gets to the mailService step to notify the user about the state of the application and the reasons
        accountVerificationStep
            // .OnEvent(AccountOpeningEvents.FraudDetectionCheckFailed) // if using OnEvent the event name must match exactly the name emitted by the inner step
            .OnProcessEvent(NewAccountVerificationProcess.ProcessEvents.OnNewUserFraudCheckFailed)
            .SendEventTo(new ProcessFunctionTargetBuilder(mailServiceStep));

        // When the fraudDetectionCheck step passes, the information gets to core system record creation step to kickstart this step
        accountVerificationStep
            // .OnEvent(AccountOpeningEvents.FraudDetectionCheckPassed) // if using OnEvent the event name must match exactly the name emitted by the inner step
            .OnProcessEvent(NewAccountVerificationProcess.ProcessEvents.OnNewAccountVerificationSucceeded)
            .SendEventTo(accountCreationStep.WhereInputEventIs(NewAccountCreationProcess.ProcessEvents.OnNewAccountVerificationPassed));

        // After crmRecord and marketing gets created, a welcome packet is created to then send information to the user with the mailService step
        accountCreationStep
            .OnProcessEvent(NewAccountCreationProcess.ProcessEvents.AccountCreatedSuccessfully)
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
        // Arrange
        Kernel kernel = CreateKernelWithChatCompletion();
        KernelProcess kernelProcess = SetupAccountOpeningProcess<UserInputSuccessfulInteractionStep>();
        // Act
        var runningProcess = await kernelProcess.StartAsync(kernel, new KernelProcessEvent() { Id = AccountOpeningEvents.StartProcess, Data = null });
        // Assert
        var processInfo = await runningProcess.GetStateAsync();
        AccountOpeningAsserts.AssertAccountOpeningSuccessMailMessage(processInfo, nameof(MailServiceStep));
    }

    /// <summary>
    /// This test uses a specific DOB that makes the creditScore to fail
    /// </summary>
    [Fact]
    public async Task UseAccountOpeningProcessFailureDueToCreditScoreFailureAsync()
    {
        // Arrange
        Kernel kernel = CreateKernelWithChatCompletion();
        KernelProcess kernelProcess = SetupAccountOpeningProcess<UserInputCreditScoreFailureInteractionStep>();
        // Act
        var runningProcess = await kernelProcess.StartAsync(kernel, new KernelProcessEvent() { Id = AccountOpeningEvents.StartProcess, Data = null });
        // Assert
        var processInfo = await runningProcess.GetStateAsync();
        AccountOpeningAsserts.AssertAccountOpeningFailDueCreditScoreMailMessage(processInfo, nameof(MailServiceStep));
    }

    /// <summary>
    /// This test uses a specific userId that makes the fraudDetection to fail
    /// </summary>
    [Fact]
    public async Task UseAccountOpeningProcessFailureDueToFraudFailureAsync()
    {
        // Arrange
        Kernel kernel = CreateKernelWithChatCompletion();
        KernelProcess kernelProcess = SetupAccountOpeningProcess<UserInputFraudFailureInteractionStep>();
        // Act
        var runningProcess = await kernelProcess.StartAsync(kernel, new KernelProcessEvent() { Id = AccountOpeningEvents.StartProcess, Data = null });
        // Assert
        var processInfo = await runningProcess.GetStateAsync();
        AccountOpeningAsserts.AssertAccountOpeningFailDueFraudMailMessage(processInfo, nameof(MailServiceStep));
    }
}
