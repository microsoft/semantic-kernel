// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Globalization;
using System.Text;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.AI.OpenAI;
using Microsoft.SemanticKernel.Connectors.AI.OpenAI.AzureSdk;
using Microsoft.SemanticKernel.Orchestration;
using RepoUtils;

#pragma warning disable RCS1110 // Declare type inside namespace.
#pragma warning disable CA1819 // Properties should not return arrays

/**
 * This example shows how to use multiple prompt template formats.
 */
// ReSharper disable once InconsistentNaming
public static class Example72_KernelStreaming
{
    /// <summary>
    /// Show how to combine multiple prompt template factories.
    /// </summary>
    public static async Task RunAsync(CancellationToken cancellationToken)
    {
        string apiKey = TestConfiguration.AzureOpenAI.ApiKey;
        string chatDeploymentName = TestConfiguration.AzureOpenAI.ChatDeploymentName;
        string endpoint = TestConfiguration.AzureOpenAI.Endpoint;

        if (apiKey == null || chatDeploymentName == null || endpoint == null)
        {
            Console.WriteLine("Azure endpoint, apiKey, or deploymentName not found. Skipping example.");
            return;
        }

        IKernel kernel = new KernelBuilder()
            .WithLoggerFactory(ConsoleLogger.LoggerFactory)
            .WithAzureOpenAIChatCompletionService(
                deploymentName: chatDeploymentName,
                endpoint: endpoint,
                serviceId: "AzureOpenAIChat",
                apiKey: apiKey)
            .Build();

        // Function defined using few-shot design pattern
        string promptTemplate = @"
Generate a creative reason or excuse for the given event.
Be creative and be funny. Let your imagination run wild.

Event: I am running late.
Excuse: I was being held ransom by giraffe gangsters.

Event: I haven't been to the gym for a year
Excuse: I've been too busy training my pet dragon.

Event: {{$input}}
";

        var excuseFunction = kernel.CreateSemanticFunction(promptTemplate, new OpenAIRequestSettings() { MaxTokens = 100, Temperature = 0.4, TopP = 1 });

        var roleDisplayed = false;

        Console.WriteLine("\n===  Semantic Function - Streaming ===\n");

        // Streaming can be of any type depending on the underlying service the function is using.
        await foreach (var update in kernel.RunStreamingAsync(excuseFunction, new ContextVariables("I missed the F1 final race"), cancellationToken))
        {
            // You will be always able to know the type of the update by checking the Type property.
            if (update.Type == "openai_chat_message_update" && update is StreamingChatResultChunk chatUpdate)
            {
                if (!roleDisplayed && chatUpdate.Role.HasValue)
                {
                    Console.WriteLine($"Role: {chatUpdate.Role}");
                    roleDisplayed = true;
                }

                if (chatUpdate.Content is { Length: > 0 })
                {
                    Console.Write(chatUpdate.Content);
                }
            }
        };

        var functions = kernel.ImportFunctions(new MyNativePlugin(), "MyNativePlugin");

        await NativeFunctionStreamingValueTypeAsync(kernel, functions, cancellationToken);

        await NativeFunctionStreamingComplexTypeAsync(kernel, functions, cancellationToken);

        await NativeFunctionValueTypeAsync(kernel, functions, cancellationToken);

        await NativeFunctionComplexTypeAsync(kernel, functions, cancellationToken);
    }

    private static async Task NativeFunctionStreamingValueTypeAsync(IKernel kernel, IDictionary<string, ISKFunction> functions, CancellationToken cancellationToken)
    {
        Console.WriteLine("\n\n=== Native Streaming Functions - Streaming (Value Type) ===\n");

        // Native string value type streaming function
        await foreach (var update in kernel.RunStreamingAsync(functions["MyValueTypeStreamingNativeFunction"], new ContextVariables("My Value Type Streaming Function Input"), cancellationToken))
        {
            if (update.Type == "native_result_update" && update is StreamingNativeResultChunk nativeUpdate)
            {
                Console.Write(nativeUpdate.Value);
            }
        }
    }

    private static async Task NativeFunctionStreamingComplexTypeAsync(IKernel kernel, IDictionary<string, ISKFunction> functions, CancellationToken cancellationToken)
    {
        Console.WriteLine("\n\n=== Native Streaming Functions - Streaming (Complex Type) ===\n");

        // Native complex type streaming function
        await foreach (var update in kernel.RunStreamingAsync(functions["MyComplexTypeStreamingNativeFunction"], new ContextVariables("My Complex Type Streaming Function Input"), cancellationToken))
        {
            // the complex type will be available thru the Value property of the native update abstraction.
            if (update.Type == "native_result_update" && update is StreamingNativeResultChunk nativeUpdate && nativeUpdate.Value is MyStreamingBlock myComplexType)
            {
                Console.WriteLine(Encoding.UTF8.GetString(myComplexType.Content));
            }
        }
    }

    private static async Task NativeFunctionValueTypeAsync(IKernel kernel, IDictionary<string, ISKFunction> functions, CancellationToken cancellationToken)
    {
        Console.WriteLine("\n=== Native Non-Streaming Functions - Streaming (Value Type) ===\n");

        // Native functions that don't support streaming and return value types can be executed with the streaming API's but the behavior will not be streamlike.
        await foreach (var update in kernel.RunStreamingAsync(functions["MyValueTypeNativeFunction"], new ContextVariables("My Value Type Non Streaming Function Input"), cancellationToken))
        {
            // the complex type will be available thru the Value property of the native update abstraction.
            if (update.Type == "native_result_update" && update is StreamingNativeResultChunk nativeUpdate)
            {
                Console.WriteLine(nativeUpdate.Value);
            }
        }
    }

    private static async Task NativeFunctionComplexTypeAsync(IKernel kernel, IDictionary<string, ISKFunction> functions, CancellationToken cancellationToken)
    {
        Console.WriteLine("\n=== Native Non-Streaming Functions - Streaming (Complex Type) ===\n");

        // Native functions that don't support streaming and return complex types can be executed with the streaming API's but the behavior will not be streamlike.
        await foreach (var update in kernel.RunStreamingAsync(functions["MyComplexTypeNativeFunction"], new ContextVariables("My Complex Type Non Streaming Function Input"), cancellationToken))
        {
            // the complex type will be available thru the Value property of the native update abstraction.
            if (update.Type == "native_result_update" && update is StreamingNativeResultChunk nativeUpdate && nativeUpdate.Value is MyCustomType myComplexType)
            {
                Console.WriteLine($"Text: {myComplexType.Text}, Number: {myComplexType.Number}");
            }
        }
    }

    private sealed class MyNativePlugin
    {
        [SKFunction]
        public async IAsyncEnumerable<string> MyValueTypeStreamingNativeFunctionAsync(string input)
        {
            var result = "My streaming example, should load word by word in 0.5sec".Split(' ');
            foreach (var item in result)
            {
                yield return $"{item} ";
                await Task.Delay(500);
            }
        }

        [SKFunction]
        public async IAsyncEnumerable<MyStreamingBlock> MyComplexTypeStreamingNativeFunctionAsync(string input)
        {
            // Base64 encoded string "Base64VideoPacket1 Base64VideoPacket2 Base64VideoPacket3"
            var result = "QmFzZTY0VmlkZW9QYWNrZXQx QmFzZTY0VmlkZW9QYWNrZXQy QmFzZTY0VmlkZW9QYWNrZXQz".Split(' ');

            foreach (var item in result)
            {
                yield return new MyStreamingBlock(Convert.FromBase64String(item));

                await Task.Delay(500);
            }
        }

        [SKFunction]
        public async Task<string> MyValueTypeNativeFunctionAsync(string input)
        {
            await Task.Delay(1000);
            return input;
        }

        [SKFunction]
        public MyCustomType MyComplexTypeNativeFunction(string input)
        {
            Thread.Sleep(1000);
            return new MyCustomType() { Number = 1, Text = "My Specific Text" };
        }
    }

    private sealed record MyStreamingBlock(byte[] Content);

    /// <summary>
    /// In order to use custom types, <see cref="TypeConverter"/> should be specified,
    /// that will convert object instance to string representation.
    /// </summary>
    /// <remarks>
    /// <see cref="TypeConverter"/> is used to represent complex object as meaningful string, so
    /// it can be passed to AI for further processing using semantic functions.
    /// It's possible to choose any format (e.g. XML, JSON, YAML) to represent your object.
    /// </remarks>
    [TypeConverter(typeof(MyCustomTypeConverter))]
    private sealed class MyCustomType
    {
        public int Number { get; set; }

        public string? Text { get; set; }
    }

    /// <summary>
    /// Implementation of <see cref="TypeConverter"/> for <see cref="MyCustomType"/>.
    /// In this example, object instance is serialized with <see cref="JsonSerializer"/> from System.Text.Json,
    /// but it's possible to convert object to string using any other serialization logic.
    /// </summary>
#pragma warning disable CA1812 // instantiated by Kernel
    private sealed class MyCustomTypeConverter : TypeConverter
#pragma warning restore CA1812
    {
        public override bool CanConvertFrom(ITypeDescriptorContext? context, Type sourceType) => true;

        /// <summary>
        /// This method is used to convert object from string to actual type. This will allow to pass object to
        /// native function which requires it.
        /// </summary>
        public override object? ConvertFrom(ITypeDescriptorContext? context, CultureInfo? culture, object value)
        {
            return JsonSerializer.Deserialize<MyCustomType>((string)value);
        }

        /// <summary>
        /// This method is used to convert actual type to string representation, so it can be passed to AI
        /// for further processing.
        /// </summary>
        public override object? ConvertTo(ITypeDescriptorContext? context, CultureInfo? culture, object? value, Type destinationType)
        {
            return JsonSerializer.Serialize(value);
        }
    }
}
