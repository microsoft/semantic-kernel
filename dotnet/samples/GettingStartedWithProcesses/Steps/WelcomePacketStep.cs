// Copyright (c) Microsoft. All rights reserved.

using Events;
using Microsoft.SemanticKernel;
using Models;

namespace Steps;

/// <summary>
/// Step used in the Processes Samples:
/// - Step_02_AccountOpening.cs
/// </summary>
public class WelcomePacketStep : KernelProcessStep
{
    public static class Functions
    {
        public const string CreateWelcomePacket = "CreateWelcomePacket";
    }

    [KernelFunction(Functions.CreateWelcomePacket)]
    public async Task CreateWelcomePacketAsync(KernelProcessStepContext context, bool marketingEntryCreated, bool crmRecordCreated, AccountDetails accountDetails, Kernel _kernel)
    {
        await context.EmitEventAsync(new()
        {
            Id = AccountOpeningEvents.WelcomePacketCreated,
            Data = $"""
                Dear {accountDetails.UserFirstName} {accountDetails.UserLastName}
                We are thrilled to inform you that you have successfully created a new PRIME ABC Account with us!

                Account Details:
                Account Number: {accountDetails.AccountId}
                Account Type: {accountDetails.AccountType}

                Please keep this confidential for security purposes.

                Here is the contact information we have in file:

                Email: {accountDetails.UserEmail}
                Phone: {accountDetails.UserPhoneNumber}

                Thank you for opening an account with us!
                """
        });
    }
}
