// Copyright (c) Microsoft. All rights reserved.

namespace Models;

/// <summary>
/// Holds details for a new entry in a marketing database, including the account identifier, contact name, phone number, and email address.<br/>
/// Model used in Step02_AccountOpening.cs samples
/// </summary>
public class MarketingNewEntryDetails
{
    public Guid AccountId { get; set; }

    public string Name { get; set; }

    public string PhoneNumber { get; set; }

    public string Email { get; set; }
}
