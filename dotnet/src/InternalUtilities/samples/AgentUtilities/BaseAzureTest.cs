// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics;
using Azure;
using Azure.AI.Agents.Persistent;
using Azure.AI.Projects;
using Azure.Identity;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Agents.AzureAI;

/// <summary>
/// Base class for samples that demonstrate the usage of <see cref="AzureAIAgent"/>.
/// </summary>
public abstract class BaseAzureAgentTest : BaseAgentsTest<PersistentAgentsClient>
{
    protected BaseAzureAgentTest(ITestOutputHelper output) : base(output)
    {
        this.Client =
            string.IsNullOrEmpty(TestConfiguration.AzureAI.ApiKey) ?
                AzureAIAgent.CreateAgentsClient(new Uri(TestConfiguration.AzureAI.Endpoint), new AzureCliCredential()) :
                AzureAIAgent.CreateAgentsClient(new Uri(TestConfiguration.AzureAI.Endpoint), new AzureKeyCredential(TestConfiguration.AzureAI.ApiKey));
    }

    /// <inheritdoc/>
    protected override PersistentAgentsClient Client { get; }

    /// <summary>
    /// Gets the <see cref="AgentsClient"/>.
    /// </summary>
    protected AgentsClient AgentsClient { get; }

    protected async Task DownloadContentAsync(ChatMessageContent message)
    {
        foreach (KernelContent item in message.Items)
        {
            if (item is AnnotationContent annotation)
            {
                await this.DownloadFileAsync(annotation.FileId!);
            }
        }
    }

    protected async Task DownloadFileAsync(string fileId, bool launchViewer = false)
    {
        PersistentAgentFile fileInfo = this.Client.GetFile(fileId);
        if (fileInfo.Purpose == PersistentAgentFilePurpose.AgentsOutput)
        {
            string filePath = Path.Combine(Path.GetTempPath(), Path.GetFileName(fileInfo.Filename));
            if (launchViewer)
            {
                filePath = Path.ChangeExtension(filePath, ".png");
            }

            BinaryData content = await this.Client.GetFileContentAsync(fileId);
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
