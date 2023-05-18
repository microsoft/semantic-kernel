// Copyright (c) Microsoft. All rights reserved.

using Microsoft.AspNetCore.Authorization;

namespace SemanticKernel.Service.Auth;

/// <summary>
/// Used to require the chat to be owned by the authenticated user.
/// </summary>
public class ChatOwnerRequirement : IAuthorizationRequirement
{
}
