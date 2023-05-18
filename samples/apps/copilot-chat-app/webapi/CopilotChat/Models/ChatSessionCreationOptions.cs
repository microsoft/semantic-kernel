// Copyright (c) Microsoft. All rights reserved.

using System.ComponentModel.DataAnnotations;

namespace SemanticKernel.Service.CopilotChat.Models;

/// <summary>
/// A chat session creation option.
/// </summary>
public record struct ChatSessionCreationOptions([Required] string Title);
