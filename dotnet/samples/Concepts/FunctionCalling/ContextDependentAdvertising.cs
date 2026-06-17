// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.OpenAI;

namespace FunctionCalling;

/// <summary>
/// These samples demonstrate how to advertise functions to AI model based on a context.
/// </summary>
public class ContextDependentAdvertising(ITestOutputHelper output) : BaseTest(output)
{
    /// <summary>
    /// This sample demonstrates how to advertise functions to AI model based on the context of the chat history.
    /// It advertises functions to the AI model based on the game state.
    /// For example, if the maze has not been created, advertise the create maze function only to prevent the AI model
    /// from adding traps or treasures to the maze before it is created.
    /// </summary>
    [Fact]
    public async Task AdvertiseFunctionsDependingOnContextPerUserInteractionAsync()
    {
        Kernel kernel = CreateKernel();

        IChatCompletionService chatCompletionService = kernel.GetRequiredService<IChatCompletionService>();

        // Tracking number of iterations to avoid infinite loop.
        int maxIteration = 10;
        int iteration = 0;

        // Define the functions for AI model to call.
        var gameUtils = kernel.ImportPluginFromType<GameUtils>();
        KernelFunction createMaze = gameUtils["CreateMaze"];
        KernelFunction addTraps = gameUtils["AddTrapsToMaze"];
        KernelFunction addTreasures = gameUtils["AddTreasuresToMaze"];
        KernelFunction playGame = gameUtils["PlayGame"];

        ChatHistory chatHistory = [];
        chatHistory.AddUserMessage("I would like to play a maze game with a lot of tricky traps and shiny treasures.");

        // Loop until the game has started or the max iteration is reached.
        while (!chatHistory.Any(item => item.Content?.Contains("Game started.") ?? false) && iteration < maxIteration)
        {
            List<KernelFunction> functionsToAdvertise = [];

            // Decide game state based on chat history.
            bool mazeCreated = chatHistory.Any(item => item.Content?.Contains("Maze created.") ?? false);
            bool trapsAdded = chatHistory.Any(item => item.Content?.Contains("Traps added to the maze.") ?? false);
            bool treasuresAdded = chatHistory.Any(item => item.Content?.Contains("Treasures added to the maze.") ?? false);

            // The maze has not been created yet so advertise the create maze function.
            if (!mazeCreated)
            {
                functionsToAdvertise.Add(createMaze);
            }
            // The maze has been created so advertise the adding traps and treasures functions.
            else if (mazeCreated && (!trapsAdded || !treasuresAdded))
            {
                functionsToAdvertise.Add(addTraps);
                functionsToAdvertise.Add(addTreasures);
            }
            // Both traps and treasures have been added so advertise the play game function.
            else if (treasuresAdded && trapsAdded)
            {
                functionsToAdvertise.Add(playGame);
            }

            // Provide the functions to the AI model.
            OpenAIPromptExecutionSettings settings = new() { FunctionChoiceBehavior = FunctionChoiceBehavior.Required(functionsToAdvertise) };

            // Prompt the AI model.
            ChatMessageContent result = await chatCompletionService.GetChatMessageContentAsync(chatHistory, settings, kernel);

            Console.WriteLine(result);

            iteration++;
        }
    }

    private static Kernel CreateKernel()
    {
        // Create kernel
        IKernelBuilder builder = Kernel.CreateBuilder();

        builder.AddOpenAIChatCompletion(TestConfiguration.OpenAI.ChatModelId, TestConfiguration.OpenAI.ApiKey);

        return builder.Build();
    }

    private sealed class GameUtils
    {
        [KernelFunction]
        public static string CreateMaze() => "Maze created.";

        [KernelFunction]
        public static string AddTrapsToMaze() => "Traps added to the maze.";

        [KernelFunction]
        public static string AddTreasuresToMaze() => "Treasures added to the maze.";

        [KernelFunction]
        public static string PlayGame() => "Game started.";
    }
}
