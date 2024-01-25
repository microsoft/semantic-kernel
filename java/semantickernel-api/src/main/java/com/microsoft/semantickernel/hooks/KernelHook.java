package com.microsoft.semantickernel.hooks;

import com.azure.ai.openai.models.ChatCompletionsOptions;
import com.azure.ai.openai.models.ChatRequestMessage;
import java.util.List;
import java.util.function.Function;
import java.util.function.Predicate;

public interface KernelHook<T extends HookEvent> extends Predicate<HookEvent>, Function<T, T> {

    interface FunctionInvokingHook extends KernelHook<FunctionInvokingEventArgs> {

        default boolean test(HookEvent arguments) {
            return FunctionInvokingEventArgs.class.isAssignableFrom(arguments.getClass());
        }
    }

    interface FunctionInvokedHook extends KernelHook<FunctionInvokedEventArgs> {

        default boolean test(HookEvent arguments) {
            return FunctionInvokedEventArgs.class.isAssignableFrom(arguments.getClass());
        }
    }

    interface PromptRenderingHook extends KernelHook<PromptRenderingEventArgs> {

        default boolean test(HookEvent arguments) {
            return PromptRenderingEventArgs.class.isAssignableFrom(arguments.getClass());
        }
    }

    interface PromptRenderedHook extends KernelHook<PromptRenderedEventArgs> {

        default boolean test(HookEvent arguments) {
            return PromptRenderedEventArgs.class.isAssignableFrom(arguments.getClass());
        }
    }

    interface PreChatCompletionHook extends KernelHook<PreChatCompletionEvent> {

        default boolean test(HookEvent arguments) {
            return PreChatCompletionEvent.class.isAssignableFrom(arguments.getClass());
        }

        static ChatCompletionsOptions cloneOptionsWithMessages(
            ChatCompletionsOptions options,
            List<ChatRequestMessage> messages) {
            ChatCompletionsOptions newOptions = new ChatCompletionsOptions(messages)
                .setPresencePenalty(options.getPresencePenalty())
                .setFrequencyPenalty(options.getFrequencyPenalty())
                .setLogitBias(options.getLogitBias())
                .setMaxTokens(options.getMaxTokens())
                .setModel(options.getModel())
                .setStop(options.getStop())
                .setTemperature(options.getTemperature())
                .setTools(options.getTools())
                .setTopP(options.getTopP())
                .setUser(options.getUser())
                .setDataSources(options.getDataSources())
                .setEnhancements(options.getEnhancements())
                .setFunctions(options.getFunctions())
                .setN(options.getN())
                .setResponseFormat(options.getResponseFormat())
                .setSeed(options.getSeed())
                .setStream(options.isStream())
                .setToolChoice(options.getToolChoice());

            if (options.getFunctionCall() != null) {
                newOptions = newOptions.setFunctionCall(options.getFunctionCall());
            }
            return newOptions;
        }
    }
}
