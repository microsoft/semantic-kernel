// Copyright (c) Microsoft. All rights reserved.

namespace Step02.Models;

/// <summary>
/// Represents the data structure for a form capturing details of a new customer, including personal information, contact details, account id and account type.<br/>
/// Class used in <see cref="Step02a_AccountOpening"/>, <see cref="Step02b_AccountOpening"/> samples
/// </summary>
public class AccountDetails : NewCustomerForm
{
    public Guid AccountId { get; set; }
    public AccountType AccountType { get; set; }
}

public enum AccountType
{
    PrimeABC,
    Other,
}
