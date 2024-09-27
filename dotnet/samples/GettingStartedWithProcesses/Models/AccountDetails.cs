// Copyright (c) Microsoft. All rights reserved.

namespace Models;

/// <summary>
/// Represents the data structure for a form capturing details of a new customer, including personal information, contact details, account id and account type.<br/>
/// Model used in Step02_AccountOpening.cs samples
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
