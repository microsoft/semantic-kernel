// Copyright (c) Microsoft. All rights reserved.

using System.Threading.Tasks;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Http;
using Microsoft.AspNetCore.Routing;
using SemanticKernel.Service.CopilotChat.Storage;

namespace SemanticKernel.Service.Auth;

/// <summary>
/// Class implementing "authorization" that validates the user has access to a chat.
/// </summary>
public class ChatOwnerAuthorizationHandler : AuthorizationHandler<ChatOwnerRequirement, HttpContext>
{
    private readonly IAuthInfo _authInfo;
    private readonly ChatSessionRepository _chatSessionRepository;

    /// <summary>
    /// Constructor
    /// </summary>
    public ChatOwnerAuthorizationHandler(
        IAuthInfo authInfo,
        ChatSessionRepository chatSessionRepository) : base()
    {
        this._authInfo = authInfo;
        this._chatSessionRepository = chatSessionRepository;
    }

    protected override async Task HandleRequirementAsync(
        AuthorizationHandlerContext context,
        ChatOwnerRequirement requirement,
        HttpContext resource)
    {
        string? chatId = resource.GetRouteValue("chatId")?.ToString();
        if (chatId == null)
        {
            // delegate to downstream validation
            context.Succeed(requirement);
            return;
        }

        var session = await this._chatSessionRepository.FindByIdAsync(chatId);
        if (session == null)
        {
            // delegate to downstream validation
            context.Succeed(requirement);
            return;
        }

        if (session.UserId != this._authInfo.UserId)
        {
            context.Fail(new AuthorizationFailureReason(this, "User does not have access to the requested chat."));
        }
    }
}
