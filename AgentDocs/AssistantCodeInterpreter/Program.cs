// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Threading.Tasks;
using Azure.Identity;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents.OpenAI;
using Microsoft.SemanticKernel.ChatCompletion;
using OpenAI.Files;

namespace AgentsSample;

/*****************
 * SETUP:
 * dotnet user-secrets set "OpenAISettings:ApiKey" "<api-key>"
 * dotnet user-secrets set "OpenAISettings:ChatModel" "gpt-4o"
 * dotnet user-secrets set "AzureOpenAISettings:Endpoint" "https://lightspeed-team-shared-openai-eastus.openai.azure.com/"
 * dotnet user-secrets set "AzureOpenAISettings:ChatModelDeployment" "gpt-4o"

 * INPUTS:
 * 1. Compare the files to determine the number of countries do not have a state or province defined compared to the total count
 * 2. Create a table for countries with state or province defined.  Include the count of states or provinces and the total population
 * 3. Provide a bar chart for countries whose names start with the same letter and sort the x axis by highest count to lowest (include all countries)
 *****************/

public static class Program
{
    public static async Task Main()
    {
        // Load configuration from environment variables or user secrets.
        Settings settings = new();

        OpenAIClientProvider clientProvider =
            //OpenAIClientProvider.ForOpenAI(settings.OpenAI.ApiKey); // Alternative (mention in docs)
            OpenAIClientProvider.ForAzureOpenAI(new AzureCliCredential(), new Uri(settings.AzureOpenAI.Endpoint));

        Console.WriteLine("Uploading files...");
        FileClient fileClient = clientProvider.Client.GetFileClient();
        OpenAIFileInfo fileDataCountryDetail = await fileClient.UploadFileAsync("PopulationByAdmin1.csv", FileUploadPurpose.Assistants);
        OpenAIFileInfo fileDataCountryList = await fileClient.UploadFileAsync("PopulationByCountry.csv", FileUploadPurpose.Assistants);

        Console.WriteLine("Defining agent...");
        OpenAIAssistantAgent agent =
            await OpenAIAssistantAgent.CreateAsync(
                clientProvider,
                new OpenAIAssistantDefinition(settings.AzureOpenAI.ChatModelDeployment)
                {
                    Name = "SampleAssistantAgent",
                    Instructions =
                        """
                        Analyze the available data to provide an answer to the user's question.
                        Always format response using markdown.
                        Always include a numerical index that starts at 1 for any lists or tables.
                        Always sort lists in ascending order.
                        """,
                    EnableCodeInterpreter = true,
                    CodeInterpreterFileIds = [fileDataCountryList.Id, fileDataCountryDetail.Id],
                },
                new Kernel());

        Console.WriteLine("Creating thread...");
        string threadId = await agent.CreateThreadAsync();

        Console.WriteLine("Ready!");

        try
        {
            bool isComplete = false;
            List<string> fileIds = [];
            do
            {
                Console.WriteLine();
                Console.Write("> ");
                string input = Console.ReadLine();
                if (string.IsNullOrWhiteSpace(input))
                {
                    continue;
                }
                if (input.Trim().Equals("EXIT", StringComparison.OrdinalIgnoreCase))
                {
                    isComplete = true;
                    break;
                }

                await agent.AddChatMessageAsync(threadId, new ChatMessageContent(AuthorRole.User, input));

                Console.WriteLine();

                bool isCode = false;
                await foreach (StreamingChatMessageContent response in agent.InvokeStreamingAsync(threadId))
                {
                    if (isCode != (response.Metadata?.ContainsKey(OpenAIAssistantAgent.CodeInterpreterMetadataKey) ?? false))
                    {
                        Console.WriteLine();
                        isCode = !isCode;
                    }

                    // Display response.
                    Console.Write($"{response.Content}");

                    // Capture file IDs for downloading.
                    fileIds.AddRange(response.Items.OfType<StreamingFileReferenceContent>().Select(item => item.FileId));
                }
                Console.WriteLine();

                // Download any files referenced in the response.
                await DownloadResponseImageAsync(fileClient, fileIds);
                fileIds.Clear();

            } while (!isComplete);
        }
        finally
        {
            Console.WriteLine();
            Console.WriteLine("Cleaning-up...");
            await Task.WhenAll(
                [
                    agent.DeleteThreadAsync(threadId),
                    agent.DeleteAsync(),
                    fileClient.DeleteFileAsync(fileDataCountryList.Id),
                    fileClient.DeleteFileAsync(fileDataCountryDetail.Id),
                ]);
        }
    }

    private static async Task DownloadResponseImageAsync(FileClient client, ICollection<string> fileIds)
    {
        if (fileIds.Count > 0)
        {
            Console.WriteLine();
            foreach (string fileId in fileIds)
            {
                await DownloadFileContentAsync(client, fileId, launchViewer: true);
            }
        }
    }

    private static async Task DownloadFileContentAsync(FileClient client, string fileId, bool launchViewer = false)
    {
        OpenAIFileInfo fileInfo = client.GetFile(fileId);
        if (fileInfo.Purpose == OpenAIFilePurpose.AssistantsOutput)
        {
            string filePath =
                Path.Combine(
                    Path.GetTempPath(),
                    Path.GetFileName(Path.ChangeExtension(fileInfo.Filename, ".png")));

            BinaryData content = await client.DownloadFileAsync(fileId);
            await using FileStream fileStream = new(filePath, FileMode.CreateNew);
            await content.ToStream().CopyToAsync(fileStream);
            Console.WriteLine($"File saved to: {filePath}.");

            if (launchViewer)
            {
                Process.Start(
                    new ProcessStartInfo
                    {
                        FileName = "cmd.exe",
                        Arguments = $"/C start {filePath}"
                    });
            }
        }
    }
}
