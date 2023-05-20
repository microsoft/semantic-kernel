// Copyright (c) Microsoft. All rights reserved.

using System.ComponentModel.DataAnnotations;
using SemanticKernel.Service.Models;
using SemanticKernel.Service.Options;

namespace SemanticKernel.Service.CopilotChat.Models;

public class ChatAsk : Ask
{
    [Required, NotEmptyOrWhitespace]
    public override string Input { get => base.Input; set => base.Input = value; }
}
