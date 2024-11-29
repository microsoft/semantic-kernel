// Copyright (c) Microsoft. All rights reserved.

using System.Net.Http.Json;
using System.Text;
using System.Text.Json;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using Microsoft.SemanticKernel.Plugins.OpenApi;

namespace Plugins;

/// <summary>
/// These samples demonstrate how SK can handle payloads for OpenAPI functions. Today, SK can handle payloads in the following ways:
///   1. By accepting the payload from the caller. See the <see cref="InvokeOpenApiFunctionWithPayloadProvidedByCallerAsync"/> sample for more details.
///   2. By constructing the payload based on the function's schema from leaf properties. See the <see cref="InvokeOpenApiFunctionWithArgumentsForPayloadLeafPropertiesAsync"/> sample for more details.
///   3. By constructing the payload based on the function's schema from leaf properties with namespaces. See the <see cref="InvokeOpenApiFunctionWithArgumentsForPayloadLeafPropertiesWithNamespacesAsync"/> sample for more details.
/// </summary>
public sealed class OpenApiPlugin_PayloadHandling : BaseTest
{
    private readonly Kernel _kernel;
    private readonly ITestOutputHelper _output;
    private readonly HttpClient _httpClient;

    public OpenApiPlugin_PayloadHandling(ITestOutputHelper output) : base(output)
    {
        IKernelBuilder builder = Kernel.CreateBuilder();
        builder.AddOpenAIChatCompletion(
            modelId: TestConfiguration.OpenAI.ChatModelId,
            apiKey: TestConfiguration.OpenAI.ApiKey);

        this._kernel = builder.Build();

        this._output = output;

        void RequestPayloadHandler(string requestPayload)
        {
            this._output.WriteLine("Actual request payload");
            this._output.WriteLine(requestPayload);
        }

        // Create HTTP client with a stub handler to log the request payload
        this._httpClient = new(new StubHttpHandler(RequestPayloadHandler));
    }

    /// <summary>
    /// This sample demonstrates how to invoke an OpenAPI function with a payload provided by the caller.
    /// </summary>
    [Fact]
    public async Task InvokeOpenApiFunctionWithPayloadProvidedByCallerAsync()
    {
        // Load an Open API document for the Event Utils service
        using Stream stream = File.OpenRead("Resources/Plugins/EventPlugin/openapiV2.json");

        // Import an OpenAPI document as SK plugin
        KernelPlugin plugin = await this._kernel.ImportPluginFromOpenApiAsync("Event_Utils", stream, new OpenApiFunctionExecutionParameters(this._httpClient)
        {
            EnableDynamicPayload = false // Disable dynamic payload construction
        });

        KernelFunction createMeetingFunction = plugin["createMeeting"];
        // Function parameters metadata available via createMeetingFunction.Metadata.Parameters property:
        // Parameter[0]
        //   Name: "payload"
        //   Description: "REST API request body."
        //   ParameterType: "{Name = "Object" FullName = "System.Object"}"
        //   Schema: {
        //      "type": "object",
        //      "properties": {
        //          "subject": {
        //              "type": "string"
        //          },
        //          "start": {
        //              "required": ["dateTime", "timeZone"],
        //              "type": "object",
        //              "properties": {
        //                  "dateTime": {
        //                      "type": "string",
        //                      "description": "The start date and time of the meeting in ISO 8601 format.",
        //                      "format": "date-time"
        //                  },
        //                  "timeZone": {
        //                      "type": "string",
        //                      "description": "The time zone in which the meeting starts."
        //                  }
        //              }
        //          }
        //          "end": {
        //              "type": "object",
        //              "properties": Similar to the 'start' property one
        //          }
        //          "tags": {
        //              "type": "array",
        //              "items": {
        //                  "required": ["name"],
        //                  "type": "object",
        //                  "properties": {
        //                      "name": {
        //                          "type": "string",
        //                          "description": "A tag associated with the meeting for categorization."
        //                      }
        //                  }
        //              },
        //              "description": "A list of tags to help categorize the meeting."
        //          }
        //      }
        //   }
        // Parameter[1]
        //   Name: "content_type"
        //   Description: "Content type of REST API request body."
        //   ParameterType: { Name = "String" FullName = "System.String" }
        //   Schema: { "type": "string" }

        // Create the payload for the createEvent function.
        string payload = """
        {
            "subject": "IT Meeting",
            "start": {
                "dateTime": "2023-10-01T10:00:00",
                "timeZone": "UTC"
            },
            "end": {
                "dateTime": "2023-10-01T11:00:00",
                "timeZone": "UTC"
            },
            "tags": [
                { "name": "IT" },
                { "name": "Meeting" }
            ]
        }
        """;

        // Create arguments for the createEvent function
        KernelArguments arguments = new()
        {
            ["payload"] = payload,
            ["content-type"] = "application/json"
        };

        // Example of how to invoke the createEvent function explicitly
        await this._kernel.InvokeAsync(createMeetingFunction, arguments);

        // Example of how to have the createEvent function invoked by the AI
        OpenAIPromptExecutionSettings settings = new() { FunctionChoiceBehavior = FunctionChoiceBehavior.Auto() };
        await this._kernel.InvokePromptAsync("Schedule one hour IT Meeting for October 1st, 2023, at 10:00 AM UTC.", new KernelArguments(settings));
    }

    /// <summary>
    /// This sample demonstrates how to invoke an OpenAPI function with arguments for payload leaf properties.
    /// </summary>
    [Fact]
    public async Task InvokeOpenApiFunctionWithArgumentsForPayloadLeafPropertiesAsync()
    {
        // Load an Open API document for the simplified Event Utils service
        using Stream stream = File.OpenRead("Resources/Plugins/EventPlugin/openapiV1.json");

        // Import an OpenAPI document as SK plugin
        KernelPlugin plugin = await this._kernel.ImportPluginFromOpenApiAsync("Event_Utils", stream, new OpenApiFunctionExecutionParameters(this._httpClient)
        {
            EnableDynamicPayload = true // Enable dynamic payload construction. It is enabled by default.
        });

        KernelFunction createMeetingFunction = plugin["createMeeting"];
        // Function parameters metadata available via createMeetingFunction.Metadata.Parameters property:
        // Parameter[0]
        //   Name: "subject"
        //   Description: "The subject or title of the meeting."
        //   ParameterType: { Name = "String" FullName = "System.String"}
        //   Schema: { "type": "string", "description": "The subject or title of the meeting." }
        // Parameter[1]
        //   Name: "dateTime"
        //   Description: "The start date and time of the meeting in ISO 8601 format."
        //   ParameterType: {Name = "String" FullName = "System.String"}
        //   Schema: { "type": "string", "description": "The start date and time of the meeting in ISO 8601 format.", "format": "date-time" }
        // Parameter[2]
        //   Name: "timeZone"
        //   Description: "The time zone in which the meeting is scheduled."
        //   ParameterType: {Name = "String" FullName = "System.String"}
        //   Schema: { "type": "string", "description": "The time zone in which the meeting is scheduled." }
        // Parameter[3]
        //   Name: "duration"
        //   Description: "Duration of the meeting in ISO 8601 format (e.g., 'PT1H' for 1 hour).."
        //   ParameterType: {Name = "String" FullName = "System.String"}
        //   Schema: { "type": "string", "description": "Duration of the meeting in ISO 8601 format (e.g., PT1H for 1 hour)." }
        // Parameter[4]
        //   Name: "tags"
        //   Description: "A list of tags to help categorize the meeting."
        //   ParameterType: null
        //   Schema: { "type": "array", "items": { "required": ["name"], "type": "object", "properties": { "name": { "type": "string", "description": "A tag associated with the meeting for categorization." }}}, "description": "A list of tags to help categorize the meeting."}

        // Create arguments for the createEvent function
        KernelArguments arguments = new()
        {
            ["subject"] = "IT Meeting",
            ["dateTime"] = "2023-10-01T10:00:00",
            ["timeZone"] = "UTC",
            ["duration"] = "PT1H",
            ["tags"] = """[ { "name": "IT" }, { "name": "Meeting" }  ]"""
        };

        // Example of how to invoke the createEvent function explicitly
        await this._kernel.InvokeAsync(createMeetingFunction, arguments);

        // Example of how to have the createEvent function invoked by the AI
        OpenAIPromptExecutionSettings settings = new() { FunctionChoiceBehavior = FunctionChoiceBehavior.Auto() };
        await this._kernel.InvokePromptAsync("Schedule one hour IT Meeting for October 1st, 2023, at 10:00 AM UTC.", new KernelArguments(settings));
    }

    /// <summary>
    /// This sample demonstrates how to invoke an OpenAPI function with arguments for payload leaf properties with namespaces.
    /// </summary>
    [Fact]
    public async Task InvokeOpenApiFunctionWithArgumentsForPayloadLeafPropertiesWithNamespacesAsync()
    {
        // Load an Open API document for the Event Utils service
        using Stream stream = File.OpenRead("Resources/Plugins/EventPlugin/openapiV2.json");

        // Import an OpenAPI document as SK plugin
        KernelPlugin plugin = await this._kernel.ImportPluginFromOpenApiAsync("Event_Utils", stream, new OpenApiFunctionExecutionParameters(this._httpClient)
        {
            EnableDynamicPayload = true, // Enable dynamic payload construction. It is enabled by default.
            EnablePayloadNamespacing = true // Enable payload namespacing.
        });

        KernelFunction createMeetingFunction = plugin["createMeeting"];
        // Function parameters metadata available via createMeetingFunction.Metadata.Parameters property:
        // Parameter[0]
        //   Name: "subject"
        //   Description: "The subject or title of the meeting."
        //   ParameterType: { Name = "String" FullName = "System.String"}
        //   Schema: { "type": "string", "description": "The subject or title of the meeting." }
        // Parameter[1]
        //   Name: "start_dateTime"
        //   Description: "The start date and time of the meeting in ISO 8601 format."
        //   ParameterType: {Name = "String" FullName = "System.String"}
        //   Schema: { "type": "string", "description": "The start date and time of the meeting in ISO 8601 format.", "format": "date-time" }
        // Parameter[2]
        //   Name: "start_timeZone"
        //   Description: "The time zone in which the meeting is scheduled."
        //   ParameterType: {Name = "String" FullName = "System.String"}
        //   Schema: { "type": "string", "description": "The time zone in which the meeting is scheduled." }
        // Parameter[3]
        //   Name: "end_dateTime"
        //   Description: "The end date and time of the meeting in ISO 8601 format."
        //   ParameterType: {Name = "String" FullName = "System.String"}
        //   Schema: { "type": "string", "description": "The end date and time of the meeting in ISO 8601 format.", "format": "date-time" }
        // Parameter[4]
        //   Name: "end_timeZone"
        //   Description: "The time zone in which the meeting ends."
        //   ParameterType: {Name = "String" FullName = "System.String"}
        //   Schema: { "type": "string", "description": "The time zone in which the meeting ends." }
        // Parameter[5]
        //   Name: "tags"
        //   Description: "A list of tags to help categorize the meeting."
        //   ParameterType: null
        //   Schema: {
        //      "type": "array",
        //      "items": {
        //          "required": ["name"],
        //          "type": "object",
        //          "properties": {
        //              "name": {
        //                  "type": "string",
        //                  "description": "A tag associated with the meeting for categorization."
        //              }
        //          }
        //      },
        //      "description": "A list of tags to help categorize the meeting."
        //  }

        // Create arguments for the createEvent function
        KernelArguments arguments = new()
        {
            ["subject"] = "IT Meeting",
            ["start.dateTime"] = "2023-10-01T10:00:00",
            ["start.timeZone"] = "UTC",
            ["end.dateTime"] = "2023-10-01T11:00:00",
            ["end.timeZone"] = "UTC",
            ["tags"] = """[ { "name": "IT" }, { "name": "Meeting" }  ]"""
        };

        // Example of how to invoke the createEvent function explicitly
        await this._kernel.InvokeAsync(createMeetingFunction, arguments);

        // Example of how to have the createEvent function invoked by the AI
        OpenAIPromptExecutionSettings settings = new() { FunctionChoiceBehavior = FunctionChoiceBehavior.Auto() };
        await this._kernel.InvokePromptAsync("Schedule one hour IT Meeting for October 1st, 2023, at 10:00 AM UTC.", new KernelArguments(settings));
    }

    /// <summary>
    /// This sample demonstrates how to invoke an OpenAPI function with arguments for payload using oneOf.
    /// </summary>
    [Fact]
    public async Task InvokeOpenApiFunctionWithArgumentsForPayloadOneOfAsync()
    {
        // Load an Open API document for the Event Utils service
        using Stream stream = File.OpenRead("Resources/Plugins/PetsPlugin/oneOfV3.json");

        // Import an OpenAPI document as SK plugin
        KernelPlugin plugin = await this._kernel.ImportPluginFromOpenApiAsync("Pets", stream, new OpenApiFunctionExecutionParameters(this._httpClient)
        {
            EnableDynamicPayload = false // Disable dynamic payload construction. It is enabled by default.
        });

        // Example of how to have the updatePater function invoked by the AI
        OpenAIPromptExecutionSettings settings = new() { FunctionChoiceBehavior = FunctionChoiceBehavior.Auto() };
        Console.WriteLine("\nExpected payload: Dog { breed=Husky, bark=false }");
        await this._kernel.InvokePromptAsync("My new dog is a Husky, he is very quiet, please create my pet information.", new KernelArguments(settings));
        Console.WriteLine("\nExpected payload: Dog { breed=Dingo, bark=true }");
        await this._kernel.InvokePromptAsync("My dog is a Dingo, he is very noisy, he likes to hunt for rabbits, please update my pet information.", new KernelArguments(settings));
        Console.WriteLine("\nExpected payload: Cat { age=15 }");
        await this._kernel.InvokePromptAsync("My cat is 15 years old now, please update my pet information.", new KernelArguments(settings));
        Console.WriteLine("\nExpected payload: Cat { hunts=true }");
        await this._kernel.InvokePromptAsync("I have a feline pet, she goes out every night hunting mice, please update my pet information.", new KernelArguments(settings));
        Console.WriteLine("\nExpected payload: Cat { age=3, hunts=true }");
        Console.WriteLine(await this._kernel.InvokePromptAsync("I have a new 3 year old cat who chases birds and barks, please create my pet information.", new KernelArguments(settings)));
    }

    /// <summary>
    /// This sample demonstrates how to invoke an OpenAPI function with arguments for payload using allOf.
    /// </summary>
    [Fact]
    public async Task InvokeOpenApiFunctionWithArgumentsForPayloadAllOfAsync()
    {
        // Load an Open API document for the Event Utils service
        using Stream stream = File.OpenRead("Resources/Plugins/PetsPlugin/allOfV3.json");

        // Import an OpenAPI document as SK plugin
        KernelPlugin plugin = await this._kernel.ImportPluginFromOpenApiAsync("Pets", stream, new OpenApiFunctionExecutionParameters(this._httpClient)
        {
            EnableDynamicPayload = false // Disable dynamic payload construction. It is enabled by default.
        });

        // Example of how to have the updatePater function invoked by the AI
        OpenAIPromptExecutionSettings settings = new() { FunctionChoiceBehavior = FunctionChoiceBehavior.Auto() };
        Console.WriteLine("\nExpected payload: { pet_type=dog, breed=Husky, bark=false }");
        Console.WriteLine(await this._kernel.InvokePromptAsync("My new dog is a Husky, he is very quiet, please update my pet information.", new KernelArguments(settings)));
        Console.WriteLine("\nExpected payload: { pet_type=dog, breed=Dingo, bark=true }");
        // This prompt deliberately tries to confuse the LLM and it succeed, in this scenario the API must provide an error message so the LLM can correct the playload
        Console.WriteLine(await this._kernel.InvokePromptAsync("My new dog is a Dingo, he is very noisy, he likes to hunt for rabbits, please create my pet information.", new KernelArguments(settings)));
        Console.WriteLine("\nExpected payload: { pet_type=cat, age=15 }");
        Console.WriteLine(await this._kernel.InvokePromptAsync("My cat is 15 years old now, please update my pet information.", new KernelArguments(settings)));
        Console.WriteLine("\nExpected payload: { pet_type=cat, hunts=true }");
        Console.WriteLine(await this._kernel.InvokePromptAsync("I have a feline pet, she goes out every night hunting mice, please update my pet information.", new KernelArguments(settings)));
        Console.WriteLine("\nExpected payload: { pet_type=cat, age=3, hunts=true }");
        Console.WriteLine(await this._kernel.InvokePromptAsync("I have a new 3 year old cat who chases birds and barks, please create my pet information.", new KernelArguments(settings)));
    }

    /// <summary>
    /// This sample demonstrates how to invoke an OpenAPI function with arguments for payload using anyOf.
    /// </summary>
    [Fact]
    public async Task InvokeOpenApiFunctionWithArgumentsForPayloadAnyOfAsync()
    {
        // Load an Open API document for the Event Utils service
        using Stream stream = File.OpenRead("Resources/Plugins/PetsPlugin/anyOfV3.json");

        // Import an OpenAPI document as SK plugin
        KernelPlugin plugin = await this._kernel.ImportPluginFromOpenApiAsync("Pets", stream, new OpenApiFunctionExecutionParameters(this._httpClient)
        {
            EnableDynamicPayload = false // Disable dynamic payload construction. It is enabled by default.
        });

        // Example of how to have the updatePater function invoked by the AI
        OpenAIPromptExecutionSettings settings = new() { FunctionChoiceBehavior = FunctionChoiceBehavior.Auto() };
        Console.WriteLine("\nExpected payload: { pet_type=Dog, nickname=Fido }");
        Console.WriteLine(await this._kernel.InvokePromptAsync("My new dog is named Fido he is 2 years old, please create my pet information.", new KernelArguments(settings)));
        Console.WriteLine("\nExpected payload: { pet_type=Dog, nickname=Spot age=1 hunts=true }");
        Console.WriteLine(await this._kernel.InvokePromptAsync("My 1 year old dog is called Spot, he likes to hunt for rabbits, please update my pet information.", new KernelArguments(settings)));
        Console.WriteLine("\nExpected payload: { pet_type=Cat, age=15 }");
        Console.WriteLine(await this._kernel.InvokePromptAsync("My cat is 15 years old now, please update my pet information.", new KernelArguments(settings)));
        Console.WriteLine("\nExpected payload: { pet_type=Cat, nick_name=Fluffy }");
        Console.WriteLine(await this._kernel.InvokePromptAsync("I have a new feline pet called Fluffy, please create my pet information.", new KernelArguments(settings)));
    }

    protected override void Dispose(bool disposing)
    {
        base.Dispose(disposing);
        this._httpClient.Dispose();
    }

    private sealed class StubHttpHandler : DelegatingHandler
    {
        private readonly Action<string> _requestPayloadHandler;
        private readonly JsonSerializerOptions _options;

        public StubHttpHandler(Action<string> requestPayloadHandler) : base()
        {
            this._requestPayloadHandler = requestPayloadHandler;
            this._options = new JsonSerializerOptions { WriteIndented = true };
        }

        protected override async Task<HttpResponseMessage> SendAsync(HttpRequestMessage? request, CancellationToken cancellationToken)
        {
            var requestJson = await request!.Content!.ReadFromJsonAsync<JsonElement>(cancellationToken);

            this._requestPayloadHandler(JsonSerializer.Serialize(requestJson, this._options));

            return new HttpResponseMessage(System.Net.HttpStatusCode.OK)
            {
                Content = new StringContent("Success", Encoding.UTF8, "application/json")
            };
        }
    }
}
