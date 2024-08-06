// Copyright (c) Microsoft. All rights reserved.
using System.Collections.ObjectModel;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents.OpenAI;
using Microsoft.SemanticKernel.ChatCompletion;

/// <summary>
/// Base class for samples that demonstrate the usage of agents.
/// </summary>
public abstract class BaseAgentsTest(ITestOutputHelper output) : BaseTest(output)
{
    /// <summary>
    /// Metadata key to indicate the assistant as created for a sample.
    /// </summary>
    protected const string AssistantSampleMetadataKey = "sksample";

    /// <summary>
    /// Metadata to indicate the assistant as created for a sample.
    /// </summary>
    /// <remarks>
    /// While the samples do attempt delete the assistants it creates, it is possible
    /// that some assistants may remain.  This metadata can be used to identify and sample
    /// agents for clean-up.
    /// </remarks>
    protected static readonly ReadOnlyDictionary<string, string> AssistantSampleMetadata =
        new(new Dictionary<string, string>
        {
            { AssistantSampleMetadataKey, bool.TrueString }
        });

    /// <summary>
    /// Provide a <see cref="OpenAIServiceConfiguration"/> according to the configuration settings.
    /// </summary>
    protected OpenAIServiceConfiguration GetOpenAIConfiguration()
        =>
            this.UseOpenAIConfig ?
                OpenAIServiceConfiguration.ForOpenAI(this.ApiKey) :
                OpenAIServiceConfiguration.ForAzureOpenAI(this.ApiKey, new Uri(this.Endpoint!));

    /// <summary>
    /// %%%  REMOVE ???
    /// </summary>
    protected async Task WriteAgentResponseAsync(IAsyncEnumerable<ChatMessageContent> messages, ChatHistory? history = null)
    {
        await foreach (ChatMessageContent message in messages)
        {
            if (history != null &&
                !message.Items.Any(i => i is FunctionCallContent || i is FunctionResultContent))
            {
                history.Add(message);
            }

            this.WriteAgentChatMessage(message);
        }
    }

    /// <summary>
    /// Common method to write formatted agent chat content to the console.
    /// </summary>
    protected void WriteAgentChatMessage(ChatMessageContent message)
    {
        // Include ChatMessageContent.AuthorName in output, if present.
        string authorExpression = message.Role == AuthorRole.User ? string.Empty : $" - {message.AuthorName ?? "*"}";
        // Include TextContent (via ChatMessageContent.Content), if present.
        string contentExpression = string.IsNullOrWhiteSpace(message.Content) ? string.Empty : message.Content;
        bool isCode = message.Metadata?.ContainsKey(OpenAIAssistantAgent.CodeInterpreterMetadataKey) ?? false;
        string codeMarker = isCode ? "\n  [CODE]\n" : " ";
        Console.WriteLine($"\n# {message.Role}{authorExpression}:{codeMarker}{contentExpression}");

        // Provide visibility for inner content (that isn't TextContent).
        foreach (KernelContent item in message.Items)
        {
            if (item is AnnotationContent annotation)
            {
                Console.WriteLine($"  [{item.GetType().Name}] {annotation.Quote}: File #{annotation.FileId}");
                //BinaryData fileContent = await fileClient.DownloadFileAsync(annotation.FileId!); // %%% COMMON
                //Console.WriteLine($"\n{Encoding.Default.GetString(fileContent.ToArray())}");
                //Console.WriteLine($"\t[{item.GetType().Name}] {functionCall.Id}"); 
            }
            if (item is FileReferenceContent fileReference)
            {
                Console.WriteLine($"  [{item.GetType().Name}] File #{fileReference.FileId}");
                //BinaryData fileContent = await fileClient.DownloadFileAsync(fileReference.FileId!); // %%% COMMON
                //string filePath = Path.ChangeExtension(Path.GetTempFileName(), ".png");
                //await File.WriteAllBytesAsync($"{filePath}.png", fileContent.ToArray());
                //Console.WriteLine($"\t* Local path - {filePath}");
            }
            if (item is ImageContent image)
            {
                Console.WriteLine($"  [{item.GetType().Name}] {image.Uri?.ToString() ?? image.DataUri ?? $"{image.Data?.Length} bytes"}");
            }
            else if (item is FunctionCallContent functionCall)
            {
                Console.WriteLine($"  [{item.GetType().Name}] {functionCall.Id}");
            }
            else if (item is FunctionResultContent functionResult)
            {
                Console.WriteLine($"  [{item.GetType().Name}] {functionResult.CallId}");
            }
        }
    }

    //private async Task<string> DownloadFileContentAsync(string fileId)
    //{
    //    string filePath = Path.Combine(Environment.CurrentDirectory, $"{fileId}.jpg");
    //    BinaryData content = await fileClient.DownloadFileAsync(fileId);
    //    File.WriteAllBytes(filePath, content.ToArray());

        //    Process.Start(
        //        new ProcessStartInfo
        //        {
        //            FileName = "cmd.exe",
        //            Arguments = $"/C start {filePath}"
        //        });

        //    return filePath;
        //}
}
