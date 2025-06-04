// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel.Plugins.MsGraph.Models;

/// <summary>
/// Model for an email address.
/// </summary>
public class EmailAddress
{
    /// <summary>
    /// Name associated with email address.
    /// </summary>
    public string? Name { get; set; }

    /// <summary>
    /// Email address
    /// </summary>
    public string? Address { get; set; }
}
