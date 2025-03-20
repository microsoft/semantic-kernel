// Copyright (c) Microsoft. All rights reserved.

using System.ClientModel;
using System.ComponentModel;
using System.Text;
using System.Text.Json;
using Azure.AI.OpenAI;
using Microsoft.Extensions.Configuration;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using OpenAI.RealtimeConversation;

namespace OpenAIRealtime;

#pragma warning disable OPENAI002

/// <summary>
/// Demonstrates the use of the OpenAI Realtime API with function calling and Semantic Kernel.
/// For conversational experiences, it is recommended to use <see cref="RealtimeConversationClient"/> from the Azure/OpenAI SDK.
/// Since the OpenAI Realtime API supports function calling, the example shows how to combine it with Semantic Kernel plugins and functions.
/// </summary>
internal sealed class Program
{
    public static async Task Main(string[] args)
    {
        // Retrieve the RealtimeConversationClient based on the available OpenAI or Azure OpenAI configuration.
        var realtimeConversationClient = GetRealtimeConversationClient();

        // Build kernel.
        var kernel = Kernel.CreateBuilder().Build();

        // Import plugin.
        kernel.ImportPluginFromType<WeatherPlugin>();

        // Start a new conversation session.
        using RealtimeConversationSession session = await realtimeConversationClient.StartConversationSessionAsync();

        // Initialize session options.
        // Session options control connection-wide behavior shared across all conversations,
        // including audio input format and voice activity detection settings.
        ConversationSessionOptions sessionOptions = new()
        {
            Voice = ConversationVoice.Alloy,
            InputAudioFormat = ConversationAudioFormat.Pcm16,
            OutputAudioFormat = ConversationAudioFormat.Pcm16,
            InputTranscriptionOptions = new()
            {
                Model = "whisper-1",
            },
        };

        // Add plugins/function from kernel as session tools.
        foreach (var tool in ConvertFunctions(kernel))
        {
            sessionOptions.Tools.Add(tool);
        }

        // If any tools are available, set tool choice to "auto".
        if (sessionOptions.Tools.Count > 0)
        {
            sessionOptions.ToolChoice = ConversationToolChoice.CreateAutoToolChoice();
        }

        // Configure session with defined options.
        await session.ConfigureSessionAsync(sessionOptions);

        // Items such as user, assistant, or system messages, as well as input audio, can be sent to the session.
        // An example of sending user message to the session.
        // ConversationItem can be constructed from Microsoft.SemanticKernel.ChatMessageContent if needed by mapping the relevant fields.
        await session.AddItemAsync(
            ConversationItem.CreateUserMessage(["I'm trying to decide what to wear on my trip."]));

        // Use audio file that contains a recorded question: "What's the weather like in San Francisco, California?"
        string inputAudioPath = FindFile("Assets\\realtime_whats_the_weather_pcm16_24khz_mono.wav");
        using Stream inputAudioStream = File.OpenRead(inputAudioPath);

        // An example of sending input audio to the session.
        await session.SendInputAudioAsync(inputAudioStream);

        // Initialize dictionaries to store streamed audio responses and function arguments.
        Dictionary<string, MemoryStream> outputAudioStreamsById = [];
        Dictionary<string, StringBuilder> functionArgumentBuildersById = [];

        // Define a loop to receive conversation updates in the session.
        await foreach (ConversationUpdate update in session.ReceiveUpdatesAsync())
        {
            // Notification indicating the start of the conversation session.
            if (update is ConversationSessionStartedUpdate sessionStartedUpdate)
            {
                Console.WriteLine($"<<< Session started. ID: {sessionStartedUpdate.SessionId}");
                Console.WriteLine();
            }

            // Notification indicating the start of detected voice activity.
            if (update is ConversationInputSpeechStartedUpdate speechStartedUpdate)
            {
                Console.WriteLine(
                    $"  -- Voice activity detection started at {speechStartedUpdate.AudioStartTime}");
            }

            // Notification indicating the end of detected voice activity.
            if (update is ConversationInputSpeechFinishedUpdate speechFinishedUpdate)
            {
                Console.WriteLine(
                    $"  -- Voice activity detection ended at {speechFinishedUpdate.AudioEndTime}");
            }

            // Notification indicating the start of item streaming, such as a function call or response message.
            if (update is ConversationItemStreamingStartedUpdate itemStreamingStartedUpdate)
            {
                Console.WriteLine("  -- Begin streaming of new item");
                if (!string.IsNullOrEmpty(itemStreamingStartedUpdate.FunctionName))
                {
                    Console.Write($"    {itemStreamingStartedUpdate.FunctionName}: ");
                }
            }

            // Notification about item streaming delta, which may include audio transcript, audio bytes, or function arguments.
            if (update is ConversationItemStreamingPartDeltaUpdate deltaUpdate)
            {
                Console.Write(deltaUpdate.AudioTranscript);
                Console.Write(deltaUpdate.Text);
                Console.Write(deltaUpdate.FunctionArguments);

                // Handle audio bytes.
                if (deltaUpdate.AudioBytes is not null)
                {
                    if (!outputAudioStreamsById.TryGetValue(deltaUpdate.ItemId, out MemoryStream? value))
                    {
                        value = new MemoryStream();
                        outputAudioStreamsById[deltaUpdate.ItemId] = value;
                    }

                    value.Write(deltaUpdate.AudioBytes);
                }

                // Handle function arguments.
                if (!functionArgumentBuildersById.TryGetValue(deltaUpdate.ItemId, out StringBuilder? arguments))
                {
                    functionArgumentBuildersById[deltaUpdate.ItemId] = arguments = new();
                }

                if (!string.IsNullOrWhiteSpace(deltaUpdate.FunctionArguments))
                {
                    arguments.Append(deltaUpdate.FunctionArguments);
                }
            }

            // Notification indicating the end of item streaming, such as a function call or response message.
            // At this point, audio transcript can be displayed on console, or a function can be called with aggregated arguments.
            if (update is ConversationItemStreamingFinishedUpdate itemStreamingFinishedUpdate)
            {
                Console.WriteLine();
                Console.WriteLine($"  -- Item streaming finished, item_id={itemStreamingFinishedUpdate.ItemId}");

                // If an item is a function call, invoke a function with provided arguments.
                if (itemStreamingFinishedUpdate.FunctionCallId is not null)
                {
                    Console.WriteLine($"    + Responding to tool invoked by item: {itemStreamingFinishedUpdate.FunctionName}");

                    // Parse function name.
                    var (functionName, pluginName) = ParseFunctionName(itemStreamingFinishedUpdate.FunctionName);

                    // Deserialize arguments.
                    var argumentsString = functionArgumentBuildersById[itemStreamingFinishedUpdate.ItemId].ToString();
                    var arguments = DeserializeArguments(argumentsString);

                    // Create a function call content based on received data.
                    var functionCallContent = new FunctionCallContent(
                        functionName: functionName,
                        pluginName: pluginName,
                        id: itemStreamingFinishedUpdate.FunctionCallId,
                        arguments: arguments);

                    // Invoke a function.
                    var resultContent = await functionCallContent.InvokeAsync(kernel);

                    // Create a function call output conversation item with function call result.
                    ConversationItem functionOutputItem = ConversationItem.CreateFunctionCallOutput(
                        callId: itemStreamingFinishedUpdate.FunctionCallId,
                        output: ProcessFunctionResult(resultContent.Result));

                    // Send function call output conversation item to the session, so the model can use it for further processing.
                    await session.AddItemAsync(functionOutputItem);
                }
                // If an item is a response message, output it to the console.
                else if (itemStreamingFinishedUpdate.MessageContentParts?.Count > 0)
                {
                    Console.Write($"    + [{itemStreamingFinishedUpdate.MessageRole}]: ");

                    foreach (ConversationContentPart contentPart in itemStreamingFinishedUpdate.MessageContentParts)
                    {
                        Console.Write(contentPart.AudioTranscript);
                    }

                    Console.WriteLine();
                }
            }

            // Notification indicating the completion of transcription from input audio.
            if (update is ConversationInputTranscriptionFinishedUpdate transcriptionCompletedUpdate)
            {
                Console.WriteLine();
                Console.WriteLine($"  -- User audio transcript: {transcriptionCompletedUpdate.Transcript}");
                Console.WriteLine();
            }

            // Notification about completed model response turn.
            if (update is ConversationResponseFinishedUpdate turnFinishedUpdate)
            {
                Console.WriteLine($"  -- Model turn generation finished. Status: {turnFinishedUpdate.Status}");

                // If the created session items contain a function name, it indicates a function call result has been provided,
                // and response updates can begin.
                if (turnFinishedUpdate.CreatedItems.Any(item => item.FunctionName?.Length > 0))
                {
                    Console.WriteLine("  -- Ending client turn for pending tool responses");

                    await session.StartResponseAsync();
                }
                // Otherwise, the model's response is provided, signaling that updates can be stopped.
                else
                {
                    break;
                }
            }

            // Notification about error in conversation session.
            if (update is ConversationErrorUpdate errorUpdate)
            {
                Console.WriteLine();
                Console.WriteLine($"ERROR: {errorUpdate.Message}");
                break;
            }
        }

        // Output the size of received audio data and dispose streams.
        foreach ((string itemId, Stream outputAudioStream) in outputAudioStreamsById)
        {
            Console.WriteLine($"Raw audio output for {itemId}: {outputAudioStream.Length} bytes");

            outputAudioStream.Dispose();
        }

        // Output example:
        //<<< Session started. ID: session_Abc123...

        //-- Voice activity detection started at 00:00:00.6400000
        //-- Voice activity detection ended at 00:00:02.9760000
        //-- Begin streaming of new item
        //  WeatherPlugin - GetWeatherForCity: { "cityName":"San Francisco"}
        //      --Item streaming finished, item_id = item_Abc123...
        //        + Responding to tool invoked by item: WeatherPlugin - GetWeatherForCity
        //      -- Model turn generation finished. Status: completed
        //      -- Ending client turn for pending tool responses

        //      -- User audio transcript: What's the weather like in San Francisco, California?

        //      -- Begin streaming of new item
        //    It's 70°F and sunny in San Francisco. Sounds like perfect weather for a light jacket or a sweater. Enjoy your trip!
        //      -- Item streaming finished, item_id = item_Abc123...
        //        + [assistant]: It's 70°F and sunny in San Francisco. Sounds like perfect weather for a light jacket or a sweater. Enjoy your trip!

        //      -- Model turn generation finished.Status: completed

        //    Raw audio output for item_Abc123...: 542400 bytes
    }

    /// <summary>A sample plugin to get a weather.</summary>
    private sealed class WeatherPlugin
    {
        [KernelFunction]
        [Description("Gets the current weather for the specified city in Fahrenheit.")]
        public static string GetWeatherForCity([Description("City name without state/country.")] string cityName)
        {
            return cityName switch
            {
                "Boston" => "61 and rainy",
                "London" => "55 and cloudy",
                "Miami" => "80 and sunny",
                "Paris" => "60 and rainy",
                "Tokyo" => "50 and sunny",
                "Sydney" => "75 and sunny",
                "Tel Aviv" => "80 and sunny",
                "San Francisco" => "70 and sunny",
                _ => throw new ArgumentException($"Data is not available for {cityName}."),
            };
        }
    }

    #region Helpers

    /// <summary>Helper method to parse a function name for compatibility with Semantic Kernel plugins/functions.</summary>
    private static (string FunctionName, string? PluginName) ParseFunctionName(string fullyQualifiedName)
    {
        const string FunctionNameSeparator = "-";

        string? pluginName = null;
        string functionName = fullyQualifiedName;

        int separatorPos = fullyQualifiedName.IndexOf(FunctionNameSeparator, StringComparison.Ordinal);
        if (separatorPos >= 0)
        {
            pluginName = fullyQualifiedName.AsSpan(0, separatorPos).Trim().ToString();
            functionName = fullyQualifiedName.AsSpan(separatorPos + FunctionNameSeparator.Length).Trim().ToString();
        }

        return (functionName, pluginName);
    }

    /// <summary>Helper method to deserialize function arguments.</summary>
    private static KernelArguments? DeserializeArguments(string argumentsString)
    {
        var arguments = JsonSerializer.Deserialize<KernelArguments>(argumentsString);

        if (arguments is not null)
        {
            // Iterate over copy of the names to avoid mutating the dictionary while enumerating it
            var names = arguments.Names.ToArray();
            foreach (var name in names)
            {
                arguments[name] = arguments[name]?.ToString();
            }
        }

        return arguments;
    }

    /// <summary>Helper method to process function result in order to provide it to the model as string.</summary>
    private static string? ProcessFunctionResult(object? functionResult)
    {
        if (functionResult is string stringResult)
        {
            return stringResult;
        }

        return JsonSerializer.Serialize(functionResult);
    }

    /// <summary>Helper method to convert Kernel plugins/function to realtime session conversation tools.</summary>
    private static IEnumerable<ConversationTool> ConvertFunctions(Kernel kernel)
    {
        foreach (var plugin in kernel.Plugins)
        {
            var functionsMetadata = plugin.GetFunctionsMetadata();

            foreach (var metadata in functionsMetadata)
            {
                var toolDefinition = metadata.ToOpenAIFunction().ToFunctionDefinition(false);

                yield return new ConversationFunctionTool(name: toolDefinition.FunctionName)
                {
                    Description = toolDefinition.FunctionDescription,
                    Parameters = toolDefinition.FunctionParameters
                };
            }
        }
    }

    /// <summary>Helper method to get a file path.</summary>
    private static string FindFile(string fileName)
    {
        for (string currentDirectory = Directory.GetCurrentDirectory();
             currentDirectory != null && currentDirectory != Path.GetPathRoot(currentDirectory);
             currentDirectory = Directory.GetParent(currentDirectory)?.FullName!)
        {
            string filePath = Path.Combine(currentDirectory, fileName);
            if (File.Exists(filePath))
            {
                return filePath;
            }
        }

        throw new FileNotFoundException($"File '{fileName}' not found.");
    }

    /// <summary>
    /// Helper method to get an instance of <see cref="RealtimeConversationClient"/> based on provided
    /// OpenAI or Azure OpenAI configuration.
    /// </summary>
    private static RealtimeConversationClient GetRealtimeConversationClient()
    {
        var config = new ConfigurationBuilder()
            .AddUserSecrets<Program>()
            .AddEnvironmentVariables()
            .Build();

        var openAIOptions = config.GetSection(OpenAIOptions.SectionName).Get<OpenAIOptions>();
        var azureOpenAIOptions = config.GetSection(AzureOpenAIOptions.SectionName).Get<AzureOpenAIOptions>();

        if (openAIOptions is not null && openAIOptions.IsValid)
        {
            return new RealtimeConversationClient(
                model: "gpt-4o-realtime-preview",
                credential: new ApiKeyCredential(openAIOptions.ApiKey));
        }
        else if (azureOpenAIOptions is not null && azureOpenAIOptions.IsValid)
        {
            var client = new AzureOpenAIClient(
                endpoint: new Uri(azureOpenAIOptions.Endpoint),
                credential: new ApiKeyCredential(azureOpenAIOptions.ApiKey));

            return client.GetRealtimeConversationClient(azureOpenAIOptions.DeploymentName);
        }
        else
        {
            throw new Exception("OpenAI/Azure OpenAI configuration was not found.");
        }
    }

    #endregion
}
