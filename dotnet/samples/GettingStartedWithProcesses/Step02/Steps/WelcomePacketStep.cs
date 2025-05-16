// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;
using Step02.Models;

namespace Step02.Steps;

/// <summary>
/// Mock step that emulates the creation of a Welcome Packet for a new user after account creation
/// </summary>
public class WelcomePacketStep : KernelProcessStep
{
    public static class ProcessStepFunctions
    {
        public const string CreateWelcomePacket = nameof(CreateWelcomePacket);
    }

    [KernelFunction(ProcessStepFunctions.CreateWelcomePacket)]
    public async Task CreateWelcomePacketAsync(KernelProcessStepContext context, bool marketingEntryCreated, bool crmRecordCreated, AccountDetails accountDetails, Kernel _kernel)
    {
        Console.WriteLine($"[WELCOME PACKET] New Account {accountDetails.AccountId} created");

        var mailMessage = $"""
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
            """;

        await context.EmitEventAsync(new()
        {
            Id = AccountOpeningEvents.WelcomePacketCreated,
            Data = mailMessage,
            Visibility = KernelProcessEventVisibility.Public,
        });
    }
}
