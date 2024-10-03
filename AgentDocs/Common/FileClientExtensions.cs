using System;
using System.Threading.Tasks;
using OpenAI.Files;

namespace AgentsSample;

public static class FileClientExtensions
{
    public static async Task<OpenAIFileInfo> UploadFileAsync(this FileClient fileClient, string filePath)
    {
        Console.WriteLine($"Uploading file: ${filePath}");
        return await fileClient.UploadFileAsync(filePath, FileUploadPurpose.Assistants);
    }
}
