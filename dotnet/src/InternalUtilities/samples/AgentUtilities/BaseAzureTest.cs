// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics;
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
        this.Client = AzureAIAgent.CreateAgentsClient(TestConfiguration.AzureAI.Endpoint, new AzureCliCredential());
    }

    protected override PersistentAgentsClient Client { get; }

    protected AIProjectClient CreateFoundryProjectClient()
    {
        return new AIProjectClient(new Uri(TestConfiguration.AzureAI.Endpoint), new AzureCliCredential());
    }

    protected async Task<string> GetConnectionId(string connectionName)
    {
        AIProjectClient client = CreateFoundryProjectClient();
        AIProjectConnectionsOperations connectionOperations = client.Connections;
        AIProjectConnection connection =
            await connectionOperations.GetConnectionsAsync().Where(connection => connection.Name == connectionName).FirstOrDefaultAsync() ??
            throw new InvalidOperationException($"Connection '{connectionName}' not found in project '{TestConfiguration.AzureAI.Endpoint}'.");
        return connection.Id;
    }

    protected async Task DownloadContentAsync(ChatMessageContent message)
    {
        foreach (KernelContent item in message.Items)
        {
            if (item is AnnotationContent annotation)
            {
                await this.DownloadFileAsync(annotation.ReferenceId!);
            }
        }
    }

    protected async Task DownloadFileAsync(string fileId, bool launchViewer = false)
    {
        PersistentAgentFileInfo fileInfo = this.Client.Files.GetFile(fileId);
        if (fileInfo.Purpose == PersistentAgentFilePurpose.AgentsOutput)
        {
            string filePath = Path.Combine(Path.GetTempPath(), Path.GetFileName(fileInfo.Filename));
            if (launchViewer)
            {
                filePath = Path.ChangeExtension(filePath, ".png");
            }

            BinaryData content = await this.Client.Files.GetFileContentAsync(fileId);
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
