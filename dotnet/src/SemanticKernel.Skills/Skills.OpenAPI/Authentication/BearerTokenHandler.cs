// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Net.Http;
using System.Net.Http.Headers;

namespace RestSkills.Authentication;

/// <summary>
/// Add Bearer token to the headers of request message.
/// This is temporary implementation of toke provider used during prototyping.
/// It'll be replaced by proper authentication mechanism when it's ready.
/// </summary>
internal class BearerTokenHandler : IAuthenticationHandler
{
    public void AddAuthenticationData(HttpRequestMessage requestMessage)
    {
        //Example of auth routing - adding auth info to the Http request message based on host name.
        var host = requestMessage.RequestUri.Host;

        if (host.Contains(".vault.azure.net", StringComparison.InvariantCultureIgnoreCase))
        {
            //PLEASE MAKE SURE NO TOKEN IS CHECKED IN.
            requestMessage.Headers.Authorization = new AuthenticationHeaderValue("Bearer", "<token>");
        }
    }
}
