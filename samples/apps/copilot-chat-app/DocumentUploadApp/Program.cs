// Copyright (c) Microsoft. All rights reserved.

using System.CommandLine;
using System.Text;
using System.Text.Json;
using Microsoft.Identity.Client;

namespace SemanticKernel.Service.DocumentUploadApp;

public static class Program
{
    public static void Main(string[] args)
    {
        var appConfig = AppConfig.GetAppConfig();
        if (!AppConfig.Validate(appConfig))
        {
            Console.WriteLine("Failed to read appsettings.json.");
            return;
        }

        var fileOption = new Option<FileInfo>(
            name: "--file",
            description: "The file to upload for injection."
        );

        var rootCommand = new RootCommand(
            "Sample app that uploads a file to the Document Store."
        );
        rootCommand.AddOption(fileOption);
        rootCommand.SetHandler(
            async (file) =>
            {
                var userId = await AcquireUserIdAsync(appConfig!);
                if (userId != null)
                {
                    await UploadFileAsync(file, userId, appConfig!);
                }
            },
            fileOption
        );

        rootCommand.Invoke(args);
    }

    /// <summary>
    /// Acquires a user unique ID from Azure AD.
    /// </summary>
    private static async Task<string?> AcquireUserIdAsync(AppConfig appConfig)
    {
        Console.WriteLine("Requesting User Account ID...");

        string[] scopes = { "User.Read" };
        try
        {
            var app = PublicClientApplicationBuilder.Create(appConfig.ClientId)
                .WithRedirectUri(appConfig.RedirectUri)
                .Build();
            var result = await app.AcquireTokenInteractive(scopes).ExecuteAsync();
            var accounts = await app.GetAccountsAsync();
            if (!accounts.Any())
            {
                Console.WriteLine("No accounts found");
                return null;
            }
            return accounts.First().HomeAccountId.Identifier;
        }
        catch (MsalServiceException ex)
        {
            Console.WriteLine(ex.Message);
            return null;
        }
    }

    /// <summary>
    /// Invokes the DocumentQuerySkill to upload a file to the Document Store for parsing.
    /// </summary>
    private static async Task UploadFileAsync(FileInfo file, string userId, AppConfig appConfig)
    {
        if (!file.Exists)
        {
            Console.WriteLine($"File {file.FullName} does not exist.");
            return;
        }

        string skillName = "DocumentQuerySkill";
        string functionName = "ParseLocalFile";
        string commandPath = $"skills/{skillName}/functions/{functionName}/invoke";

        using StringContent jsonContent = new(
            JsonSerializer.Serialize(
                new
                {
                    input = file.FullName,
                    Variables = new List<KeyValuePair<string, string>> {
                        new KeyValuePair<string, string>("userId", userId)
                    }
                }
            ),
            Encoding.UTF8,
            "application/json"
        );

        HttpClientHandler clientHandler = new()
        {
            // Bypass the certificate check
            ServerCertificateCustomValidationCallback =
                (sender, cert, chain, sslPolicyErrors) => { return true; }
        };

        // Create a HttpClient intance and set the timeout to infinite since
        // large documents will take a while to parse.
        HttpClient httpClient = new(clientHandler) { BaseAddress = new Uri(appConfig.ServiceUri) };
        httpClient.Timeout = Timeout.InfiniteTimeSpan;

        Console.WriteLine("Uploading and parsing file...");
        try
        {
            using HttpResponseMessage response = await httpClient.PostAsync(
                commandPath,
                jsonContent
            );
            Console.WriteLine("Uploading and parsing successful.");
        }
        catch (HttpRequestException ex)
        {
            Console.WriteLine(ex.Message);
        }

        httpClient.Dispose();
        clientHandler.Dispose();
    }
}
