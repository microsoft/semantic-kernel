package com.microsoft.semantickernel.aiservices.openai;

import java.util.List;
import java.util.Map;

import javax.annotation.Nonnull;
import javax.annotation.Nullable;

import com.azure.ai.openai.models.ChatCompletions;
import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.chatcompletion.ChatCompletion;
import com.microsoft.semantickernel.chatcompletion.ChatHistory;
import com.microsoft.semantickernel.chatcompletion.ChatRequestSettings;
import com.microsoft.semantickernel.orchestration.FunctionResult;
import com.microsoft.semantickernel.textcompletion.CompletionRequestSettings;
import com.microsoft.semantickernel.textcompletion.CompletionType;
import com.microsoft.semantickernel.aiservices.AIService;
import com.microsoft.semantickernel.aiservices.responsetypes.BinaryFile;

import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

public class OpenAIChatCompletion implements AIService, ChatCompletion<ChatHistory> {
    
    public OpenAIChatCompletion(String modelId, String apiKey) {}

    @Override
    public Mono<List<String>> completeAsync(@Nonnull String text, @Nonnull CompletionRequestSettings requestSettings) {
        // TODO Auto-generated method stub
        throw new UnsupportedOperationException("Unimplemented method 'completeAsync'");
    }

    @Override
    public Flux<String> completeStreamAsync(@Nonnull String text, @Nonnull CompletionRequestSettings requestSettings) {
        // TODO Auto-generated method stub
        throw new UnsupportedOperationException("Unimplemented method 'completeStreamAsync'");
    }

    @Override
    public CompletionType defaultCompletionType() {
        // TODO Auto-generated method stub
        throw new UnsupportedOperationException("Unimplemented method 'defaultCompletionType'");
    }

    @Override
    public Mono<String> generateMessageAsync(ChatHistory chat, @Nullable ChatRequestSettings requestSettings) {
        // TODO Auto-generated method stub
        throw new UnsupportedOperationException("Unimplemented method 'generateMessageAsync'");
    }

    @Override
    public ChatHistory createNewChat(String instructions) {
        // TODO Auto-generated method stub
        throw new UnsupportedOperationException("Unimplemented method 'createNewChat'");
    }

    @Override
    public ChatHistory createNewChat() {
        // TODO Auto-generated method stub
        throw new UnsupportedOperationException("Unimplemented method 'createNewChat'");
    }

    @Override
    public Flux<String> generateMessageStream(ChatHistory chatHistory, @Nullable ChatRequestSettings requestSettings) {
        // TODO Auto-generated method stub
        throw new UnsupportedOperationException("Unimplemented method 'generateMessageStream'");
    }

    @Override
    public Flux<ChatCompletions> getStreamingChatCompletionsAsync(ChatHistory chat,
            ChatRequestSettings requestSettings) {
        // TODO Auto-generated method stub
        throw new UnsupportedOperationException("Unimplemented method 'getStreamingChatCompletionsAsync'");
    }

    @Override
    public String getModelId() {
        // TODO Auto-generated method stub
        throw new UnsupportedOperationException("Unimplemented method 'getModelId'");
    }

    @Override
    public List<Class<?>> getOutputTypes() {
        // TODO Auto-generated method stub
        throw new UnsupportedOperationException("Unimplemented method 'getOutputTypes'");
    }

    @Override
    public List<String> getCapabilities() {
        // TODO Auto-generated method stub
        throw new UnsupportedOperationException("Unimplemented method 'getCapabilities'");
    }

    @Override
    public Mono<FunctionResult> getModelResultAsync(Kernel kernel, String pluginName, String name, String prompt,
            Map<Object, BinaryFile> files) {
        // TODO Auto-generated method stub
        throw new UnsupportedOperationException("Unimplemented method 'getModelResultAsync'");
    }

    @Override
    public Mono<FunctionResult> getModelStreamingResultAsync(Kernel kernel, String pluginName, String name,
            String prompt, Map<Object, BinaryFile> files) {
        // TODO Auto-generated method stub
        throw new UnsupportedOperationException("Unimplemented method 'getModelStreamingResultAsync'");
    }
}
