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
import com.microsoft.semantickernel.plugin.KernelPlugin;
import com.microsoft.semantickernel.plugin.KernelPluginFactory;
import com.microsoft.semantickernel.plugin.annotations.DefineKernelFunction;
import com.microsoft.semantickernel.plugin.annotations.KernelFunctionParameter;
import com.microsoft.semantickernel.semanticfunctions.KernelFunctionFromPrompt;
import java.time.Instant;

public class Example59_OpenAIFunctionCalling {

    private static final String CLIENT_KEY = System.getenv("CLIENT_KEY");
    private static final String AZURE_CLIENT_KEY = System.getenv("AZURE_CLIENT_KEY");

    // Only required if AZURE_CLIENT_KEY is set
    private static final String CLIENT_ENDPOINT = System.getenv("CLIENT_ENDPOINT");
    private static final String MODEL_ID = System.getenv()
        .getOrDefault("MODEL_ID", "gpt-35-turbo-2");

    public static class Plugin {
        @DefineKernelFunction(name = "getLatitudeOfCity", description = "Gets the latitude of a given city")
        public String getLatitudeOfCity(
            @KernelFunctionParameter(name = "cityName", description = "City name")
            String cityName) {
            return "1.0";
        }

        @DefineKernelFunction(name = "getLongitudeOfCity", description = "Gets the longitude of a given city")
        public String getLongitudeOfCity(
            @KernelFunctionParameter(name = "cityName", description = "City name")
            String cityName) {
            return "2.0";
        }

        @DefineKernelFunction(name = "getsTheWeatherAtAGivenLocation", description = "Gets the current weather at a given longitude and latitude")
        public String getWeatherForCityAtTime(
            @KernelFunctionParameter(name = "latitude", description = "latitude of the location")
            String latitude,
            @KernelFunctionParameter(name = "longitude", description = "longitude of the location")
            String longitude
        ) {
            return "61 and rainy";
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

        KernelPlugin plugin = KernelPluginFactory.createFromObject(new Plugin(), "plugin");

        var kernel = Kernel.builder()
            .withAIService(ChatCompletionService.class, chat)
            .build();

        kernel.getPlugins().add(plugin);

        var function = KernelFunctionFromPrompt.builder()
            .withTemplate(
                "What is the current color of the sky in Thrapston?")
            .withDefaultExecutionSettings(
                PromptExecutionSettings.builder()
                    .withTemperature(0.4)
                    .withTopP(1)
                    .withMaxTokens(100)
                    .withToolCallBehavior(
                        new ToolCallBehavior().autoInvoke(true))
                    .build()
            )
            .build();

        var result = kernel.invokeAsync(function, null, String.class).block();
        System.out.print(result.getResult());
    }

}
