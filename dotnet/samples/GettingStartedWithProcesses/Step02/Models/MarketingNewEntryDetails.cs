// Copyright (c) Microsoft. All rights reserved.

namespace Step02.Models;

/// <summary>
/// Holds details for a new entry in a marketing database, including the account identifier, contact name, phone number, and email address.<br/>
/// Class used in <see cref="Step02a_AccountOpening"/>, <see cref="Step02b_AccountOpening"/> samples
/// </summary>
public record MarketingNewEntryDetails
{
    public Guid AccountId { get; set; }

    public string Name { get; set; }

    public string PhoneNumber { get; set; }

    public string Email { get; set; }
}
