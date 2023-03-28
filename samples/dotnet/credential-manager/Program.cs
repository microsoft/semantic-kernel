// Copyright (c) Microsoft. All rights reserved.

using System.Net.Http.Headers;
using Microsoft.Extensions.Configuration;
using Microsoft.Identity.Client;

namespace CredentialManagerExample;

public sealed class Program
{
    public static async Task Main()
    {
        // Using appsettings.json for our configuration settings
        IConfiguration configuration = new ConfigurationBuilder()
            .AddJsonFile(path: "appsettings.json", optional: false, reloadOnChange: true)
            .Build();

        PublicClientApplicationOptions appConfiguration = configuration.Get<PublicClientApplicationOptions>()
                                                          ?? throw new InvalidOperationException("Invalid configuration for public client application."); ;

        var scopes = configuration.GetSection("Scopes").Get<string[]>() ?? throw new InvalidOperationException("Invalid scopes.");
        
        var authProvider = CreateAuthenticationProvider(
            new LocalUserMSALCredentialManager(),
            appConfiguration.ClientId,
            appConfiguration.TenantId,
            scopes,
            new Uri(appConfiguration.RedirectUri)
            );

        // Create and authenticate request
        using var httpClient = new HttpClient();
        using var requestMessage = new HttpRequestMessage(HttpMethod.Get, "https://graph.microsoft.com/beta/me/profile/");
        await authProvider.AuthenticateRequestAsync(requestMessage);

        // Send request
        HttpResponseMessage responseMessage = await httpClient.SendAsync(requestMessage);
        Console.WriteLine(responseMessage.StatusCode + " " + responseMessage.ReasonPhrase);
        Console.WriteLine(await responseMessage.Content.ReadAsStringAsync());
    }

    private static DelegateAuthenticationProvider CreateAuthenticationProvider(
        LocalUserMSALCredentialManager credentialManager,
        string clientId,
        string tenantId,
        string[] scopes,
        Uri redirectUri)
        => new(
            async (requestMessage) =>
            {
                requestMessage.Headers.Authorization = new AuthenticationHeaderValue(
                    scheme: "bearer",
                    parameter: await credentialManager.GetTokenAsync(
                        clientId,
                        tenantId,
                        scopes,
                        redirectUri));
            });
}
