#r "nuget: Microsoft.Extensions.DependencyInjection"
#r "nuget: Microsoft.Extensions.Http"
#r "nuget: Microsoft.Extensions.Logging.Console"
#r "nuget: Microsoft.Extensions.Logging"
#r "nuget: Microsoft.SemanticKernel.Connectors.HuggingFace, 1.12.0-preview"


open Microsoft.SemanticKernel
open Microsoft.SemanticKernel.ChatCompletion
open Microsoft.Extensions.Logging
open System
open Microsoft.Extensions.DependencyInjection
open Microsoft.Extensions.Http.Logging
open System.Net.Http
open System.Net.Http.Json
open Microsoft.Extensions.Http
open System.Threading.Tasks

let builder =
    // TODO: request your API key in your 🤗 hugging face private settings
    let API_KEY = "TODO_REPLACE_ME"
    let MODEL_ID = "microsoft/Phi-3-mini-4k-instruct" // pick the model you prefer!
    let API_URL = $"https://api-inference.huggingface.co/"

    let b = Kernel.CreateBuilder().AddHuggingFaceChatCompletion(
            MODEL_ID,
            API_URL |> Uri, 
            API_KEY)

    b.Services
        .AddLogging(fun b ->

            b.AddFilter("System.Net.Http.HttpClient", 
                LogLevel.Debug) |> ignore
            b.AddFilter("Microsoft.AspNetCore.HttpLogging.HttpLoggingMiddleware", 
                LogLevel.Debug) |> ignore
            
            b.AddConsole() |> ignore
            b.SetMinimumLevel(LogLevel.Information) |> ignore

            |> ignore
        )|> ignore

    b

let kernel = builder.Build()

let chatCompletion = 
    kernel.GetRequiredService<IChatCompletionService>()

let chatHistory = 
    new ChatHistory("""
        You are an expert in F#, dotnet, aspnet and .fsx and scripting with nuget! 
        always reply in this example format for conversations

        question: `how do i declare a record in F#?`
        ---
        answer:
        ```fsharp
        type Car = { Brand: string }
        ```
        
        try to keep answers as short and relevant as possible, if you do NOT know, 
        ASK for more details to the user and wait for the next input
        """)

let mutable exit = false

while not exit do 
    printfn "I am an F# assistant, ask me anything!"

    let question = System.Console.ReadLine()
    chatHistory.Add(new ChatMessageContent(AuthorRole.Assistant, question))

    let result = 
        chatCompletion.GetChatMessageContentAsync(chatHistory)
        |> Async.AwaitTask
        |> Async.RunSynchronously

    Console.WriteLine(result.Role)
    Console.WriteLine(result.Content)

    printfn "another round? y/n"
    printfn "\r\n"
    let reply = Console.ReadKey()
    exit <- reply.KeyChar.ToString().ToLower() <> "y"
