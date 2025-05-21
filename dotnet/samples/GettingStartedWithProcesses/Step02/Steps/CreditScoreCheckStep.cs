// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;
using Step02.Models;

namespace Step02.Steps;

/// <summary>
/// Mock step that emulates User Credit Score check, based on the date of birth the score will be enough or insufficient
/// </summary>
public class CreditScoreCheckStep : KernelProcessStep
{
    public static class ProcessStepFunctions
    {
        public const string DetermineCreditScore = nameof(DetermineCreditScore);
    }

    private const int MinCreditScore = 600;

    [KernelFunction(ProcessStepFunctions.DetermineCreditScore)]
    public async Task DetermineCreditScoreAsync(KernelProcessStepContext context, NewCustomerForm customerDetails, Kernel _kernel)
    {
        // Placeholder for a call to API to validate credit score with customerDetails
        var creditScore = customerDetails.UserDateOfBirth == "02/03/1990" ? 700 : 500;

        if (creditScore >= MinCreditScore)
        {
            Console.WriteLine("[CREDIT CHECK] Credit Score Check Passed");
            await context.EmitEventAsync(new() { Id = AccountOpeningEvents.CreditScoreCheckApproved, Data = true });
            return;
        }
        Console.WriteLine("[CREDIT CHECK] Credit Score Check Failed");
        await context.EmitEventAsync(new()
        {
            Id = AccountOpeningEvents.CreditScoreCheckRejected,
            Data = $"We regret to inform you that your credit score of {creditScore} is insufficient to apply for an account of the type PRIME ABC",
            Visibility = KernelProcessEventVisibility.Public,
        });
    }
}
