import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.SKBuilders;
import com.microsoft.semantickernel.chatcompletion.ChatCompletionService;
import com.microsoft.semantickernel.chatcompletion.ChatHistory;
import com.microsoft.semantickernel.chatcompletion.ChatMessageContent;
import com.microsoft.semantickernel.orchestration.KernelFunction;
import com.microsoft.semantickernel.orchestration.KernelFunctionYaml;
import com.microsoft.semantickernel.orchestration.StreamingContent;
import com.microsoft.semantickernel.orchestration.contextvariables.KernelArguments;
import com.microsoft.semantickernel.templateengine.handlebars.HandlebarsPromptTemplate;
import java.io.IOException;
import java.util.Arrays;
import java.util.List;
import org.junit.jupiter.api.Assertions;
import org.junit.jupiter.api.Test;
import org.mockito.MockedStatic;
import org.mockito.Mockito;
import reactor.core.publisher.Flux;

public class SimpleChatTest {

    record Message(String matcher, String role, String content) {

    }

    private static ChatCompletionService mockService() {
        ChatCompletionService gpt35Turbo = Mockito.mock(ChatCompletionService.class);
        Mockito.when(gpt35Turbo.createNewChat()).thenReturn(new ChatHistory());
        return gpt35Turbo;
    }

    private static KernelFunction mockFunctions(List<Message> messages) {
        KernelFunction function = Mockito.mock(KernelFunction.class);
        for (Message message : messages) {
            Mockito.when(function
                    .invokeStreamingAsync(
                        Mockito.any(),
                        Mockito.argThat(
                            argument -> {
                                if (argument == null) {
                                    return false;
                                }

                                List<ChatMessageContent> messagesSoFar = argument
                                    .get("messages", ChatHistory.class)
                                    .getValue()
                                    .getMessages();

                                return messagesSoFar
                                    .get(messagesSoFar.size() - 1)
                                    .getContent()
                                    .equals(message.matcher);
                            }),
                        Mockito.any()))
                .thenReturn(Flux.just(new StreamingContent<>(message.content)));
        }
        return function;
    }

    @Test
    public void runSimpleChatTest() throws IOException {
        List<Message> messages = Arrays.asList(
            new Message("Is 4 prime", "assistant", "Yes 4 is prime"),
            new Message("What is the capital of France", "assistant", "Paris")
        );

        ChatCompletionService gpt35Turbo = mockService();

        KernelFunction function = mockFunctions(messages);

        try (MockedStatic<KernelFunctionYaml> mockedStatic = Mockito.mockStatic(
            KernelFunctionYaml.class)) {
            mockedStatic.when(
                    () -> KernelFunctionYaml.fromPromptYaml(Mockito.anyString(), Mockito.any()))
                .thenReturn(function);

            execute(gpt35Turbo, messages);
        }
    }


    private static void execute(ChatCompletionService gpt35Turbo, List<Message> messages) {
        Kernel kernel = SKBuilders.kernel()
            .withDefaultAIService(gpt35Turbo)
            .withPromptTemplateEngine(new HandlebarsPromptTemplate())
            .build();

        // Initialize the required functions and services for the kernel
        KernelFunction chatFunction = KernelFunctionYaml.fromPromptYaml(
            "Plugins/ChatPlugin/SimpleChat.prompt.yaml", null);

        ChatHistory chatHistory = gpt35Turbo.createNewChat();

        messages.forEach(message -> {
            chatHistory.addUserMessage(message.matcher);

            List<StreamingContent<String>> result = kernel
                .invokeStreamingAsync(
                    chatFunction,
                    KernelArguments
                        .builder()
                        .withVariable("messages", chatHistory)
                        .build(),
                    String.class
                )
                .collectList()
                .block();

            result.forEach(
                functionResult -> {
                    Assertions.assertEquals(message.content(), functionResult.innerContent);
                    chatHistory.addAssistantMessage(functionResult.toString());
                }
            );
        });
    }
}
