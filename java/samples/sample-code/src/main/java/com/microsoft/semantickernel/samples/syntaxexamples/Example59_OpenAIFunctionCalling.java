// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.samples.syntaxexamples;

import com.azure.ai.openai.OpenAIAsyncClient;
import com.azure.ai.openai.OpenAIClientBuilder;
import com.azure.core.credential.AzureKeyCredential;
import com.azure.core.credential.KeyCredential;
import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.aiservices.openai.chatcompletion.OpenAIChatCompletion;
import com.microsoft.semantickernel.contextvariables.ContextVariableTypes;
import com.microsoft.semantickernel.orchestration.PromptExecutionSettings;
import com.microsoft.semantickernel.orchestration.ToolCallBehavior;
import com.microsoft.semantickernel.plugin.KernelPlugin;
import com.microsoft.semantickernel.plugin.KernelPluginFactory;
import com.microsoft.semantickernel.semanticfunctions.KernelFunction;
import com.microsoft.semantickernel.semanticfunctions.KernelFunctionFromPrompt;
import com.microsoft.semantickernel.semanticfunctions.annotations.DefineKernelFunction;
import com.microsoft.semantickernel.semanticfunctions.annotations.KernelFunctionParameter;
import com.microsoft.semantickernel.services.chatcompletion.ChatCompletionService;

public class Example59_OpenAIFunctionCalling {

    private static final String CLIENT_KEY = System.getenv("CLIENT_KEY");
    private static final String AZURE_CLIENT_KEY = System.getenv("AZURE_CLIENT_KEY");

    // Only required if AZURE_CLIENT_KEY is set
    private static final String CLIENT_ENDPOINT = System.getenv("CLIENT_ENDPOINT");
    private static final String MODEL_ID = System.getenv()
        .getOrDefault("MODEL_ID", "gpt-35-turbo-2");

    public static void main(String[] args) throws NoSuchMethodException {
        System.out.println("======== Open AI - Function calling ========");

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

        kernel.addPlugin(plugin);

        var function = KernelFunctionFromPrompt.builder()
            .withTemplate(
                "What is the probable current color of the sky in Thrapston?")
            .withDefaultExecutionSettings(
                PromptExecutionSettings.builder()
                    .withTemperature(0.4)
                    .withTopP(1)
                    .withMaxTokens(100)
                    .build())
            .build();

        // Example 1: All kernel functions are enabled to be called by the model
        kernelFunctions(kernel, function);
        // Example 2: A set of functions available to be called by the model
        enableFunctions(kernel, plugin, function);
        // Example 3: A specific function to be called by the model
        requireFunction(kernel, plugin, function);
    }

    public static void kernelFunctions(Kernel kernel, KernelFunction<?> function) {
        System.out.println("======== Kernel functions ========");

        var toolCallBehavior = new ToolCallBehavior()
            .enableKernelFunctions(true)
            .autoInvoke(true);

        var result = kernel
            .invokeAsync(function)
            .withToolCallBehavior(toolCallBehavior)
            .withResultType(ContextVariableTypes.getGlobalVariableTypeForClass(String.class))
            .block();

        System.out.println(result.getResult());
    }

    public static void enableFunctions(Kernel kernel, KernelPlugin plugin,
        KernelFunction<?> function) {
        System.out.println("======== Enable functions ========");

        // Based on coordinates
        var toolCallBehavior = new ToolCallBehavior()
            .enableFunction(plugin.get("getLatitudeOfCity"), true)
            .enableFunction(plugin.get("getLongitudeOfCity"), true)
            .enableFunction(plugin.get("getsTheWeatherAtAGivenLocation"), true)
            .autoInvoke(true);

        var result = kernel
            .invokeAsync(function)
            .withToolCallBehavior(toolCallBehavior)
            .withResultType(ContextVariableTypes.getGlobalVariableTypeForClass(String.class))
            .block();

        System.out.println(result.getResult());
    }

    public static void requireFunction(Kernel kernel, KernelPlugin plugin,
        KernelFunction<?> function) {
        System.out.println("======== Require a function ========");

        // Based on coordinates
        var toolCallBehavior = new ToolCallBehavior()
            .requireFunction(plugin.get("getsTheWeatherForCity"))
            .autoInvoke(true);

        var result = kernel
            .invokeAsync(function)
            .withToolCallBehavior(toolCallBehavior)
            .withResultType(ContextVariableTypes.getGlobalVariableTypeForClass(String.class))
            .block();

        System.out.println(result.getResult());
    }

    public static class Plugin {

        @DefineKernelFunction(name = "getLatitudeOfCity", description = "Gets the latitude of a given city")
        public String getLatitudeOfCity(
            @KernelFunctionParameter(name = "cityName", description = "City name") String cityName) {
            return "1.0";
        }

        @DefineKernelFunction(name = "getLongitudeOfCity", description = "Gets the longitude of a given city")
        public String getLongitudeOfCity(
            @KernelFunctionParameter(name = "cityName", description = "City name") String cityName) {
            return "2.0";
        }

        @DefineKernelFunction(name = "getsTheWeatherAtAGivenLocation", description = "Gets the current weather at a given longitude and latitude")
        public String getWeatherForCityAtTime(
            @KernelFunctionParameter(name = "latitude", description = "latitude of the location") String latitude,
            @KernelFunctionParameter(name = "longitude", description = "longitude of the location") String longitude) {
            return "61 and rainy";
        }

        @DefineKernelFunction(name = "getsTheWeatherForCity", description = "Gets the current weather at a city name")
        public String getsTheWeatherForCity(
            @KernelFunctionParameter(name = "cityName", description = "Name of the city") String cityName) {
            return "80 and sunny";
        }
    }
}
