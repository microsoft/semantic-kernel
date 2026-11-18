// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics;
using Azure.AI.Extensions.OpenAI;
using Azure.AI.Projects;
using Azure.AI.Projects.Agents;
using Azure.Identity;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using OpenAI.Containers;
using OpenAI.Files;
using OpenAI.Responses;

/// <summary>
/// Base class for samples that use a Microsoft Foundry Prompt Agent through a <see cref="ChatCompletionAgent"/>.
/// </summary>
/// <remarks>
/// A Foundry Prompt Agent is a versioned agent definition (model, instructions, and tools) stored in a Foundry project.
/// It replaces the OpenAI Assistants API, which OpenAI shut down on August 26, 2026.
/// The samples read the project endpoint from <c>AzureAI:Endpoint</c> and the model deployment from <c>AzureAI:ChatModelId</c>.
/// </remarks>
public abstract class BaseFoundryAgentTest : BaseAgentsTest<AIProjectClient>
{
    protected BaseFoundryAgentTest(ITestOutputHelper output) : base(output)
    {
        this.Client = new AIProjectClient(new Uri(TestConfiguration.AzureAI.Endpoint), new AzureCliCredential());
        ProjectOpenAIClient openAIClient = this.Client.GetProjectOpenAIClient();
        this.FileClient = openAIClient.GetProjectFilesClient();
        this.VectorStoreClient = openAIClient.GetProjectVectorStoresClient();
        this.ContainerClient = openAIClient.GetContainerClient();
    }

    /// <inheritdoc/>
    protected override AIProjectClient Client { get; }

    /// <summary>
    /// Gets the client for files that Prompt Agent tools use, such as code interpreter inputs and file search documents.
    /// </summary>
    protected ProjectFilesClient FileClient { get; }

    /// <summary>
    /// Gets the client for the vector stores that the file search tool searches.
    /// </summary>
    protected ProjectVectorStoresClient VectorStoreClient { get; }

    /// <summary>
    /// Gets the client for the containers in which the code interpreter tool runs and stores its generated files.
    /// </summary>
    protected ContainerClient ContainerClient { get; }

    /// <summary>
    /// Gets the model deployment that the Prompt Agents use.
    /// </summary>
    protected static string DeploymentName => TestConfiguration.AzureAI.ChatModelId;

    /// <summary>
    /// Creates a Prompt Agent version with a unique name that starts with <paramref name="name"/>.
    /// </summary>
    protected Task<ProjectsAgentVersion> CreatePromptAgentAsync(string name, DeclarativeAgentDefinition definition)
        => this.Client.CreatePromptAgentAsync(name, definition);

    /// <summary>
    /// Deletes the Prompt Agent, including all of its versions.
    /// </summary>
    protected Task DeletePromptAgentAsync(ProjectsAgentVersion agentVersion)
        => this.Client.DeletePromptAgentAsync(agentVersion);

    /// <summary>
    /// Creates a <see cref="Kernel"/> whose chat service sends every request to the given Prompt Agent version.
    /// </summary>
    /// <param name="agentVersion">The Prompt Agent version that receives the requests.</param>
    /// <param name="plugins">The plugins whose functions the Prompt Agent may call. Declare them on the definition with
    /// <see cref="FoundryPromptAgentExtensions.AddFunctionTools"/> as well.</param>
    protected Kernel CreateKernel(ProjectsAgentVersion agentVersion, params KernelPlugin[] plugins)
    {
        IKernelBuilder builder = Kernel.CreateBuilder();
        builder.Services.AddSingleton(this.Client.AsKernelChatClient(agentVersion, this.LoggerFactory));
        Kernel kernel = builder.Build();
        kernel.Plugins.AddRange(plugins);
        return kernel;
    }

    /// <summary>
    /// Uploads a file that Prompt Agent tools can use.
    /// </summary>
    protected async Task<OpenAIFile> UploadFileAsync(Stream stream, string fileName)
    {
        // "assistants" is the Files API purpose for files used by agent tools. It isn't tied to the retired Assistants API.
        return await this.FileClient.UploadFileAsync(stream, fileName, FileUploadPurpose.Assistants);
    }

    /// <summary>
    /// Downloads the files that the code interpreter tool generated for a response.
    /// </summary>
    /// <param name="message">The response message.</param>
    /// <param name="launchViewer">Opens each downloaded image with its default viewer, for example to display a chart.</param>
    protected async Task DownloadGeneratedFilesAsync(ChatMessageContent message, bool launchViewer = false)
    {
        foreach (ContainerFileCitationMessageAnnotation file in message.GetGeneratedFiles())
        {
            await this.DownloadGeneratedFileAsync(file, launchViewer);
        }
    }

    /// <summary>
    /// Downloads the files that the code interpreter tool generated for a streamed response.
    /// </summary>
    /// <param name="message">A streamed update.</param>
    /// <param name="launchViewer">Opens each downloaded image with its default viewer, for example to display a chart.</param>
    protected async Task DownloadGeneratedFilesAsync(StreamingChatMessageContent message, bool launchViewer = false)
    {
        foreach (ContainerFileCitationMessageAnnotation file in message.GetGeneratedFiles())
        {
            await this.DownloadGeneratedFileAsync(file, launchViewer);
        }
    }

    private static readonly HashSet<string> s_viewableImageExtensions = new(StringComparer.OrdinalIgnoreCase) { ".png", ".jpg", ".jpeg", ".gif", ".bmp" };

    private async Task DownloadGeneratedFileAsync(ContainerFileCitationMessageAnnotation file, bool launchViewer)
    {
        BinaryData content = (await this.ContainerClient.DownloadContainerFileAsync(file.ContainerId, file.FileId)).Value;

        string filePath = Path.Combine(Path.GetTempPath(), Path.GetFileName(file.Filename));
        await File.WriteAllBytesAsync(filePath, content.ToArray());
        Console.WriteLine($"  File #{file.FileId} saved to: {filePath}");

        // The model chooses the file name. Only images are opened, and the shell opens them with the default viewer
        // instead of a command line, so a generated script or executable is never run.
        if (launchViewer && s_viewableImageExtensions.Contains(Path.GetExtension(filePath)))
        {
            using Process? viewer = Process.Start(new ProcessStartInfo(filePath) { UseShellExecute = true });
        }
    }
}
