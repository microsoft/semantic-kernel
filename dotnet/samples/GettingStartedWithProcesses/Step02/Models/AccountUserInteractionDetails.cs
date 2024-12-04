// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;

namespace Step02.Models;

/// <summary>
/// Represents the details of interactions between a user and service, including a unique identifier for the account,
/// a transcript of conversation with the user, and the type of user interaction.<br/>
/// Class used in <see cref="Step02a_AccountOpening"/>, <see cref="Step02b_AccountOpening"/> samples
/// </summary>
public record AccountUserInteractionDetails
{
    public Guid AccountId { get; set; }

    public List<ChatMessageContent> InteractionTranscript { get; set; } = [];

    public UserInteractionType UserInteractionType { get; set; }
}

public enum UserInteractionType
{
    Complaint,
    AccountInfoRequest,
    OpeningNewAccount
}
