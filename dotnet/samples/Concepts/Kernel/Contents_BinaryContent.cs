// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json;
using Microsoft.SemanticKernel;

namespace KernelExamples;
public class Contents_BinaryContent(ITestOutputHelper output) : BaseTest(output)
{
    [Fact] public Task UsingRawBinaryContents()
    {
        Console.WriteLine("======== Binary Contents ========");
        var content = new BinaryContent(new ReadOnlyMemory<byte>([0x01, 0x02, 0x03, 0x04]), "application/octet-stream");
        var serialized = JsonSerializer.Serialize(content);

        Console.WriteLine($"Serialized Base64 Content: {serialized}");

        return Task.CompletedTask;
    }
}
