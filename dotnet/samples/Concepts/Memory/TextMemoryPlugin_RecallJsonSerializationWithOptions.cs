// Copyright (c) Microsoft. All rights reserved.

using System.Text.Encodings.Web;
using System.Text.Json;
using System.Text.Unicode;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using Microsoft.SemanticKernel.Memory;
using Microsoft.SemanticKernel.Plugins.Memory;

namespace Memory;

/// <summary>
/// This example shows how to use custom <see cref="JsonSerializerOptions"/> when serializing multiple results during recall using <see cref="TextMemoryPlugin"/>.
/// </summary>
/// <remarks>
/// When multiple results are returned during recall, <see cref="TextMemoryPlugin"/> has to turn these results into a string to pass back to the kernel.
/// The <see cref="TextMemoryPlugin"/> uses <see cref="JsonSerializer"/> to turn the results into a string.
/// In some cases though, the default serialization options may not work, e.g. if the memories contain non-latin text, <see cref="JsonSerializer"/>
/// will escape these characters by default. In this case, you can provide custom <see cref="JsonSerializerOptions"/> to the <see cref="TextMemoryPlugin"/> to control how the memories are serialized.
/// </remarks>
public class TextMemoryPlugin_RecallJsonSerializationWithOptions(ITestOutputHelper output) : BaseTest(output)
{
    [Fact]
    public async Task RunAsync()
    {
        // Create a Kernel.
        var kernelWithoutOptions = Kernel.CreateBuilder()
            .Build();

        // Create an embedding generator to use for semantic memory.
        var embeddingGenerator = new AzureOpenAITextEmbeddingGenerationService(TestConfiguration.AzureOpenAIEmbeddings.DeploymentName, TestConfiguration.AzureOpenAIEmbeddings.Endpoint, TestConfiguration.AzureOpenAIEmbeddings.ApiKey);

        // Using an in memory store for this example.
        var memoryStore = new VolatileMemoryStore();

        // The combination of the text embedding generator and the memory store makes up the 'SemanticTextMemory' object used to
        // store and retrieve memories.
        SemanticTextMemory textMemory = new(memoryStore, embeddingGenerator);
        await textMemory.SaveInformationAsync("samples", "First example of some text in Thai and Bengali: วรรณยุกต์ চলিতভাষা", "test-record-1");
        await textMemory.SaveInformationAsync("samples", "Second example of some text in Thai and Bengali: วรรณยุกต์ চলিতভাষা", "test-record-2");

        // Import the TextMemoryPlugin into the Kernel without any custom JsonSerializerOptions.
        var memoryPluginWithoutOptions = kernelWithoutOptions.ImportPluginFromObject(new TextMemoryPlugin(textMemory));

        // Retrieve the memories using the TextMemoryPlugin.
        var resultWithoutOptions = await kernelWithoutOptions.InvokeAsync(memoryPluginWithoutOptions["Recall"], new()
        {
            [TextMemoryPlugin.InputParam] = "Text examples",
            [TextMemoryPlugin.CollectionParam] = "samples",
            [TextMemoryPlugin.LimitParam] = "2",
            [TextMemoryPlugin.RelevanceParam] = "0.79",
        });

        // The recall operation returned the following text, where the Thai and Bengali text was escaped:
        // ["Second example of some text in Thai and Bengali: \u0E27\u0E23\u0E23\u0E13\u0E22\u0E38\u0E01\u0E15\u0E4C \u099A\u09B2\u09BF\u09A4\u09AD\u09BE\u09B7\u09BE","First example of some text in Thai and Bengali: \u0E27\u0E23\u0E23\u0E13\u0E22\u0E38\u0E01\u0E15\u0E4C \u099A\u09B2\u09BF\u09A4\u09AD\u09BE\u09B7\u09BE"]
        Console.WriteLine(resultWithoutOptions.GetValue<string>());

        // Create a Kernel.
        var kernelWithOptions = Kernel.CreateBuilder()
            .Build();

        // Import the TextMemoryPlugin into the Kernel with custom JsonSerializerOptions that allow Thai and Bengali script to be serialized unescaped.
        var options = new JsonSerializerOptions { Encoder = JavaScriptEncoder.Create(UnicodeRanges.BasicLatin, UnicodeRanges.Thai, UnicodeRanges.Bengali) };
        var memoryPluginWithOptions = kernelWithOptions.ImportPluginFromObject(new TextMemoryPlugin(textMemory, jsonSerializerOptions: options));

        // Retrieve the memories using the TextMemoryPlugin.
        var result = await kernelWithOptions.InvokeAsync(memoryPluginWithOptions["Recall"], new()
        {
            [TextMemoryPlugin.InputParam] = "Text examples",
            [TextMemoryPlugin.CollectionParam] = "samples",
            [TextMemoryPlugin.LimitParam] = "2",
            [TextMemoryPlugin.RelevanceParam] = "0.79",
        });

        // The recall operation returned the following text, where the Thai and Bengali text was not escaped:
        // ["Second example of some text in Thai and Bengali: วรรณยุกต์ চলিতভাষা","First example of some text in Thai and Bengali: วรรณยุกต์ চলিতভাষা"]
        Console.WriteLine(result.GetValue<string>());
    }
}
