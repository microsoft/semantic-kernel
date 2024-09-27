// Copyright (c) Microsoft. All rights reserved.
namespace Events;

/// <summary>
/// Processes Events related to Account Opening scenarios.<br/>
/// Class used in Step02_AccountOpening.cs samples
/// </summary>
public static class AccountOpeningEvents
{
    public static readonly string NewCustomerFormWelcomeMessageComplete = "newCustomerWelcomeComplete";
    public static readonly string NewCustomerFormCompleted = "newCustomerFormComplete";
    public static readonly string NewCustomerFormNeedsMoreDetails = "newCustomerFormNeedsMoreDetails";
    public static readonly string CustomerInteractionTranscriptReady = "customerInteractionTranscriptReady";

    public static readonly string CreditScoreCheckApproved = "creditScoreCheckApproved";
    public static readonly string CreditScoreCheckRejected = "creditScoreCheckRejected";

    public static readonly string FraudDetectionCheckPassed = "fraudDetectionCheckPassed";
    public static readonly string FraudDetectionCheckFailed = "fraudDetectionCheckFailed";

    public static readonly string NewAccountDetailsReady = "newAccountDetailsReady";

    public static readonly string NewMarketingRecordInfoReady = "newMarketingRecordInfoReady";
    public static readonly string NewMarketingEntryCreated = "newMarketingEntryCreated";
    public static readonly string CRMRecordInfoReady = "crmRecordInfoReady";
    public static readonly string CRMRecordInfoEntryCreated = "crmRecordInfoEntryCreated";

    public static readonly string WelcomePacketCreated = "welcomePacketCreated";

    public static readonly string MailServiceSent = "mailServiceSent";
}
