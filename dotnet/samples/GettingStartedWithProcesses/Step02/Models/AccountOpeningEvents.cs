// Copyright (c) Microsoft. All rights reserved.
namespace Step02.Models;

/// <summary>
/// Processes Events related to Account Opening scenarios.<br/>
/// Class used in <see cref="Step02a_AccountOpening"/>, <see cref="Step02b_AccountOpening"/> samples
/// </summary>
public static class AccountOpeningEvents
{
    public static readonly string StartProcess = nameof(StartProcess);

    public static readonly string NewCustomerFormWelcomeMessageComplete = nameof(NewCustomerFormWelcomeMessageComplete);
    public static readonly string NewCustomerFormCompleted = nameof(NewCustomerFormCompleted);
    public static readonly string NewCustomerFormNeedsMoreDetails = nameof(NewCustomerFormNeedsMoreDetails);
    public static readonly string CustomerInteractionTranscriptReady = nameof(CustomerInteractionTranscriptReady);

    public static readonly string NewAccountVerificationCheckPassed = nameof(NewAccountVerificationCheckPassed);

    public static readonly string CreditScoreCheckApproved = nameof(CreditScoreCheckApproved);
    public static readonly string CreditScoreCheckRejected = nameof(CreditScoreCheckRejected);

    public static readonly string FraudDetectionCheckPassed = nameof(FraudDetectionCheckPassed);
    public static readonly string FraudDetectionCheckFailed = nameof(FraudDetectionCheckFailed);

    public static readonly string NewAccountDetailsReady = nameof(NewAccountDetailsReady);

    public static readonly string NewMarketingRecordInfoReady = nameof(NewMarketingRecordInfoReady);
    public static readonly string NewMarketingEntryCreated = nameof(NewMarketingEntryCreated);
    public static readonly string CRMRecordInfoReady = nameof(CRMRecordInfoReady);
    public static readonly string CRMRecordInfoEntryCreated = nameof(CRMRecordInfoEntryCreated);

    public static readonly string WelcomePacketCreated = nameof(WelcomePacketCreated);

    public static readonly string MailServiceSent = nameof(MailServiceSent);
}
