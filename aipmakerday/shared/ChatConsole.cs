// Comment to disable streamed responses
#define AGENT_STREAMING

namespace SemanticKernel.HelloAgents.Internal;

using Microsoft.SemanticKernel.Agents;

internal static class ChatConsole
{
    private const ConsoleColor InputColor = ConsoleColor.White;
    private const ConsoleColor PromptColor = ConsoleColor.Yellow;
    private const ConsoleColor AgentColor = ConsoleColor.Cyan;

    public static async Task ChatAsync(Agent agent)
    {
        AgentThread? thread = null;
        string input;
        while (!string.IsNullOrWhiteSpace(input = ReadInput("Input> ") ?? string.Empty))
        {
            Console.WriteLine();

            // Streaming and non-streaming responses each use their own content model,
            // but the invocation pattern is equivalent.
#if AGENT_STREAMING
            var response = agent.InvokeStreamingAsync(input, thread);
#else
            var response = agent.InvokeAsync(input, thread);
#endif

            bool isResponding = false;
            await foreach (var item in response)
            {
                thread ??= item.Thread;
                if (!isResponding)
                {
                    isResponding = true;
                    WriteLine(PromptColor, "Agent>");
                }
                Write(AgentColor, item.Message.Content);
            }

            Console.WriteLine(Environment.NewLine);
        }
    }

    private static string? ReadInput(string prmopt)
    {
        Write(PromptColor, "Input> ");
        Console.ForegroundColor = InputColor;
        try
        {
            return Console.ReadLine();
        }
        finally
        {
            Console.ResetColor();
        }
    }

    private static void Write(ConsoleColor color, string? message)
    {
        Console.ForegroundColor = color;
        try
        {
            Console.Write(message);
        }
        finally
        {
            Console.ResetColor();
        }
    }

    private static void WriteLine(ConsoleColor color, string? message)
    {
        Write(color, message);
        Write(color, Environment.NewLine);
    }
}
