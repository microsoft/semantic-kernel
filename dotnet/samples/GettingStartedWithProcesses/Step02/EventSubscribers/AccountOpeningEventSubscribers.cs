// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.Process;
using Step02.Models;

namespace Step02.EventSubscribers;
/// <summary>
/// The SK Process Event Subscribers can link to specific Process Events triggered
/// by making use of the <see cref="KernelProcessEventsSubscriber{TEnum}.ProcessEventSubscriberAttribute" />
/// </summary>
public class AccountOpeningEventSubscribers : KernelProcessEventsSubscriber<AccountOpeningEvents.NewAccountOpeningEvents>
{
    [ProcessEventSubscriber(AccountOpeningEvents.NewAccountOpeningEvents.OnNewUserCreditCheckFailed)]
    public Task OnSendMailDueCreditCheckFailure(string message)
    {
        this.MockSendEmail("New Account Failure [CREDIT]", message);
        return Task.CompletedTask;
    }

    [ProcessEventSubscriber(AccountOpeningEvents.NewAccountOpeningEvents.OnNewUserFraudCheckFailed)]
    public Task OnSendMailDueFraudCheckFailure(string message)
    {
        this.MockSendEmail("New Account Failure [FRAUD]", message);
        return Task.CompletedTask;
    }

    [ProcessEventSubscriber(AccountOpeningEvents.NewAccountOpeningEvents.AccountCreatedSuccessfully)]
    public Task OnSendMailWithNewAccountInfo(string message)
    {
        this.MockSendEmail("Welcome! You have a new account", message);
        return Task.CompletedTask;
    }

    private void MockSendEmail(string subject, string message)
    {
        Console.WriteLine("======== MAIL SERVICE (via SK Event Subscribers) ========");
        Console.WriteLine($"SUBJECT:  {subject}");
        Console.WriteLine(message);
        Console.WriteLine("=========================================================");
    }
}
