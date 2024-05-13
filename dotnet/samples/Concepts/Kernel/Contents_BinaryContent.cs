// Copyright (c) Microsoft. All rights reserved.

using System.Text;
using System.Text.Json;
using Microsoft.SemanticKernel;

namespace KernelExamples;
public class Contents_BinaryContent(ITestOutputHelper output) : BaseTest(output)
{
    [Fact]
    public Task BinarySerialization()
    {
        var content = new BinaryContent(new ReadOnlyMemory<byte>([0x01, 0x02, 0x03, 0x04]), "application/octet-stream");
        var serialized = JsonSerializer.Serialize(content);

        Console.WriteLine($"Content ToString: {content}");
        Console.WriteLine($"Serialized Content: {serialized}");

        var deserializedContent = JsonSerializer.Deserialize<BinaryContent>(serialized);
        Console.WriteLine($"Deserialized Content ToString: {deserializedContent}");

        return Task.CompletedTask;
    }

    [Fact]
    public Task UriSerialization()
    {
        var content = new BinaryContent(new Uri("https://fake-random-test-host:123"));
        var serialized = JsonSerializer.Serialize(content);

        Console.WriteLine($"Content ToString: {content}");
        Console.WriteLine($"Serialized Content: {serialized}");

        var deserializedContent = JsonSerializer.Deserialize<BinaryContent>(serialized);
        Console.WriteLine($"Deserialized Content ToString: {deserializedContent}");

        return Task.CompletedTask;
    }

    [Fact]
    public Task TransformNonReadableInAReadable()
    {
        var content = new BinaryContent(new Uri("https://fake-random-test-host:123"));
        var serialized = JsonSerializer.Serialize(content);
        Console.WriteLine($"Serialized Content Before: {serialized}");
        Console.WriteLine($"Content ToString Before: {content}");

        content.Uri = "data:text/plain;base64,VGhpcyBpcyBhIHRleHQgY29udGVudA==";

        Assert.True(content.CanRead());

        serialized = JsonSerializer.Serialize(content);
        Console.WriteLine($"Serialized Content After: {serialized}");
        Console.WriteLine($"Content ToString After: {content}");

        var deserializedContent = JsonSerializer.Deserialize<BinaryContent>(serialized);
        Console.WriteLine($"Deserialized Content ToString After: {deserializedContent}");

        return Task.CompletedTask;
    }

    [Fact]
    public Task TransformReadableInANonReadable()
    {
        var content = new BinaryContent("data:text/plain;base64,VGhpcyBpcyBhIHRleHQgY29udGVudA==");
        var serialized = JsonSerializer.Serialize(content);
        Console.WriteLine($"Serialized Content Before: {serialized}");
        Console.WriteLine($"Content ToString Before: {content}");

        content.Uri = "https://fake-random-test-host:123";

        Assert.False(content.CanRead());

        serialized = JsonSerializer.Serialize(content);
        Console.WriteLine($"Serialized Content After: {serialized}");
        Console.WriteLine($"Content ToString After: {content}");

        var deserializedContent = JsonSerializer.Deserialize<BinaryContent>(serialized);
        Console.WriteLine($"Deserialized Content ToString After: {deserializedContent}");

        return Task.CompletedTask;
    }


    [Fact]
    public async Task ByteArrayProviderAsync()
    {
        async static Task<(ReadOnlyMemory<byte> content, string mimeType)> Provider() => (Encoding.UTF8.GetBytes("This is a text content"), "text/plain");
        var content = new BinaryContent(Provider!);

        var byteArray = await content.GetByteArrayAsync();
        Console.WriteLine($"ByteArray: {byteArray}");

        // Should be possible to serialize after the content is retrieved once.
        var serialized = JsonSerializer.Serialize(content);

        Console.WriteLine($"Content ToString: {content}");

        Console.WriteLine($"Serialized Content: {serialized}");

        var deserializedContent = JsonSerializer.Deserialize<BinaryContent>(serialized)!;

        Console.WriteLine($"Deserialized Content ToString: {deserializedContent}");

        var deserializedContentArray = await deserializedContent.GetByteArrayAsync();

        Console.WriteLine($"Deserialized ByteArray: {byteArray}");
    }

    [Fact]
    public async Task StreamProviderAsync()
    {
        int invocations = 0;
        Stream? streamForProvider = null;
        async Task<(Stream content, string? mimeType)> Provider()
        {
            invocations++;
            streamForProvider = new MemoryStream(Encoding.UTF8.GetBytes("This is a text content"));
            return (streamForProvider, "text/plain");
        }

        var content = new BinaryContent(Provider!);

        await content.GetByteArrayAsync();
        await content.GetByteArrayAsync();

        var byteArray = await content.GetByteArrayAsync();
        Console.WriteLine($"ByteArray: {byteArray}");

        // Should be possible to serialize after the content is retrieved once.
        var serialized = JsonSerializer.Serialize(content);

        Console.WriteLine($"Content ToString: {content}");
        Console.WriteLine($"Serialized Content: {serialized}");

        var deserializedContent = JsonSerializer.Deserialize<BinaryContent>(serialized)!;

        Console.WriteLine($"Deserialized Content ToString: {deserializedContent}");

        var deserializedContentArray = await deserializedContent.GetByteArrayAsync();

        Console.WriteLine($"Deserialized ByteArray: {byteArray}");

        Assert.Equal(1, invocations);
    }
}

public class Contents_ImageV2Content(ITestOutputHelper output) : BaseTest(output)
{
    [Fact]
    public Task Serialization()
    {
        var content = new ImageContentV2(new Uri("https://fake-random-test-host:123"));
        var serialized = JsonSerializer.Serialize(content);

        Console.WriteLine($"Content ToString: {content}");

        Console.WriteLine($"Serialized Content: {serialized}");

        var deserializedContent = JsonSerializer.Deserialize<ImageContentV2>(serialized);

        Console.WriteLine($"Deserialized Content ToString: {deserializedContent}");

        return Task.CompletedTask;
    }
}
