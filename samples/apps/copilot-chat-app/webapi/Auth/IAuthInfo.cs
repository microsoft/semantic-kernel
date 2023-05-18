// Copyright (c) Microsoft. All rights reserved.

namespace SemanticKernel.Service.Auth;

public interface IAuthInfo
{
    /// <summary>
    /// The authenticated user's unique ID.
    /// </summary>
    public string UserId { get; }
}
