import java.io.IOException;
import java.nio.file.Path;
import java.util.Arrays;
import java.util.List;

import org.junit.jupiter.api.Assertions;
import org.junit.jupiter.api.Test;
import org.mockito.Mockito;

import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.SKBuilders;
import com.microsoft.semantickernel.chatcompletion.AuthorRole;
import com.microsoft.semantickernel.chatcompletion.ChatCompletionService;
import com.microsoft.semantickernel.chatcompletion.ChatHistory;
import com.microsoft.semantickernel.chatcompletion.StreamingChatMessageContent;
import com.microsoft.semantickernel.orchestration.KernelFunction;
import com.microsoft.semantickernel.orchestration.KernelFunctionYaml;
import com.microsoft.semantickernel.orchestration.contextvariables.KernelArguments;
import com.microsoft.semantickernel.templateengine.handlebars.HandlebarsPromptTemplate;

import reactor.core.publisher.Flux;

public class PersonaChatTest {

    record Message(String matcher, String role, String content) {

    }

    private static ChatCompletionService mockService(List<Message> messages) {
        ChatCompletionService gpt35Turbo = Mockito.mock(ChatCompletionService.class);

        for (Message message : messages) {
            Mockito.when(gpt35Turbo.getStreamingChatMessageContentsAsync(
                    Mockito.<String>argThat(
                        argument -> {
                            if (argument != null && argument.contains(message.matcher)) {
                                return true;
                            }

                            return false;
                        }),
                    Mockito.any(),
                    Mockito.any()))
                .thenReturn(Flux.just(new StreamingChatMessageContent(
                    AuthorRole.ASSISTANT, message.content())));
        }
        return gpt35Turbo;
    }

    @Test
    public void runSimpleChatTest() throws IOException {
        List<Message> messages = Arrays.asList(
            new Message("Is 4 prime", "assistant", "Yes 4 is prime"),
            new Message("What is the capital of France", "assistant", "Paris")
        );

        ChatCompletionService gpt35Turbo = mockService(messages);

        Kernel kernel = SKBuilders.kernel()
            .withDefaultAIService(ChatCompletionService.class, gpt35Turbo)
            .withPromptTemplate(new HandlebarsPromptTemplate())
            .build();

        // Initialize the required functions and services for the kernel
        KernelFunction chatFunction = KernelFunctionYaml.fromYaml(
            Path.of("Plugins/ChatPlugin/PersonaChat.prompt.yaml"));

        ChatHistory chatHistory = new ChatHistory();

        messages.forEach(message -> {
            chatHistory.addUserMessage(message.matcher);

            List<String> result = kernel
                .invokeStreamingAsync(
                    chatFunction,
                    KernelArguments
                        .builder()
                        .withVariable("messages", chatHistory)
                        .withVariable("persona",
                            "You are a snarky (yet helpful) teenage assistant. Make sure to use hip slang in every response.")
                        .build(),
                    String.class
                )
                .collectList()
                .block();

            result
                .forEach(
                    functionResult -> {
                        Assertions.assertEquals(message.content(), functionResult);
                        chatHistory.addAssistantMessage(functionResult.toString());
                    }
                );
        });
    }
}
