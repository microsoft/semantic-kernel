// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;

namespace Microsoft.SemanticKernel.Skills.MsGraph.Models;

/// <summary>
/// Model for an email message.
/// </summary>
public class EmailMessage
{
    /// <summary>
    /// From email address.
    /// </summary>
    public EmailAddress? From { get; set; }

    /// <summary>
    /// Email recipients.
    /// </summary>
    public IEnumerable<EmailAddress>? Recipients { get; set; }

    /// <summary>
    /// Email cc recipients.
    /// </summary>
    public IEnumerable<EmailAddress>? CcRecipients { get; set; }

    /// <summary>
    /// Email bcc recipients.
    /// </summary>
    public IEnumerable<EmailAddress>? BccRecipients { get; set; }

    /// <summary>
    /// Email subject.
    /// </summary>
    public string? Subject { get; set; }

    /// <summary>
    /// Email body.
    /// </summary>
    public string? Body { get; set; }

    /// <summary>
    /// A shortened form of the body.
    /// </summary>
    public string? BodyPreview { get; set; }

    /// <summary>
    /// True if the email is read, otherwise false.
    /// </summary>
    public bool? IsRead { get; set; }

    /// <summary>
    /// Email received date/time.
    /// </summary>
    public DateTimeOffset? ReceivedDateTime { get; set; }

    /// <summary>
    /// Email sent date/time.
    /// </summary>
    public DateTimeOffset? SentDateTime { get; set; }
}
