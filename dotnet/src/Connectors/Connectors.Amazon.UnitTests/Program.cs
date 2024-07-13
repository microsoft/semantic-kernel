// See https://aka.ms/new-console-template for more information

using System.Text;
using System.Text.Json;
using Amazon.BedrockRuntime;
using Amazon.BedrockRuntime.Model;
using Connectors.Amazon.Models.Amazon;
using Connectors.Amazon.Services;
using Microsoft.SemanticKernel;
using Moq;

Console.WriteLine("Hello, World!");

// Arrange
string modelId = "amazon.titan-text-premier-v1:0";
var mockBedrockApi = new Mock<IAmazonBedrockRuntime>();
var responseData = Encoding.UTF8.GetBytes(JsonSerializer.Serialize(new TitanTextResponse
{
    InputTextTokenCount = 5,
    Results = new List<TitanTextResponse.Result>
    {
        new TitanTextResponse.Result
        {
            TokenCount = 10,
            OutputText = "Hello, world!",
            CompletionReason = "stop"
        }
    }
}));
mockBedrockApi.Setup(m => m.InvokeModelWithResponseStreamAsync(It.IsAny<InvokeModelWithResponseStreamRequest>(), It.IsAny<CancellationToken>()))
    .ReturnsAsync(new InvokeModelWithResponseStreamResponse()
    {
        Body = new ResponseStream(new MemoryStream(responseData)),
        ContentType = "application/json"
    });
var service = new BedrockTextGenerationService(modelId, mockBedrockApi.Object);
var prompt = "Write a greeting.";

// Act
var streamingContents = new List<StreamingTextContent>();
var asyncEnumerator = service.GetStreamingTextContentsAsync(prompt).ConfigureAwait(true).GetAsyncEnumerator();
streamingContents.Add(asyncEnumerator.Current);
Console.WriteLine("here: " + streamingContents[0].ModelId);
try
{
    while (await asyncEnumerator.MoveNextAsync())
    {
        streamingContents.Add(asyncEnumerator.Current);
    }
}
finally
{
    await asyncEnumerator.DisposeAsync();
}
