// Copyright (c) Microsoft. All rights reserved.

using System.Net.Http;

namespace RestSkills.Authentication;

/// <summary>
/// Interface for authentication handler.
/// </summary>
internal interface IAuthenticationHandler
{
    /// <summary>
    /// Adds authentication information to the HTTP request message.
    /// </summary>
    /// <param name="requestMessage">The request message.</param>
    void AddAuthenticationData(HttpRequestMessage requestMessage);
}
