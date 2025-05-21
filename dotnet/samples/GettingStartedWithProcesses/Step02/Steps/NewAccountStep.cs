// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;
using Step02.Models;

namespace Step02.Steps;

/// <summary>
/// Mock step that emulates the creation of a new account that triggers other services after a new account id creation
/// </summary>
public class NewAccountStep : KernelProcessStep
{
    public static class ProcessStepFunctions
    {
        public const string CreateNewAccount = nameof(CreateNewAccount);
    }

    [KernelFunction(ProcessStepFunctions.CreateNewAccount)]
    public async Task CreateNewAccountAsync(KernelProcessStepContext context, bool previousCheckSucceeded, NewCustomerForm customerDetails, List<ChatMessageContent> interactionTranscript, Kernel _kernel)
    {
        // Placeholder for a call to API to create new account for user
        var accountId = new Guid();
        AccountDetails accountDetails = new()
        {
            UserDateOfBirth = customerDetails.UserDateOfBirth,
            UserFirstName = customerDetails.UserFirstName,
            UserLastName = customerDetails.UserLastName,
            UserId = customerDetails.UserId,
            UserPhoneNumber = customerDetails.UserPhoneNumber,
            UserState = customerDetails.UserState,
            UserEmail = customerDetails.UserEmail,
            AccountId = accountId,
            AccountType = AccountType.PrimeABC,
        };

        Console.WriteLine($"[ACCOUNT CREATION] New Account {accountId} created");

        await context.EmitEventAsync(new()
        {
            Id = AccountOpeningEvents.NewMarketingRecordInfoReady,
            Data = new MarketingNewEntryDetails
            {
                AccountId = accountId,
                Name = $"{customerDetails.UserFirstName} {customerDetails.UserLastName}",
                PhoneNumber = customerDetails.UserPhoneNumber,
                Email = customerDetails.UserEmail,
            }
        });

        await context.EmitEventAsync(new()
        {
            Id = AccountOpeningEvents.CRMRecordInfoReady,
            Data = new AccountUserInteractionDetails
            {
                AccountId = accountId,
                UserInteractionType = UserInteractionType.OpeningNewAccount,
                InteractionTranscript = interactionTranscript
            }
        });

        await context.EmitEventAsync(new()
        {
            Id = AccountOpeningEvents.NewAccountDetailsReady,
            Data = accountDetails,
        });
    }
}
