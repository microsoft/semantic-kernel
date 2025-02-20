// Copyright (c) Microsoft. All rights reserved.

using System.ClientModel;
using System.Diagnostics;
using Azure.Identity;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Agents.OpenAI;
using OpenAI;
using OpenAI.Assistants;
using OpenAI.Files;

/// <summary>
/// Base class for samples that demonstrate the usage of <see cref="OpenAIAssistantAgent"/>.
/// </summary>
public abstract class BaseAssistantTest : BaseAgentsTest<OpenAIClient>
{
    protected BaseAssistantTest(ITestOutputHelper output) : base(output)
    {
        this.Client =
            this.UseOpenAIConfig ?
                OpenAIAssistantAgent.CreateOpenAIClient(new ApiKeyCredential(this.ApiKey ?? throw new ConfigurationNotFoundException("OpenAI:ApiKey"))) :
                !string.IsNullOrWhiteSpace(this.ApiKey) ?
                    OpenAIAssistantAgent.CreateAzureOpenAIClient(new ApiKeyCredential(this.ApiKey), new Uri(this.Endpoint!)) :
                    OpenAIAssistantAgent.CreateAzureOpenAIClient(new AzureCliCredential(), new Uri(this.Endpoint!));

        this.AssistantClient = this.Client.GetAssistantClient();
    }

    /// <inheritdoc/>
    protected override OpenAIClient Client { get; }

    /// <summary>
    /// Gets the the <see cref="AssistantClient"/>.
    /// </summary>
    protected AssistantClient AssistantClient { get; }

    protected async Task DownloadResponseContentAsync(ChatMessageContent message)
    {
        OpenAIFileClient fileClient = this.Client.GetOpenAIFileClient();

        foreach (KernelContent item in message.Items)
        {
            if (item is AnnotationContent annotation)
            {
                await this.DownloadFileContentAsync(fileClient, annotation.FileId!);
            }
        }
    }

    protected async Task DownloadResponseImageAsync(ChatMessageContent message)
    {
        OpenAIFileClient fileClient = this.Client.GetOpenAIFileClient();

        foreach (KernelContent item in message.Items)
        {
            if (item is FileReferenceContent fileReference)
            {
                await this.DownloadFileContentAsync(fileClient, fileReference.FileId, launchViewer: true);
            }
        }
    }

    private async Task DownloadFileContentAsync(OpenAIFileClient fileClient, string fileId, bool launchViewer = false)
    {
        OpenAIFile fileInfo = fileClient.GetFile(fileId);
        if (fileInfo.Purpose == FilePurpose.AssistantsOutput)
        {
            string filePath = Path.Combine(Path.GetTempPath(), Path.GetFileName(fileInfo.Filename));
            if (launchViewer)
            {
                filePath = Path.ChangeExtension(filePath, ".png");
            }

            BinaryData content = await fileClient.DownloadFileAsync(fileId);
            File.WriteAllBytes(filePath, content.ToArray());
            Console.WriteLine($"  File #{fileId} saved to: {filePath}");

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
