// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel;
using RepoUtils;

namespace LLamaExample;

internal class Program
{
    const string ModelPath = "C:\\Experiment\\bot\\BotSharp\\model\\wizardLM-7B.ggmlv3.q4_0.bin"; //model-path, download from here: https://huggingface.co/TheBloke/wizardLM-7B-GGML/tree/main
    static async Task Main(string[] args)
    {
        //run text completion
        await RunQaAsync();

        Console.ReadLine();
    }

    
    
    public static async Task RunQaAsync()
    {
        Console.WriteLine("======== LLama QA AI ========");
        Console.WriteLine("type 'exit' to close");
        List<Chat> chatList = new List<Chat>();
        IKernel kernel = new KernelBuilder()
            .WithLogger(ConsoleLogger.Log)
            .WithLLamaTextCompletionService("LLamaChat",ModelPath, new List<string>() { "A:" })
            .Build();

        const string FunctionDefinition = "{{$history}} Question: {{$input}}; Answer:";


        var questionAnswerFunction = kernel.CreateSemanticFunction(FunctionDefinition);
        while (true)
        {
            Console.Write("Q: ");
            var question = Console.ReadLine();
            if (string.IsNullOrEmpty(question)) continue;
            if (question == "exit")
            {
                Console.WriteLine("exiting app...");
                break;
            }
            var context = new ContextVariables();
            context.Set("input", question);
            context.Set("history", GetHistory());
            try
            {
                var result = await kernel.RunAsync(context, questionAnswerFunction);
                var res = result.Result.Replace("A:", string.Empty);
                Console.WriteLine($"A: {res}");
                chatList.Add(new Chat() { Question = question, Answer = res });
            }
            catch (Exception ex)
            {
                Console.WriteLine("try another question..");
            }

            /*
            foreach (var modelResult in result.ModelResults)
            {
                var resp = modelResult.GetLLamaResult();
                Console.WriteLine(resp.AsJson());
            }*/
            
        }


        string GetHistory()
        {
            var history = string.Empty;
            foreach (var chat in chatList)
            {
                history += $"Question: {chat.Question}; Answer:{chat.Answer};\n";
            }
            return history;
        }
    }
}

public class Chat
{
    public string Question { get; set; }
    public string Answer { get; set; }
}
