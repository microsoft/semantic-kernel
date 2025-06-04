// Copyright (c) Microsoft. All rights reserved.

using System.Text;
using System.Text.Json;
using System.Text.Json.Serialization.Metadata;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;

namespace ChatCompletion;

public class ChatHistorySerialization(ITestOutputHelper output) : BaseTest(output)
{
    private static readonly JsonSerializerOptions s_options = new() { WriteIndented = true };

    /// <summary>
    /// Demonstrates how to serialize and deserialize <see cref="ChatHistory"/> class
    /// with <see cref="ChatMessageContent"/> having SK various content types as items.
    /// </summary>
    [Fact]
    public async Task SerializeChatHistoryWithSKContentTypesAsync()
    {
        int[] data = [1, 2, 3];

        var message = new ChatMessageContent(AuthorRole.User, "Describe the factors contributing to climate change.")
        {
            Items =
            [
                new TextContent("Discuss the potential long-term consequences for the Earth's ecosystem as well."),
                new ImageContent(new Uri("https://fake-random-test-host:123")),
                new BinaryContent(new BinaryData(data), "application/octet-stream"),
                new AudioContent(new BinaryData(data), "application/octet-stream")
            ]
        };

        var chatHistory = new ChatHistory([message]);

        var chatHistoryJson = JsonSerializer.Serialize(chatHistory, s_options);

        var deserializedHistory = JsonSerializer.Deserialize<ChatHistory>(chatHistoryJson);

        var deserializedMessage = deserializedHistory!.Single();

        Console.WriteLine($"Content: {deserializedMessage.Content}");
        Console.WriteLine($"Role: {deserializedMessage.Role.Label}");

        Console.WriteLine($"Text content: {(deserializedMessage.Items![0]! as TextContent)!.Text}");

        Console.WriteLine($"Image content: {(deserializedMessage.Items![1]! as ImageContent)!.Uri}");

        Console.WriteLine($"Binary content: {Encoding.UTF8.GetString((deserializedMessage.Items![2]! as BinaryContent)!.Data!.Value.Span)}");

        Console.WriteLine($"Audio content: {Encoding.UTF8.GetString((deserializedMessage.Items![3]! as AudioContent)!.Data!.Value.Span)}");

        Console.WriteLine($"JSON:\n{chatHistoryJson}");
    }

    /// <summary>
    /// Shows how to serialize and deserialize <see cref="ChatHistory"/> class with <see cref="ChatMessageContent"/> having custom content type as item.
    /// </summary>
    [Fact]
    public void SerializeChatWithHistoryWithCustomContentType()
    {
        var message = new ChatMessageContent(AuthorRole.User, "Describe the factors contributing to climate change.")
        {
            Items =
            [
                new TextContent("Discuss the potential long-term consequences for the Earth's ecosystem as well."),
                new CustomContent("Some custom content"),
            ]
        };

        var chatHistory = new ChatHistory([message]);

        // The custom resolver should be used to serialize and deserialize the chat history with custom .
        var options = new JsonSerializerOptions
        {
            TypeInfoResolver = new CustomResolver(),
            WriteIndented = true,
        };

        var chatHistoryJson = JsonSerializer.Serialize(chatHistory, options);

        var deserializedHistory = JsonSerializer.Deserialize<ChatHistory>(chatHistoryJson, options);

        var deserializedMessage = deserializedHistory!.Single();

        Console.WriteLine($"Content: {deserializedMessage.Content}");
        Console.WriteLine($"Role: {deserializedMessage.Role.Label}");

        Console.WriteLine($"Text content: {(deserializedMessage.Items![0]! as TextContent)!.Text}");

        Console.WriteLine($"Custom content: {(deserializedMessage.Items![1]! as CustomContent)!.Content}");
        Console.WriteLine($"JSON:\n{chatHistoryJson}");
    }

    private sealed class CustomContent(string content) : KernelContent(content)
    {
        public string Content { get; } = content;
    }

    /// <summary>
    /// The TypeResolver is used to serialize and deserialize custom content types polymorphically.
    /// For more details, refer to the <see href="https://learn.microsoft.com/en-us/dotnet/standard/serialization/system-text-json/polymorphism?pivots=dotnet-8-0"/> article.
    /// </summary>
    private sealed class CustomResolver : DefaultJsonTypeInfoResolver
    {
        public override JsonTypeInfo GetTypeInfo(Type type, JsonSerializerOptions options)
        {
            var jsonTypeInfo = base.GetTypeInfo(type, options);

            if (jsonTypeInfo.Type != typeof(KernelContent))
            {
                return jsonTypeInfo;
            }

            // It's possible to completely override the polymorphic configuration specified in the KernelContent class
            // by using the '=' assignment operator instead of the ??= compound assignment one in the line below.
            jsonTypeInfo.PolymorphismOptions ??= new JsonPolymorphismOptions();

            // Add custom content type to the list of derived types declared on KernelContent class.
            jsonTypeInfo.PolymorphismOptions.DerivedTypes.Add(new JsonDerivedType(typeof(CustomContent), "customContent"));

            // Override type discriminator declared on KernelContent class as "$type", if needed.
            jsonTypeInfo.PolymorphismOptions.TypeDiscriminatorPropertyName = "name";

            return jsonTypeInfo;
        }
    }
}
