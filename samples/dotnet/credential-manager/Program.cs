// Copyright (c) Microsoft. All rights reserved.

using System.Net.Http.Headers;
using Microsoft.Extensions.Configuration;
using Microsoft.Identity.Client;

namespace CredentialManagerExample;

public delegate Task AuthorizationCallback(HttpRequestMessage request);

public sealed class Program
{
    private static readonly HttpClient s_httpClient = new();

    public static async Task Main()
    {
        // Using appsettings.json for our configuration settings
        IConfiguration configuration = new ConfigurationBuilder()
            .AddJsonFile(path: "appsettings.json", optional: false, reloadOnChange: true)
            .Build();

        PublicClientApplicationOptions appConfiguration = configuration.Get<PublicClientApplicationOptions>()
                                                          ?? throw new InvalidOperationException("Invalid configuration for public client application."); ;

        var scopes = configuration.GetSection("Scopes").Get<string[]>() ?? throw new InvalidOperationException("Invalid scopes.");
        
        using var requestMessage = new HttpRequestMessage(HttpMethod.Get, "https://graph.microsoft.com/beta/me/profile/");

        async Task localUserMSALAuthCallback(HttpRequestMessage requestMessage)
        {
            requestMessage.Headers.Authorization = new AuthenticationHeaderValue(
                scheme: "bearer",
                parameter: await new LocalUserMSALCredentialManager().GetTokenAsync(
                    appConfiguration.ClientId,
                    appConfiguration.TenantId,
                    scopes,
                    new Uri(appConfiguration.RedirectUri))
                );
        }
        HttpResponseMessage responseMessage = await AuthorizeAndSendRequestAsync(requestMessage, localUserMSALAuthCallback);

        Console.WriteLine(responseMessage.StatusCode + " " + responseMessage.ReasonPhrase);
        Console.WriteLine(await responseMessage.Content.ReadAsStringAsync());
    }

    public static async Task<HttpResponseMessage> AuthorizeAndSendRequestAsync(HttpRequestMessage requestMessage, AuthorizationCallback authCallback)
    {
        // Authorize the message before sending it, using the provided callback/delegate
        await authCallback(requestMessage);
        return await s_httpClient.SendAsync(requestMessage);
    }
}
