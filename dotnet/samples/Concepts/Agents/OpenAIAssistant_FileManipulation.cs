<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
<<<<<<< main
﻿// Copyright (c) Microsoft. All rights reserved.
=======
// Copyright (c) Microsoft. All rights reserved.
using System.Text;
>>>>>>> origin/PR
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======

// Copyright (c) Microsoft. All rights reserved.
using System.Text;
>>>>>>> main
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Agents.OpenAI;
using Microsoft.SemanticKernel.ChatCompletion;
using OpenAI.Files;
using Resources;

namespace Agents;

/// <summary>
/// Demonstrate using code-interpreter to manipulate and generate csv files with <see cref="OpenAIAssistantAgent"/> .
/// </summary>
public class OpenAIAssistant_FileManipulation(ITestOutputHelper output) : BaseAgentsTest(output)
{
    [Fact]
    public async Task RunAsync()
    public async Task AnalyzeCSVFileUsingOpenAIAssistantAgentAsync()
    {
        OpenAIClientProvider provider = this.GetClientProvider();

<<<<<<< Updated upstream
<<<<<<< Updated upstream
        FileClient fileClient = provider.Client.GetFileClient();

        OpenAIFileInfo uploadFile =
=======
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
        FileClient fileClient = provider.Client.GetFileClient();

        OpenAIFileInfo uploadFile =
=======
        OpenAIFileClient fileClient = provider.Client.GetOpenAIFileClient();

        OpenAIFile uploadFile =
>>>>>>> main
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
            await fileClient.UploadFileAsync(
                new BinaryData(await EmbeddedResource.ReadAllAsync("sales.csv")!),
                "sales.csv",
                FileUploadPurpose.Assistants);

        // Define the agent
        OpenAIAssistantAgent agent =
            await OpenAIAssistantAgent.CreateAsync(
<<<<<<< Updated upstream
<<<<<<< Updated upstream
                kernel: new(),
                provider,
                new(this.Model)
=======
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
                kernel: new(),
                provider,
                new(this.Model)
=======
                provider,
                definition: new OpenAIAssistantDefinition(this.Model)
                kernel: new(),
                provider,
                new(this.Model)
                provider,
                definition: new OpenAIAssistantDefinition(this.Model)
>>>>>>> main
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
                {
                    EnableCodeInterpreter = true,
                    CodeInterpreterFileIds = [uploadFile.Id],
                    Metadata = AssistantSampleMetadata,
<<<<<<< Updated upstream
<<<<<<< Updated upstream
                });
=======
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
                });
=======
                },
                kernel: new Kernel());
                });
                },
                kernel: new Kernel());
>>>>>>> main
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes

        // Create a chat for agent interaction.
        AgentGroupChat chat = new();
        var chat = new AgentGroupChat();

        // Respond to user input
        try
        {
            await InvokeAgentAsync("Which segment had the most sales?");
            await InvokeAgentAsync("List the top 5 countries that generated the most profit.");
            await InvokeAgentAsync("Create a tab delimited file report of profit by each country per month.");
        }
        finally
        {
            await agent.DeleteAsync();
            await fileClient.DeleteFileAsync(uploadFile.Id);
        }

        // Local function to invoke agent and display the conversation messages.
        async Task InvokeAgentAsync(string input)
        {
            ChatMessageContent message = new(AuthorRole.User, input);
            chat.AddChatMessage(new(AuthorRole.User, input));
            this.WriteAgentChatMessage(message);

            await foreach (ChatMessageContent response in chat.InvokeAsync(agent))
            {
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
<<<<<<< main
                this.WriteAgentChatMessage(response);
                await this.DownloadResponseContentAsync(fileClient, response);
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
                this.WriteAgentChatMessage(response);
                await this.DownloadResponseContentAsync(fileClient, response);
>>>>>>> main
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
                Console.WriteLine($"# {content.Role} - {content.AuthorName ?? "*"}: '{content.Content}'");

                foreach (AnnotationContent annotation in content.Items.OfType<AnnotationContent>())
            await foreach (var content in chat.InvokeAsync(agent))
            {
                Console.WriteLine($"# {content.Role} - {content.AuthorName ?? "*"}: '{content.Content}'");

                foreach (var annotation in content.Items.OfType<AnnotationContent>())
                {
                    Console.WriteLine($"\n* '{annotation.Quote}' => {annotation.FileId}");
                    BinaryContent fileContent = await fileService.GetFileContentAsync(annotation.FileId!);
                    byte[] byteContent = fileContent.Data?.ToArray() ?? [];
                    Console.WriteLine(Encoding.Default.GetString(byteContent));
                }
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> origin/PR
=======
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
>>>>>>> origin/PR
=======
                this.WriteAgentChatMessage(response);
                await this.DownloadResponseContentAsync(fileClient, response);
>>>>>>> main
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
            }
        }
    }
}
