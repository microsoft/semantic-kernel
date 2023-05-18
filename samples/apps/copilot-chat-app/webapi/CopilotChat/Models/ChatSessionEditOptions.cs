// Copyright (c) Microsoft. All rights reserved.

using System.ComponentModel.DataAnnotations;

namespace SemanticKernel.Service.CopilotChat.Models;

/// <summary>
/// A chat session edit option.
/// </summary>
public record struct ChatSessionEditOptions([Required] string Title);
