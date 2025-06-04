// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading;
using System.Threading.Tasks;
using Azure.Core;

namespace SemanticKernel.Agents.UnitTests;

internal sealed class FakeTokenCredential : TokenCredential
{
    /// <inheritdoc/>
    public override AccessToken GetToken(TokenRequestContext requestContext, CancellationToken cancellationToken)
    {
        return new AccessToken("fakeToken", DateTimeOffset.Now.AddHours(1));
    }

    /// <inheritdoc/>
    public override ValueTask<AccessToken> GetTokenAsync(TokenRequestContext requestContext, CancellationToken cancellationToken)
    {
        return new ValueTask<AccessToken>(new AccessToken("fakeToken", DateTimeOffset.Now.AddHours(1)));
    }
}
