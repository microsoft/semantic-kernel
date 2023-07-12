// Copyright (c) Microsoft. All rights reserved.

using System.Threading.Tasks;
using Microsoft.SemanticKernel.Services.Configuration;
using Microsoft.SemanticKernel.Services.Storage.Pipeline;

public class Example1_ImportWithMemoryClient
{
    public static async Task RunAsync()
    {
        var memory = new SemanticMemoryClient(AppBuilder.Build().Services);

        await memory.ImportFileAsync("file1.txt", "user1", "collection01");
        await memory.ImportFileAsync("file2.txt", "user1", "collection01");
        await memory.ImportFileAsync("file3.doc", "user1", "collection01");
        await memory.ImportFileAsync("file4.pdf", "user1", "collection01");
    }
}
