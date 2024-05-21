package com.microsoft.semantickernel.samples.syntaxexamples;

import com.azure.core.credential.AzureKeyCredential;
import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.aiservices.huggingface.HuggingFaceClient;
import com.microsoft.semantickernel.aiservices.huggingface.services.HuggingFaceChatCompletionService;
import com.microsoft.semantickernel.aiservices.huggingface.services.HuggingFaceTextGenerationService;
import com.microsoft.semantickernel.semanticfunctions.KernelFunctionArguments;
import com.microsoft.semantickernel.semanticfunctions.KernelFunctionFromPrompt;
import com.microsoft.semantickernel.services.chatcompletion.ChatCompletionService;
import com.microsoft.semantickernel.services.textcompletion.TextGenerationService;

public class Example20_HuggingFace {

    private static final String HUGGINGFACE_CLIENT_KEY = System.getenv("HUGGINGFACE_CLIENT_KEY");
    private static final String HUGGINGFACE_CLIENT_ENDPOINT = System.getenv(
        "HUGGINGFACE_CLIENT_ENDPOINT");

    public static void main(String[] args) {
        runConversationApiExampleAsync();
        runInferenceApiExampleAsync();
    }

    public static void runInferenceApiExampleAsync() {
        System.out.println("\n======== HuggingFace Inference API example ========\n");

        HuggingFaceClient client = HuggingFaceClient.builder()
            .credential(new AzureKeyCredential(HUGGINGFACE_CLIENT_KEY))
            .endpoint(HUGGINGFACE_CLIENT_ENDPOINT)
            .build();

        var chatCompletion = HuggingFaceTextGenerationService.builder()
            .withModelId("gpt2-24")
            .withHuggingFaceClient(client)
            .build();

        Kernel kernel = Kernel.builder()
            .withAIService(TextGenerationService.class, chatCompletion)
            .build();

        var questionAnswerFunction = KernelFunctionFromPrompt.builder()
            .withTemplate("Question: {{$input}}; Answer:")
            .build();

        var result = kernel.invokeAsync(questionAnswerFunction)
            .withArguments(
                KernelFunctionArguments.builder()
                    .withVariable("input", "What is New York?")
                    .build()
            )
            .withResultType(String.class)
            .block();

        System.out.println(result.getResult());
    }


    public static void runConversationApiExampleAsync() {
        System.out.println("\n======== HuggingFace Inference API example ========\n");

        HuggingFaceClient client = HuggingFaceClient.builder()
            .credential(new AzureKeyCredential(HUGGINGFACE_CLIENT_KEY))
            .endpoint(HUGGINGFACE_CLIENT_ENDPOINT)
            .build();

        var chatCompletion = HuggingFaceChatCompletionService.builder()
            .withModelId("msft-dialogpt-medium-13")
            .withHuggingFaceClient(client)
            .build();

        Kernel kernel = Kernel.builder()
            .withAIService(ChatCompletionService.class, chatCompletion)
            .build();

        var questionAnswerFunction = KernelFunctionFromPrompt.builder()
            .withTemplate("""
                <message role="system">Assistant is a large language model that answers questions.</message>
                <message role="assistant">What is your question?</message>
                <message role="user">{{$input}}</message>
                """)
            .build();

        var result = kernel.invokeAsync(questionAnswerFunction)
            .withArguments(
                KernelFunctionArguments.builder()
                    .withVariable("input", "What is New York?")
                    .build()
            )
            .withResultType(String.class)
            .block();

        System.out.println(result.getResult());
    }


    /*
    /// <summary>
    /// This example uses HuggingFace Inference API to access hosted models.
    /// More information here: <see href="https://huggingface.co/inference-api"/>
    /// </summary>
    [Fact]

    [RetryFact(typeof(HttpOperationException))]
    public async Task RunInferenceApiEmbeddingAsync()
    {
        this.System.out.println("\n======= Hugging Face Inference API - Embedding Example ========\n");

        Kernel kernel = Kernel.CreateBuilder()
            .AddHuggingFaceTextEmbeddingGeneration(
                model: TestConfiguration.HuggingFace.EmbeddingModelId,
        apiKey: TestConfiguration.HuggingFace.ApiKey)
            .Build();

        var embeddingGenerator = kernel.GetRequiredService<ITextEmbeddingGenerationService>();

        // Generate embeddings for each chunk.
        var embeddings = await embeddingGenerator.GenerateEmbeddingsAsync(["John: Hello, how are you?\nRoger: Hey, I'm Roger!"]);

        this.System.out.println($"Generated {embeddings.Count} embeddings for the provided text");
    }

    [RetryFact(typeof(HttpOperationException))]
    public async Task RunStreamingExampleAsync()
    {
        System.out.println("\n======== HuggingFace zephyr-7b-beta streaming example ========\n");

        const string Model = "HuggingFaceH4/zephyr-7b-beta";

        Kernel kernel = Kernel.CreateBuilder()
            .AddHuggingFaceTextGeneration(
                model: Model,
        apiKey: TestConfiguration.HuggingFace.ApiKey)
            .Build();

        var settings = new HuggingFacePromptExecutionSettings { UseCache = false };

        var questionAnswerFunction = kernel.CreateFunctionFromPrompt("Question: {{$input}}; Answer:", new HuggingFacePromptExecutionSettings
        {
            UseCache = false
        });

        await foreach (string text in kernel.InvokePromptStreamingAsync<string>("Question: {{$input}}; Answer:", new(settings) { ["input"] = "What is New York?" }))
        {
            this.Write(text);
        }
    }

    /// <summary>
    /// This example uses HuggingFace Llama 2 model and local HTTP server from Semantic Kernel repository.
    /// How to setup local HTTP server: <see href="https://github.com/microsoft/semantic-kernel/blob/main/samples/apps/hugging-face-http-server/README.md"/>.
    /// <remarks>
    /// Additional access is required to download Llama 2 model and run it locally.
    /// How to get access:
    /// 1. Visit <see href="https://ai.meta.com/resources/models-and-libraries/llama-downloads/"/> and complete request access form.
    /// 2. Visit <see href="https://huggingface.co/meta-llama/Llama-2-7b-hf"/> and complete form "Access Llama 2 on Hugging Face".
    /// Note: Your Hugging Face account email address MUST match the email you provide on the Meta website, or your request will not be approved.
    /// </remarks>
    /// </summary>
    [Fact(Skip = "Requires local model or Huggingface Pro subscription")]
    public async Task RunLlamaExampleAsync()
    {
        System.out.println("\n======== HuggingFace Llama 2 example ========\n");

        // HuggingFace Llama 2 model: https://huggingface.co/meta-llama/Llama-2-7b-hf
        const string Model = "meta-llama/Llama-2-7b-hf";

        // HuggingFace local HTTP server endpoint
        // const string Endpoint = "http://localhost:5000/completions";

        Kernel kernel = Kernel.CreateBuilder()
            .AddHuggingFaceTextGeneration(
                model: Model,
        //endpoint: Endpoint,
        apiKey: TestConfiguration.HuggingFace.ApiKey)
            .Build();

        var questionAnswerFunction = kernel.CreateFunctionFromPrompt("Question: {{$input}}; Answer:");

        var result = await kernel.InvokeAsync(questionAnswerFunction, new() { ["input"] = "What is New York?" });

        System.out.println(result.GetValue<string>());
    }

    /// <summary>
    /// Follow steps in <see href="https://huggingface.co/docs/text-generation-inference/main/en/quicktour"/> to setup HuggingFace local Text Generation Inference HTTP server.
    /// </summary>
    [Fact(Skip = "Requires TGI (text generation inference) deployment")]
    public async Task RunTGI_ChatCompletionAsync()
    {
        System.out.println("\n======== HuggingFace - TGI Chat Completion ========\n");

        // This example was run against one of the chat completion (Message API) supported models from HuggingFace, listed in here: <see href="https://huggingface.co/docs/text-generation-inference/main/en/supported_models"/>
        // Starting a Local Docker i.e:
        // docker run --gpus all --shm-size 1g -p 8080:80 -v "F:\temp\huggingface:/data" ghcr.io/huggingface/text-generation-inference:1.4 --model-id teknium/OpenHermes-2.5-Mistral-7B

        // HuggingFace local HTTP server endpoint
        var endpoint = new Uri("http://localhost:8080");

        const string Model = "teknium/OpenHermes-2.5-Mistral-7B";

        Kernel kernel = Kernel.CreateBuilder()
            .AddHuggingFaceChatCompletion(
                model: Model,
        endpoint: endpoint)
            .Build();

        var chatCompletion = kernel.GetRequiredService<IChatCompletionService>();
        var chatHistory = new ChatHistory("You are a helpful assistant.")
        {
            new ChatMessageContent(AuthorRole.User, "What is deep learning?")
        };

        var result = await chatCompletion.GetChatMessageContentAsync(chatHistory);

        System.out.println(result.Role);
        System.out.println(result.Content);
    }

    /// <summary>
    /// Follow steps in <see href="https://huggingface.co/docs/text-generation-inference/main/en/quicktour"/> to setup HuggingFace local Text Generation Inference HTTP server.
    /// </summary>
    [Fact(Skip = "Requires TGI (text generation inference) deployment")]
    public async Task RunTGI_StreamingChatCompletionAsync()
    {
        System.out.println("\n======== HuggingFace - TGI Chat Completion Streaming ========\n");

        // This example was run against one of the chat completion (Message API) supported models from HuggingFace, listed in here: <see href="https://huggingface.co/docs/text-generation-inference/main/en/supported_models"/>
        // Starting a Local Docker i.e:
        // docker run --gpus all --shm-size 1g -p 8080:80 -v "F:\temp\huggingface:/data" ghcr.io/huggingface/text-generation-inference:1.4 --model-id teknium/OpenHermes-2.5-Mistral-7B

        // HuggingFace local HTTP server endpoint
        var endpoint = new Uri("http://localhost:8080");

        const string Model = "teknium/OpenHermes-2.5-Mistral-7B";

        Kernel kernel = Kernel.CreateBuilder()
            .AddHuggingFaceChatCompletion(
                model: Model,
        endpoint: endpoint)
            .Build();

        var chatCompletion = kernel.GetRequiredService<IChatCompletionService>();
        var chatHistory = new ChatHistory("You are a helpful assistant.")
        {
            new ChatMessageContent(AuthorRole.User, "What is deep learning?")
        };

        AuthorRole? role = null;
        await foreach (var chatMessageChunk in chatCompletion.GetStreamingChatMessageContentsAsync(chatHistory))
        {
            if (role is null)
            {
                role = chatMessageChunk.Role;
                Write(role);
            }
            Write(chatMessageChunk.Content);
        }
    }

    public Example20_HuggingFace(ITestOutputHelper output) : base(output)
    {
    }


     */
}
