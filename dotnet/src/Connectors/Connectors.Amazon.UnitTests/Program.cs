// See https://aka.ms/new-console-template for more information

using System.Text;
using System.Text.Json;
using System.Text.Json.Nodes;
using Amazon.BedrockRuntime;
using Amazon.BedrockRuntime.Model;
using Connectors.Amazon.Models.Amazon;
using Connectors.Amazon.Services;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.Amazon.Services;
using Moq;

Console.WriteLine("Hello, World!");
// string modelId = "amazon.titan-text-premier-v1:0";
// string prompt = "Write a greeting.";
// List<PayloadPart> payloadParts = new List<PayloadPart>
// {
//     new PayloadPart { Bytes = new MemoryStream(JsonSerializer.SerializeToUtf8Bytes(new JsonObject { { "outputText", "Hello" } })) },
//     new PayloadPart { Bytes = new MemoryStream(JsonSerializer.SerializeToUtf8Bytes(new JsonObject { { "outputText", ", world!" } })) }
// };
// byte[] byteArray = payloadParts.SelectMany(p => p.Bytes.ToArray()).ToArray();
// var mockBedrockApi = new Mock<IAmazonBedrockRuntime>();
// mockBedrockApi.Setup(m => m.InvokeModelWithResponseStreamAsync(It.IsAny<InvokeModelWithResponseStreamRequest>(), It.IsAny<CancellationToken>()))
//     .ReturnsAsync(new InvokeModelWithResponseStreamResponse()
//     {
//         Body = new ResponseStream(new MemoryStream(Encoding.UTF8.GetBytes(JsonSerializer.Serialize("hi")))),
//         ContentType = "application/json"
//     });
//
// // var mockIoService = new Mock<AmazonIOService>();
// // mockIoService.Setup(m => m.GetInvokeModelRequestBody(prompt, null))
// //     .Returns(new { inputText = prompt, textGenerationConfig = new { temperature = 0.7, topP = 0.9, maxTokenCount = 512, stopSequences = new List<string>() } });
// // mockIoService.Setup(m => m.GetTextStreamOutput(It.IsAny<JsonNode>()))
// //     .Returns<JsonNode>(chunk => chunk?["outputText"]?.ToString() == null ? Enumerable.Empty<string>() : new[] { chunk["outputText"].ToString() });
//
// var service = new BedrockTextGenerationService(modelId, mockBedrockApi.Object);
//
// // Act
// List<StreamingTextContent> result = new List<StreamingTextContent>();
// await foreach (var item in service.GetStreamingTextContentsAsync(prompt).ConfigureAwait(true))
// {
//     Console.Write(item.Text);
//     result.Add(item);
// }





//
// // Arrange
// string modelId = "amazon.titan-text-premier-v1:0";
// var mockBedrockApi = new Mock<IAmazonBedrockRuntime>();
// var responseData = Encoding.UTF8.GetBytes(JsonSerializer.Serialize(new TitanTextResponse
// {
//     InputTextTokenCount = 5,
//     Results = new List<TitanTextResponse.Result>
//     {
//         new TitanTextResponse.Result
//         {
//             TokenCount = 10,
//             OutputText = "Hello, world!",
//             CompletionReason = "stop"
//         }
//     }
// }));
// mockBedrockApi.Setup(m => m.InvokeModelWithResponseStreamAsync(It.IsAny<InvokeModelWithResponseStreamRequest>(), It.IsAny<CancellationToken>()))
//     .ReturnsAsync(new InvokeModelWithResponseStreamResponse()
//     {
//         Body = new ResponseStream(new MemoryStream(responseData)),
//         ContentType = "application/json"
//     });
// var service = new BedrockTextGenerationService(modelId, mockBedrockApi.Object);
// var prompt = "Write a greeting.";
//
// // Act
// var streamingContents = new List<StreamingTextContent>();
// var asyncEnumerator = service.GetStreamingTextContentsAsync(prompt).ConfigureAwait(true).GetAsyncEnumerator();
// streamingContents.Add(asyncEnumerator.Current);
// Console.WriteLine("here: " + streamingContents[0].ModelId);
// try
// {
//     while (await asyncEnumerator.MoveNextAsync())
//     {
//         streamingContents.Add(asyncEnumerator.Current);
//     }
// }
// finally
// {
//     await asyncEnumerator.DisposeAsync();
// }



// string modelId = "amazon.titan-embed-text-v1:0";
// var mockBedrockApi = new Mock<IAmazonBedrockRuntime>();
// var test = new ContentBlockDeltaEvent()
// {
//     Delta = new ContentBlockDelta()
//     {
//         Text = "hello"
//     }
// };
// var byteTest = JsonSerializer.SerializeToUtf8Bytes(test);
//
// mockBedrockApi.Setup(m => m.ConverseStreamAsync(It.IsAny<ConverseStreamRequest>(), It.IsAny<CancellationToken>()))
//     .ReturnsAsync(new ConverseStreamResponse
//     {
//         Stream = new ConverseStreamOutput(new MemoryStream())
//     });
//
// var service = new BedrockChatCompletionService(modelId, mockBedrockApi.Object);
// var chatHistory = new ChatHistory();
//
// // Act
// List<StreamingChatMessageContent> output = new List<StreamingChatMessageContent>();
// var result = service.GetStreamingChatMessageContentsAsync(chatHistory).ConfigureAwait(true);
// await foreach (var item in result)
// {
//     output.Add(item);
// }


string modelId = "amazon.titan-text-premier-v1:0";
string prompt = "Write a short greeting.";

var mockBedrockApi = new Mock<IAmazonBedrockRuntime>();
mockBedrockApi.Setup(m => m.InvokeModelWithResponseStreamAsync(It.IsAny<InvokeModelWithResponseStreamRequest>(), It.IsAny<CancellationToken>()))
    .ReturnsAsync(new InvokeModelWithResponseStreamResponse()
    {
        Body = new ResponseStream(new MemoryStream()),
        ContentType = "application/json"
    });
var service = new BedrockTextGenerationService(modelId, mockBedrockApi.Object);

// Act
List<StreamingTextContent> result = new List<StreamingTextContent>();
var output = service.GetStreamingTextContentsAsync(prompt).ConfigureAwait(true);
await foreach (var item in output)
{
    Console.Write(item.Text);
    result.Add(item);
}
