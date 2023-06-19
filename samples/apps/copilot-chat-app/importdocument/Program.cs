// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.CommandLine;
using System.IO;
using System.Linq;
using System.Net.Http;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Identity.Client;

namespace ImportDocument;

/// <summary>
/// This console app imports a file to the CopilotChat WebAPI document memory store.
/// </summary>
public static class Program
{
    public static void Main(string[] args)
    {
        var config = Config.GetConfig();
        if (!Config.Validate(config))
        {
            Console.WriteLine("Error: Failed to read appsettings.json.");
            return;
        }

        var fileOption = new Option<FileInfo>(name: "--file", description: "The file to import to document memory store.")
        {
            IsRequired = true
        };

        // TODO: UI to retrieve ChatID from the WebApp will be added in the future with multi-user support.
        var chatCollectionOption = new Option<Guid>(
            name: "--chat-id",
            description: "Save the extracted context to an isolated chat collection.",
            getDefaultValue: () => Guid.Empty
        );

        var rootCommand = new RootCommand(
            "This console app imports a file to the CopilotChat WebAPI's document memory store."
        )
        {
            fileOption, chatCollectionOption
        };

        rootCommand.SetHandler(async (file, chatCollectionId) =>
            {
                await UploadFileAsync(file, config!, chatCollectionId);
            },
            fileOption, chatCollectionOption
        );

        rootCommand.Invoke(args);
    }

    /// <summary>
    /// Acquires a user account from Azure AD.
    /// </summary>
    /// <param name="config">The App configuration.</param>
    /// <param name="setAccount">Sets the account to the first account found.</param>
    /// <param name="setAccessToken">Sets the access token to the first account found.</param>
    /// <returns>True if the user account was acquired.</returns>
    private static async Task<bool> AcquireUserAccountAsync(
        Config config,
        Action<IAccount> setAccount,
        Action<string> setAccessToken)
    {
        Console.WriteLine("Requesting User Account ID...");

        string[] scopes = { "User.Read" };
        try
        {
            var app = PublicClientApplicationBuilder.Create(config.ClientId)
                .WithRedirectUri(config.RedirectUri)
                .Build();
            var result = await app.AcquireTokenInteractive(scopes).ExecuteAsync();
            IEnumerable<IAccount>? accounts = await app.GetAccountsAsync();
            IAccount? first = accounts.FirstOrDefault();

            if (first is null)
            {
                Console.WriteLine("Error: No accounts found");
                return false;
            }

            setAccount(first);
            setAccessToken(result.AccessToken);
            return true;
        }
        catch (Exception ex) when (ex is MsalServiceException or MsalClientException)
        {
            Console.WriteLine($"Error: {ex.Message}");
            return false;
        }
    }

    /// <summary>
    /// Conditionally uploads a file to the Document Store for parsing.
    /// </summary>
    /// <param name="file">The file to upload for injection.</param>
    /// <param name="config">Configuration.</param>
    /// <param name="chatCollectionId">Save the extracted context to an isolated chat collection.</param>
    private static async Task UploadFileAsync(FileInfo file, Config config, Guid chatCollectionId)
    {
        if (!file.Exists)
        {
            Console.WriteLine($"File {file.FullName} does not exist.");
            return;
        }

        IAccount? userAccount = null;
        string? accessToken = null;

        if (await AcquireUserAccountAsync(config, v => { userAccount = v; }, v => { accessToken = v; }) == false)
        {
            Console.WriteLine("Error: Failed to acquire user account.");
            return;
        }
        Console.WriteLine($"Successfully acquired User ID. Continuing...");

        using var fileContent = new StreamContent(file.OpenRead());
        using var formContent = new MultipartFormDataContent
        {
            { fileContent, "formFile", file.Name }
        };

        var userId = userAccount!.HomeAccountId.Identifier;
        var userName = userAccount.Username;
        using var userIdContent = new StringContent(userId);
        using var userNameContent = new StringContent(userName);
        formContent.Add(userIdContent, "userId");
        formContent.Add(userNameContent, "userName");

        if (chatCollectionId != Guid.Empty)
        {
            Console.WriteLine($"Uploading and parsing file to chat {chatCollectionId}...");
            using var chatScopeContent = new StringContent("Chat");
            using var chatCollectionIdContent = new StringContent(chatCollectionId.ToString());
            formContent.Add(chatScopeContent, "documentScope");
            formContent.Add(chatCollectionIdContent, "chatId");

            // Calling UploadAsync here to make sure disposable objects are still in scope.
            await UploadAsync(formContent, accessToken!, config);
        }
        else
        {
            Console.WriteLine("Uploading and parsing file to global collection...");
            using var globalScopeContent = new StringContent("Global");
            formContent.Add(globalScopeContent, "documentScope");

            // Calling UploadAsync here to make sure disposable objects are still in scope.
            await UploadAsync(formContent, accessToken!, config);
        }
    }

    /// <summary>
    /// Sends a POST request to the Document Store to upload a file for parsing.
    /// </summary>
    /// <param name="multipartFormDataContent">The multipart form data content to send.</param>
    /// <param name="config">Configuration.</param>
    private static async Task UploadAsync(
        MultipartFormDataContent multipartFormDataContent,
        string accessToken,
        Config config)
    {
        // Create a HttpClient instance and set the timeout to infinite since
        // large documents will take a while to parse.
        using HttpClientHandler clientHandler = new()
        {
            CheckCertificateRevocationList = true
        };
        using HttpClient httpClient = new(clientHandler)
        {
            Timeout = Timeout.InfiniteTimeSpan
        };
        // Add required properties to the request header.
        httpClient.DefaultRequestHeaders.Add("Authorization", $"Bearer {accessToken}");
        if (!string.IsNullOrEmpty(config.ApiKey))
        {
            httpClient.DefaultRequestHeaders.Add("x-sk-api-key", config.ApiKey);
        }

        try
        {
            using HttpResponseMessage response = await httpClient.PostAsync(
                new Uri(new Uri(config.ServiceUri), "importDocument"),
                multipartFormDataContent
            );

            if (!response.IsSuccessStatusCode)
            {
                Console.WriteLine($"Error: {response.StatusCode} {response.ReasonPhrase}");
                Console.WriteLine(await response.Content.ReadAsStringAsync());
                return;
            }

            Console.WriteLine("Uploading and parsing successful.");
        }
        catch (HttpRequestException ex)
        {
            Console.WriteLine($"Error: {ex.Message}");
        }
    }
}
