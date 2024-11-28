// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;
using Step02.Steps;

namespace Step02.Utils;
public static class AccountOpeningAsserts
{
    private const string ExpectedAccountSuccessMessage = """
        Dear John Contoso
        We are thrilled to inform you that you have successfully created a new PRIME ABC Account with us!
        
        Account Details:
        Account Number: 00000000-0000-0000-0000-000000000000
        Account Type: PrimeABC
        
        Please keep this confidential for security purposes.
        
        Here is the contact information we have in file:
        
        Email: john.contoso@contoso.com
        Phone: (222)-222-1234
        
        Thank you for opening an account with us!
        """;

    private const string ExpectedFailedAccountDueFraudDetectionMessage = """
        We regret to inform you that we found some inconsistent details regarding the information you provided regarding the new account of the type PRIME ABC you applied.
        """;
    private const string ExpectedFailedAccountDueCreditCheckMessage = """
        We regret to inform you that your credit score of 500 is insufficient to apply for an account of the type PRIME ABC
        """;

    private static void AssertMailerStepStateLastMessage(KernelProcess processInfo, string stepName, string? expectedLastMessage)
    {
        KernelProcessStepInfo? stepInfo = processInfo.Steps.FirstOrDefault(s => s.State.Name == stepName);
        Assert.NotNull(stepInfo);
        var outputStepResult = stepInfo.State as KernelProcessStepState<MailServiceState>;
        Assert.NotNull(outputStepResult?.State);
        Assert.Equal(expectedLastMessage, outputStepResult.State.LastMessageSent);
    }

    public static void AssertAccountOpeningSuccessMailMessage(KernelProcess processInfo, string stepName)
    {
        AssertMailerStepStateLastMessage(processInfo, stepName, ExpectedAccountSuccessMessage);
    }

    public static void AssertAccountOpeningFailDueFraudMailMessage(KernelProcess processInfo, string stepName)
    {
        AssertMailerStepStateLastMessage(processInfo, stepName, ExpectedFailedAccountDueFraudDetectionMessage);
    }

    public static void AssertAccountOpeningFailDueCreditScoreMailMessage(KernelProcess processInfo, string stepName)
    {
        AssertMailerStepStateLastMessage(processInfo, stepName, ExpectedFailedAccountDueCreditCheckMessage);
    }
}
