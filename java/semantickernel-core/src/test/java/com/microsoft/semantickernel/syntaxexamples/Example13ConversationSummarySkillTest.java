// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.syntaxexamples;

import com.azure.ai.openai.OpenAIAsyncClient;
import com.microsoft.semantickernel.DefaultKernelTest;
import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.coreskills.ConversationSummarySkill;
import com.microsoft.semantickernel.orchestration.SKContext;
import com.microsoft.semantickernel.skilldefinition.ReadOnlyFunctionCollection;
import org.junit.jupiter.api.Assertions;
import org.junit.jupiter.api.Test;
import reactor.util.function.Tuples;

public class Example13ConversationSummarySkillTest {
    private static final String ChatTranscript =
            "\n"
                + "John: Hello, how are you?\n"
                + "Jane: I'm fine, thanks. How are you?\n"
                + "John: I'm doing well, writing some example code.\n"
                + "Jane: That's great! I'm writing some example code too.\n"
                + "John: What are you writing?\n"
                + "Jane: I'm writing a chatbot.\n"
                + "John: That's cool. I'm writing a chatbot too.\n"
                + "Jane: What language are you writing it in?\n"
                + "John: I'm writing it in C#.\n"
                + "Jane: I'm writing it in Python.\n"
                + "John: That's cool. I need to learn Python.\n"
                + "Jane: I need to learn C#.\n"
                + "John: Can I try out your chatbot?\n"
                + "Jane: Sure, here's the link.\n"
                + "John: Thanks!\n"
                + "Jane: You're welcome.\n"
                + "Jane: Look at this poem my chatbot wrote:\n"
                + "Jane: Roses are red\n"
                + "Jane: Violets are blue\n"
                + "Jane: I'm writing a chatbot\n"
                + "Jane: What about you?\n"
                + "John: That's cool. Let me see if mine will write a poem, too.\n"
                + "John: Here's a poem my chatbot wrote:\n"
                + "John: The singularity of the universe is a mystery.\n"
                + "John: The universe is a mystery.\n"
                + "John: The universe is a mystery.\n"
                + "John: The universe is a mystery.\n"
                + "John: Looks like I need to improve mine, oh well.\n"
                + "Jane: You might want to try using a different model.\n"
                + "Jane: I'm using the GPT-3 model.\n"
                + "John: I'm using the GPT-2 model. That makes sense.\n"
                + "John: Here is a new poem after updating the model.\n"
                + "John: The universe is a mystery.\n"
                + "John: The universe is a mystery.\n"
                + "John: The universe is a mystery.\n"
                + "John: Yikes, it's really stuck isn't it. Would you help me debug my code?\n"
                + "Jane: Sure, what's the problem?\n"
                + "John: I'm not sure. I think it's a bug in the code.\n"
                + "Jane: I'll take a look.\n"
                + "Jane: I think I found the problem.\n"
                + "Jane: It looks like you're not passing the right parameters to the model.\n"
                + "John: Thanks for the help!\n"
                + "Jane: I'm now writing a bot to summarize conversations. I want to make sure it"
                + " works when the conversation is long.\n"
                + "John: So you need to keep talking with me to generate a long conversation?\n"
                + "Jane: Yes, that's right.\n"
                + "John: Ok, I'll keep talking. What should we talk about?\n"
                + "Jane: I don't know, what do you want to talk about?\n"
                + "John: I don't know, it's nice how CoPilot is doing most of the talking for us."
                + " But it definitely gets stuck sometimes.\n"
                + "Jane: I agree, it's nice that CoPilot is doing most of the talking for us.\n"
                + "Jane: But it definitely gets stuck sometimes.\n"
                + "John: Do you know how long it needs to be?\n"
                + "Jane: I think the max length is 1024 tokens. Which is approximately 1024*4= 4096"
                + " characters.\n"
                + "John: That's a lot of characters.\n"
                + "Jane: Yes, it is.\n"
                + "John: I'm not sure how much longer I can keep talking.\n"
                + "Jane: I think we're almost there. Let me check.\n"
                + "Jane: I have some bad news, we're only half way there.\n"
                + "John: Oh no, I'm not sure I can keep going. I'm getting tired.\n"
                + "Jane: I'm getting tired too.\n"
                + "John: Maybe there is a large piece of text we can use to generate a long"
                + " conversation.\n"
                + "Jane: That's a good idea. Let me see if I can find one. Maybe Lorem Ipsum?\n"
                + "John: Yeah, that's a good idea.\n"
                + "Jane: I found a Lorem Ipsum generator.\n"
                + "Jane: Here's a 4096 character Lorem Ipsum text:\n"
                + "Jane: Lorem ipsum dolor sit amet, con\n"
                + "Jane: Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed euismod, nunc"
                + " sit amet aliquam\n"
                + "Jane: Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed euismod, nunc"
                + " sit amet aliquam\n"
                + "Jane: Darn, it's just repeating stuf now.\n"
                + "John: I think we're done.\n"
                + "Jane: We're not though! We need like 1500 more characters.\n"
                + "John: Oh Cananda, our home and native land.\n"
                + "Jane: True patriot love in all thy sons command.\n"
                + "John: With glowing hearts we see thee rise.\n"
                + "Jane: The True North strong and free.\n"
                + "John: From far and wide, O Canada, we stand on guard for thee.\n"
                + "Jane: God keep our land glorious and free.\n"
                + "John: O Canada, we stand on guard for thee.\n"
                + "Jane: O Canada, we stand on guard for thee.\n"
                + "Jane: That was fun, thank you. Let me check now.\n"
                + "Jane: I think we need about 600 more characters.\n"
                + "John: Oh say can you see?\n"
                + "Jane: By the dawn's early light.\n"
                + "John: What so proudly we hailed.\n"
                + "Jane: At the twilight's last gleaming.\n"
                + "John: Whose broad stripes and bright stars.\n"
                + "Jane: Through the perilous fight.\n"
                + "John: O'er the ramparts we watched.\n"
                + "Jane: Were so gallantly streaming.\n"
                + "John: And the rockets' red glare.\n"
                + "Jane: The bombs bursting in air.\n"
                + "John: Gave proof through the night.\n"
                + "Jane: That our flag was still there.\n"
                + "John: Oh say does that star-spangled banner yet wave.\n"
                + "Jane: O'er the land of the free.\n"
                + "John: And the home of the brave.\n"
                + "Jane: Are you a Seattle Kraken Fan?\n"
                + "John: Yes, I am. I love going to the games.\n"
                + "Jane: I'm a Seattle Kraken Fan too. Who is your favorite player?\n"
                + "John: I like watching all the players, but I think my favorite is Matty"
                + " Beniers.\n"
                + "Jane: Yeah, he's a great player. I like watching him too. I also like watching"
                + " Jaden Schwartz.\n"
                + "John: Adam Larsson is another good one. The big cat!\n"
                + "Jane: WE MADE IT! It's long enough. Thank you!\n"
                + "John: Can you automate generating long text next time?\n"
                + "Jane: I will.\n"
                + "John: You're welcome. I'm glad we could help. Goodbye!\n"
                + "Jane: Goodbye!";

    @Test
    public void conversationSummarySkillAsync() {

        OpenAIAsyncClient client =
                DefaultKernelTest.mockCompletionOpenAIAsyncClientMatch(
                        Tuples.of(
                                arg -> {
                                    Assertions.assertTrue(
                                            arg.contains("Summarize the conversation"));
                                    return arg.contains("Hello, how are you");
                                },
                                "Summary of first half"),
                        Tuples.of(
                                arg -> {
                                    Assertions.assertTrue(
                                            arg.contains("Summarize the conversation"));
                                    return arg.contains("I think we're almost there");
                                },
                                "Summary of second half"));

        Kernel kernel = DefaultKernelTest.buildKernel("model", client);

        ReadOnlyFunctionCollection conversationSummarySkill =
                kernel.importSkill(new ConversationSummarySkill(kernel), null);

        SKContext summary =
                conversationSummarySkill
                        .getFunction("SummarizeConversation")
                        .invokeAsync(ChatTranscript)
                        .block();

        Assertions.assertTrue(summary.getResult().contains("Summary of first half"));
        Assertions.assertTrue(summary.getResult().contains("Summary of second half"));
    }

    @Test
    public void getConversationActionItemsAsync() {

        OpenAIAsyncClient client =
                DefaultKernelTest.mockCompletionOpenAIAsyncClientMatch(
                        Tuples.of(
                                arg -> {
                                    Assertions.assertTrue(
                                            arg.contains("You are an action item extractor"));
                                    return arg.contains("Hello, how are you");
                                },
                                "An action item"),
                        Tuples.of(
                                arg -> {
                                    Assertions.assertTrue(
                                            arg.contains("You are an action item extractor"));
                                    return arg.contains("I think we're almost there");
                                },
                                "Another action item"));

        Kernel kernel = DefaultKernelTest.buildKernel("model", client);

        ReadOnlyFunctionCollection conversationSummarySkill =
                kernel.importSkill(new ConversationSummarySkill(kernel), null);

        SKContext summary =
                conversationSummarySkill
                        .getFunction("GetConversationActionItems")
                        .invokeAsync(ChatTranscript)
                        .block();

        Assertions.assertTrue(summary.getResult().contains("An action item"));
        Assertions.assertTrue(summary.getResult().contains("Another action item"));
    }

    @Test
    public void getConversationTopicsAsync() {

        OpenAIAsyncClient client =
                DefaultKernelTest.mockCompletionOpenAIAsyncClientMatch(
                        Tuples.of(
                                arg -> {
                                    Assertions.assertTrue(arg.contains("extract key topics"));
                                    return arg.contains("Hello, how are you");
                                },
                                "A topic"),
                        Tuples.of(
                                arg -> {
                                    Assertions.assertTrue(arg.contains("extract key topics"));
                                    return arg.contains("I think we're almost there");
                                },
                                "Another topic"));

        Kernel kernel = DefaultKernelTest.buildKernel("model", client);

        ReadOnlyFunctionCollection conversationSummarySkill =
                kernel.importSkill(new ConversationSummarySkill(kernel), null);

        SKContext summary =
                conversationSummarySkill
                        .getFunction("GetConversationTopics")
                        .invokeAsync(ChatTranscript)
                        .block();

        Assertions.assertTrue(summary.getResult().contains("A topic"));
        Assertions.assertTrue(summary.getResult().contains("Another topic"));
    }
}
