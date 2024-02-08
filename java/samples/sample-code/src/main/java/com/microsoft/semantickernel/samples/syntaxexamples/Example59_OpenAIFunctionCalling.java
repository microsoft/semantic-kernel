package com.microsoft.semantickernel.samples.syntaxexamples;

import com.azure.ai.openai.OpenAIAsyncClient;
import com.azure.ai.openai.OpenAIClientBuilder;
import com.azure.core.credential.AzureKeyCredential;
import com.azure.core.credential.KeyCredential;
import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.aiservices.openai.chatcompletion.OpenAIChatCompletion;
import com.microsoft.semantickernel.chatcompletion.ChatCompletionService;
import com.microsoft.semantickernel.orchestration.PromptExecutionSettings;
import com.microsoft.semantickernel.orchestration.ToolCallBehavior;
import com.microsoft.semantickernel.plugin.KernelFunctionFactory;
import com.microsoft.semantickernel.plugin.KernelPlugin;
import com.microsoft.semantickernel.plugin.KernelPluginFactory;
import com.microsoft.semantickernel.plugin.annotations.DefineKernelFunction;
import com.microsoft.semantickernel.plugin.annotations.KernelFunctionParameter;
import com.microsoft.semantickernel.semanticfunctions.KernelFunctionFromPrompt;

import java.time.Instant;
import java.util.List;

public class Example59_OpenAIFunctionCalling {

    private static final String CLIENT_KEY = System.getenv("CLIENT_KEY");
    private static final String AZURE_CLIENT_KEY = System.getenv("AZURE_CLIENT_KEY");

    // Only required if AZURE_CLIENT_KEY is set
    private static final String CLIENT_ENDPOINT = System.getenv("CLIENT_ENDPOINT");
    private static final String MODEL_ID = System.getenv()
        .getOrDefault("MODEL_ID", "gpt-35-turbo-2");

    public static class Plugin {
        @DefineKernelFunction(name = "getCurrentTime", description = "Gets the current time for a city")
        public String getCurrentTime() {
            return Instant.now().toString();
        }
        @DefineKernelFunction(name = "getWeatherForCity", description = "Gets current weather of a city")
        public String getWeatherForCity(@KernelFunctionParameter(name="cityName", description = "City name")
                                                String cityName) {
            return switch (cityName) {
                case "Boston" -> "61 and rainy";
                case "London" -> "55 and cloudy";
                case "Miami" -> "80 and sunny";
                case "Paris" -> "60 and rainy";
                case "Tokyo" -> "50 and sunny";
                case "Sydney" -> "75 and sunny";
                case "Tel Aviv" -> "80 and sunny";
                default -> "31 and snowing";
            };
        }
    }

    public static void main(String[] args) throws NoSuchMethodException {
        System.out.println("======== Open AI - ChatGPT ========");

        OpenAIAsyncClient client;

        if (AZURE_CLIENT_KEY != null) {
            client = new OpenAIClientBuilder()
                .credential(new AzureKeyCredential(AZURE_CLIENT_KEY))
                .endpoint(CLIENT_ENDPOINT)
                .buildAsyncClient();

        } else {
            client = new OpenAIClientBuilder()
                .credential(new KeyCredential(CLIENT_KEY))
                .buildAsyncClient();
        }

        ChatCompletionService chat = OpenAIChatCompletion.builder()
            .withModelId(MODEL_ID)
            .withOpenAIAsyncClient(client)
            .build();

        KernelPlugin plugin = KernelPluginFactory.createFromFunctions("plugin", List.of(
                KernelFunctionFactory.createFromMethod(Plugin.class.getMethod("getCurrentTime"),
                        new Plugin(), "getCurrentTime", null, null, null),
                KernelFunctionFactory.createFromMethod(Plugin.class.getMethod("getWeatherForCity", String.class),
                        new Plugin(), "getWeatherForCity", null, null, null)
        ));

        var kernel = Kernel.builder()
                .withAIService(ChatCompletionService.class, chat)
                .build();

        kernel.getPlugins().add(plugin);

        var function = KernelFunctionFromPrompt.builder()
            .withTemplate("Given the current time of day and weather, what is the likely color of the sky in Boston?")
            .withDefaultExecutionSettings(
                PromptExecutionSettings.builder()
                        .withTemperature(0.4)
                        .withTopP(1)
                        .withMaxTokens(100)
                        .withToolCallBehavior(new ToolCallBehavior().autoInvoke(true))
                        .build()
            )
            .build();

        var result = kernel.invokeAsync(function, null, String.class).block();
        System.out.print(result.getResult());
    }

}
