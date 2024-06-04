package com.microsoft.semantickernel.samples.syntaxexamples.functions;

import com.google.cloud.vertexai.VertexAI;
import com.google.cloud.vertexai.api.FunctionResponse;
import com.google.protobuf.Struct;
import com.google.protobuf.Value;
import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.aiservices.google.chatcompletion.GeminiChatCompletion;
import com.microsoft.semantickernel.aiservices.google.chatcompletion.GeminiChatMessageContent;
import com.microsoft.semantickernel.aiservices.google.chatcompletion.GeminiFunctionCall;
import com.microsoft.semantickernel.contextvariables.ContextVariableTypes;
import com.microsoft.semantickernel.orchestration.FunctionResult;
import com.microsoft.semantickernel.orchestration.InvocationContext;
import com.microsoft.semantickernel.orchestration.InvocationReturnMode;
import com.microsoft.semantickernel.orchestration.PromptExecutionSettings;
import com.microsoft.semantickernel.orchestration.ToolCallBehavior;
import com.microsoft.semantickernel.plugin.KernelPluginFactory;
import com.microsoft.semantickernel.semanticfunctions.KernelFunctionArguments;
import com.microsoft.semantickernel.semanticfunctions.KernelFunctionFromPrompt;
import com.microsoft.semantickernel.semanticfunctions.annotations.DefineKernelFunction;
import com.microsoft.semantickernel.semanticfunctions.annotations.KernelFunctionParameter;
import com.microsoft.semantickernel.services.chatcompletion.AuthorRole;
import com.microsoft.semantickernel.services.chatcompletion.ChatCompletionService;
import com.microsoft.semantickernel.services.chatcompletion.ChatHistory;
import com.microsoft.semantickernel.services.chatcompletion.ChatMessageContent;

import java.time.ZonedDateTime;
import java.time.format.DateTimeFormatter;
import java.util.ArrayList;
import java.util.List;

public class Example98_GeminiFunctionCalling {
    private static final String PROJECT_ID = System.getenv("PROJECT_ID");
    private static final String LOCATION = System.getenv("LOCATION");
    private static final String MODEL_ID = System.getenv("GEMINI_MODEL_ID");


    // Define functions that can be called by the model
    public static class HelperFunctions {

        @DefineKernelFunction(name = "currentUtcTime", description = "Retrieves the current time in UTC.")
        public String currentUtcTime() {
            return ZonedDateTime.now().format(DateTimeFormatter.RFC_1123_DATE_TIME);
        }

        @DefineKernelFunction(name = "getWeatherForCity", description = "Gets the current weather for the specified city")
        public String getWeatherForCity(
                @KernelFunctionParameter(name = "cityName", description = "Name of the city") String cityName) {
            switch (cityName) {
                case "Thrapston":
                    return "80 and sunny";
                case "Boston":
                    return "61 and rainy";
                case "London":
                    return "55 and cloudy";
                case "Miami":
                    return "80 and sunny";
                case "Paris":
                    return "60 and rainy";
                case "Tokyo":
                    return "50 and sunny";
                case "Sydney":
                    return "75 and sunny";
                case "Tel Aviv":
                    return "80 and sunny";
                default:
                    return "31 and snowing";
            }
        }

        public static void main(String[] args) throws NoSuchMethodException {
            System.out.println("======== Open AI - Function calling ========");

            VertexAI client = new VertexAI(PROJECT_ID, LOCATION);

            ChatCompletionService chat = GeminiChatCompletion.builder()
                    .withModelId(MODEL_ID)
                    .withVertexAIClient(client)
                    .build();

            var plugin = KernelPluginFactory.createFromObject(new HelperFunctions(), "HelperFunctions");

            var kernel = Kernel.builder()
                    .withAIService(ChatCompletionService.class, chat)
                    .withPlugin(plugin)
                    .build();

            System.out.println("======== Example 1: Use automated function calling ========");

            var function = KernelFunctionFromPrompt.builder()
                    .withTemplate(
                            "Given the current time of day and weather, what is the likely color of the sky in Boston?")
                    .withDefaultExecutionSettings(
                            PromptExecutionSettings.builder()
                                    .withTemperature(0.4)
                                    .withTopP(1)
                                    .withMaxTokens(100)
                                    .build())
                    .build();

            var result = kernel
                    .invokeAsync(function)
                    .withToolCallBehavior(ToolCallBehavior.allowAllKernelFunctions(true))
                    .withResultType(ContextVariableTypes.getGlobalVariableTypeForClass(String.class))
                    .block();

            System.out.println(result.getResult());

            System.out.println("======== Example 2: Use manual function calling ========");

            var chatHistory = new ChatHistory();
            chatHistory.addUserMessage(
                    "Given the current time of day and weather, what is the likely color of the sky in Boston?");

            while (true) {
                var message = (GeminiChatMessageContent<?>) chat.getChatMessageContentsAsync(
                                chatHistory,
                                kernel,
                                InvocationContext.builder()
                                        .withToolCallBehavior(ToolCallBehavior.allowAllKernelFunctions(false))
                                        .withReturnMode(InvocationReturnMode.LAST_MESSAGE_ONLY)
                                        .build())
                        .block().get(0);

                // Add the assistant's response to the chat history
                chatHistory.addMessage(message);
                if (message.getContent() != null && !message.getContent().isEmpty()) {
                    System.out.println(message.getContent());
                }

                // Process the functions calls or break if there are no more functions to call
                if (message.getGeminiFunctionCalls().isEmpty()) {
                    break;
                }

                List<GeminiFunctionCall> functionResponses = new ArrayList<>();
                for (var geminiFunction : message.getGeminiFunctionCalls()) {

                    String content = null;
                    try {
                        // getFunction will throw an exception if the function is not found
                        var fn = kernel.getFunction(geminiFunction.getPluginName(), geminiFunction.getFunctionName());

                        var arguments = KernelFunctionArguments.builder();
                        geminiFunction.getFunctionCall().getArgs().getFieldsMap().forEach((key, value) -> {
                            arguments.withVariable(key, value.getStringValue());
                        });

                        // Invoke the function and add the result to the list of function responses
                        FunctionResult<?> functionResult = fn
                                .invokeAsync(kernel, arguments.build(), null, null).block();

                        functionResponses.add(new GeminiFunctionCall(geminiFunction.getFunctionCall(), functionResult));
                    } catch (IllegalArgumentException e) {
                        content = "Unable to find function. Please try again!";
                    }
                }

                // Add the function responses to the chat history
                ChatMessageContent<?> functionResponsesMessage = new GeminiChatMessageContent<>(AuthorRole.USER,
                        "", null, null, null, null, functionResponses);

                chatHistory.addMessage(functionResponsesMessage);
            }
        }
    }
}
