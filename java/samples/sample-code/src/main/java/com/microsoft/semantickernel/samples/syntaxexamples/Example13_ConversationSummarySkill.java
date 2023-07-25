// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.samples.syntaxexamples;

import com.azure.ai.openai.OpenAIAsyncClient;
import com.microsoft.semantickernel.samples.Config;
import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.KernelConfig;
import com.microsoft.semantickernel.builders.SKBuilders;
import com.microsoft.semantickernel.coreskills.ConversationSummarySkill;
import com.microsoft.semantickernel.orchestration.SKContext;
import com.microsoft.semantickernel.orchestration.SKFunction;
import com.microsoft.semantickernel.skilldefinition.ReadOnlyFunctionCollection;
import com.microsoft.semantickernel.textcompletion.TextCompletion;
import reactor.core.publisher.Mono;

import java.io.IOException;

public class Example13_ConversationSummarySkill {
    private static final String ChatTranscript =
            """
                    John: Hello, how are you?
                    Jane: I'm fine, thanks. How are you?
                    John: I'm doing well, writing some example code.
                    Jane: That's great! I'm writing some example code too.
                    John: What are you writing?
                    Jane: I'm writing a chatbot.
                    John: That's cool. I'm writing a chatbot too.
                    Jane: What language are you writing it in?
                    John: I'm writing it in C#.
                    Jane: I'm writing it in Python.
                    John: That's cool. I need to learn Python.
                    Jane: I need to learn C#.
                    John: Can I try out your chatbot?
                    Jane: Sure, here's the link.
                    John: Thanks!
                    Jane: You're welcome.
                    Jane: Look at this poem my chatbot wrote:
                    Jane: Roses are red
                    Jane: Violets are blue
                    Jane: I'm writing a chatbot
                    Jane: What about you?
                    John: That's cool. Let me see if mine will write a poem, too.
                    John: Here's a poem my chatbot wrote:
                    John: The singularity of the universe is a mystery.
                    John: The universe is a mystery.
                    John: The universe is a mystery.
                    John: The universe is a mystery.
                    John: Looks like I need to improve mine, oh well.
                    Jane: You might want to try using a different model.
                    Jane: I'm using the GPT-3 model.
                    John: I'm using the GPT-2 model. That makes sense.
                    John: Here is a new poem after updating the model.
                    John: The universe is a mystery.
                    John: The universe is a mystery.
                    John: The universe is a mystery.
                    John: Yikes, it's really stuck isn't it. Would you help me debug my code?
                    Jane: Sure, what's the problem?
                    John: I'm not sure. I think it's a bug in the code.
                    Jane: I'll take a look.
                    Jane: I think I found the problem.
                    Jane: It looks like you're not passing the right parameters to the model.
                    John: Thanks for the help!
                    Jane: I'm now writing a bot to summarize conversations. I want to make sure it works when the conversation is long.
                    John: So you need to keep talking with me to generate a long conversation?
                    Jane: Yes, that's right.
                    John: Ok, I'll keep talking. What should we talk about?
                    Jane: I don't know, what do you want to talk about?
                    John: I don't know, it's nice how CoPilot is doing most of the talking for us. But it definitely gets stuck sometimes.
                    Jane: I agree, it's nice that CoPilot is doing most of the talking for us.
                    Jane: But it definitely gets stuck sometimes.
                    John: Do you know how long it needs to be?
                    Jane: I think the max length is 1024 tokens. Which is approximately 1024*4= 4096 characters.
                    John: That's a lot of characters.
                    Jane: Yes, it is.
                    John: I'm not sure how much longer I can keep talking.
                    Jane: I think we're almost there. Let me check.
                    Jane: I have some bad news, we're only half way there.
                    John: Oh no, I'm not sure I can keep going. I'm getting tired.
                    Jane: I'm getting tired too.
                    John: Maybe there is a large piece of text we can use to generate a long conversation.
                    Jane: That's a good idea. Let me see if I can find one. Maybe Lorem Ipsum?
                    John: Yeah, that's a good idea.
                    Jane: I found a Lorem Ipsum generator.
                    Jane: Here's a 4096 character Lorem Ipsum text:
                    Jane: Lorem ipsum dolor sit amet, con
                    Jane: Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed euismod, nunc sit amet aliquam
                    Jane: Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed euismod, nunc sit amet aliquam
                    Jane: Darn, it's just repeating stuf now.
                    John: I think we're done.
                    Jane: We're not though! We need like 1500 more characters.
                    John: Oh Cananda, our home and native land.
                    Jane: True patriot love in all thy sons command.
                    John: With glowing hearts we see thee rise.
                    Jane: The True North strong and free.
                    John: From far and wide, O Canada, we stand on guard for thee.
                    Jane: God keep our land glorious and free.
                    John: O Canada, we stand on guard for thee.
                    Jane: O Canada, we stand on guard for thee.
                    Jane: That was fun, thank you. Let me check now.
                    Jane: I think we need about 600 more characters.
                    John: Oh say can you see?
                    Jane: By the dawn's early light.
                    John: What so proudly we hailed.
                    Jane: At the twilight's last gleaming.
                    John: Whose broad stripes and bright stars.
                    Jane: Through the perilous fight.
                    John: O'er the ramparts we watched.
                    Jane: Were so gallantly streaming.
                    John: And the rockets' red glare.
                    Jane: The bombs bursting in air.
                    John: Gave proof through the night.
                    Jane: That our flag was still there.
                    John: Oh say does that star-spangled banner yet wave.
                    Jane: O'er the land of the free.
                    John: And the home of the brave.
                    Jane: Are you a Seattle Kraken Fan?
                    John: Yes, I am. I love going to the games.
                    Jane: I'm a Seattle Kraken Fan too. Who is your favorite player?
                    John: I like watching all the players, but I think my favorite is Matty Beniers.
                    Jane: Yeah, he's a great player. I like watching him too. I also like watching Jaden Schwartz.
                    John: Adam Larsson is another good one. The big cat!
                    Jane: WE MADE IT! It's long enough. Thank you!
                    John: Can you automate generating long text next time?
                    Jane: I will.
                    John: You're welcome. I'm glad we could help. Goodbye!
                    Jane: Goodbye!
                    """.stripIndent();

    public static void main(String[] args) throws IOException {
        OpenAIAsyncClient client = Config.getClient();

        conversationSummarySkillAsync(client);
        getConversationActionItemsAsync(client);
        getConversationTopicsAsync(client);
    }

    private static void conversationSummarySkillAsync(OpenAIAsyncClient client) {
        System.out.println("======== SampleSkills - Conversation Summary Skill - Summarize ========");
        Kernel kernel = initializeKernel(client);

        ReadOnlyFunctionCollection conversationSummarySkill =
                kernel.importSkill(new ConversationSummarySkill(kernel), null);

        Mono<SKContext> summary = conversationSummarySkill
                .getFunction("SummarizeConversation", SKFunction.class)
                .invokeAsync(ChatTranscript);

        System.out.println("Generated Summary (This may take some time):");
        System.out.println(summary.block().getResult());
    }


    private static void getConversationActionItemsAsync(OpenAIAsyncClient client) {
        System.out.println("======== SampleSkills - Conversation Summary Skill - Action Items ========");
        Kernel kernel = initializeKernel(client);

        ReadOnlyFunctionCollection conversationSummarySkill =
                kernel.importSkill(new ConversationSummarySkill(kernel), null);

        Mono<SKContext> summary = conversationSummarySkill
                .getFunction("GetConversationActionItems", SKFunction.class)
                .invokeAsync(ChatTranscript);

        System.out.println("Generated Action Items (This may take some time):");
        System.out.println(summary.block().getResult());
    }

    private static void getConversationTopicsAsync(OpenAIAsyncClient client) {
        Kernel kernel = initializeKernel(client);

        ReadOnlyFunctionCollection conversationSummarySkill =
                kernel.importSkill(new ConversationSummarySkill(kernel), null);

        Mono<SKContext> summary = conversationSummarySkill
                .getFunction("GetConversationTopics", SKFunction.class)
                .invokeAsync(ChatTranscript);

        System.out.println("Generated Topics:");
        System.out.println(summary.block().getResult());
    }

    private static Kernel initializeKernel(OpenAIAsyncClient client) {
        TextCompletion textCompletion = SKBuilders.textCompletionService().build(client, "text-davinci-003");

        KernelConfig kernelConfig =
                new KernelConfig.Builder()
                        .build();

        return SKBuilders.kernel()
                .withKernelConfig(kernelConfig)
                .withAIService("text-davinci-003", textCompletion, true, TextCompletion.class).build();
    }
}
