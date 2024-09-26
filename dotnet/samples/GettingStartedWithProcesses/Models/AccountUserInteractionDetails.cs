// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;

namespace Models;

public class AccountUserInteractionDetails
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
