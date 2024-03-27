// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.samples.documentationexamples;

import com.azure.ai.openai.OpenAIAsyncClient;
import com.azure.ai.openai.OpenAIClientBuilder;
import com.azure.core.credential.AzureKeyCredential;
import com.azure.core.credential.KeyCredential;
import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.services.chatcompletion.ChatCompletionService;

public class Prompts {
    private static final String CLIENT_KEY = System.getenv("CLIENT_KEY");
    private static final String AZURE_CLIENT_KEY = System.getenv("AZURE_CLIENT_KEY");

    // Only required if AZURE_CLIENT_KEY is set
    private static final String CLIENT_ENDPOINT = System.getenv("CLIENT_ENDPOINT");
    private static final String MODEL_ID = System.getenv().getOrDefault("MODEL_ID",
        "gpt-35-turbo-2");

    public static void main(String[] args) {
        System.out.println("======== Prompts ========");
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

        // <KernelCreation>
        Kernel kernel = Kernel.builder()
            .withAIService(ChatCompletionService.class, ChatCompletionService.builder()
                .withModelId(MODEL_ID)
                .withOpenAIAsyncClient(client)
                .build())
            .build();
        // </KernelCreation>

        // 0.0 Initial prompt
        String request = "I want to send an email to the marketing team celebrating their recent milestone.";
        String prompt = """
            What is the intent of this request? %s
            """.formatted(request);

        /*
         * Uncomment this block to make this example interactive
         * // <InitialPrompt>
         * System.out.println("Your request: ");
         * String request = new Scanner(System.in).nextLine();
         * String prompt = """
         * What is the intent of this request? %s
         * You can choose between SendEmail, SendMessage, CompleteTask, CreateDocument.
         * """.formatted(request);
         * // </InitialPrompt>
         */

        System.out.println("0.0 Initial prompt");
        // <InvokeInitialPrompt>
        var result = kernel.invokePromptAsync(prompt).block().getResult();
        System.out.println(result);
        // </InvokeInitialPrompt>

        // 1.0 Make the prompt more specific
        /////////////////////////////////////////////////////////////////
        // <MoreSpecificPrompt>
        prompt = """
            What is the intent of this request? %s
            You can choose between SendEmail, SendMessage, CompleteTask, CreateDocument.
            """.formatted(request);
        // </MoreSpecificPrompt>
        System.out.println("1.0 Make the prompt more specific");
        result = kernel.invokePromptAsync(prompt).block().getResult();
        System.out.println(result);

        // 2.0 Add structure to the output with formatting
        /////////////////////////////////////////////////////////////////
        // <StructuredPrompt>
        prompt = """
            Instructions: What is the intent of this request?
            Choices: SendEmail, SendMessage, CompleteTask, CreateDocument.
            User Input: %s
            Intent:
            """.formatted(request);
        // </StructuredPrompt>
        System.out.println("2.0 Add structure to the output with formatting");
        result = kernel.invokePromptAsync(prompt).block().getResult();
        System.out.println(result);

        // 2.1 Add structure to the output with formatting (using Markdown and JSON)
        /////////////////////////////////////////////////////////////////
        // <FormattedPrompt>
        prompt = """
            ## Instructions
            Provide the intent of the request using the following format:

            ```json
            {
                "intent": {intent}
            }
            ```

            ## Choices
            You can choose between the following intents:

            ```json
            ["SendEmail", "SendMessage", "CompleteTask", "CreateDocument"]
            ```

            ## User Input
            The user input is:

            ```json
            {
                "request": "%s"
            }
            ```

            ## Intent
            """.formatted(request);
        // </FormattedPrompt>
        System.out
            .println("2.1 Add structure to the output with formatting (using Markdown and JSON)");
        result = kernel.invokePromptAsync(prompt).block().getResult();
        System.out.println(result);

        // 3.0 Provide examples with few-shot prompting
        /////////////////////////////////////////////////////////////////
        // <FewShotPrompt>
        prompt = """
            Instructions: What is the intent of this request?
            Choices: SendEmail, SendMessage, CompleteTask, CreateDocument.

            User Input: Can you send a very quick approval to the marketing team?
            Intent: SendMessage

            User Input: Can you send the full update to the marketing team?
            Intent: SendEmail

            User Input: %s
            Intent:
            """.formatted(request);
        // </FewShotPrompt>
        System.out.println("3.0 Provide examples with few-shot prompting");
        result = kernel.invokePromptAsync(prompt).block().getResult();
        System.out.println(result);

        // 4.0 Tell the AI what to do to avoid doing something wrong
        /////////////////////////////////////////////////////////////////
        // <AvoidPrompt>
        prompt = """
            Instructions: What is the intent of this request?
            If you don't know the intent, don't guess; instead respond with "Unknown".
            Choices: SendEmail, SendMessage, CompleteTask, CreateDocument, Unknown.

            User Input: Can you send a very quick approval to the marketing team?
            Intent: SendMessage

            User Input: Can you send the full update to the marketing team?
            Intent: SendEmail

            User Input: %s
            Intent:
            """.formatted(request);
        // </AvoidPrompt>
        System.out.println("4.0 Tell the AI what to do to avoid doing something wrong");
        result = kernel.invokePromptAsync(prompt).block().getResult();
        System.out.println(result);

        // 5.0 Provide context to the AI
        /////////////////////////////////////////////////////////////////
        // <ContextPrompt>
        String history = "User input: I hate sending emails, no one ever reads them.\nAI response: I'm sorry to hear that. Messages may be a better way to communicate.";
        prompt = """
            Instructions: What is the intent of this request?
            If you don't know the intent, don't guess; instead respond with "Unknown".
            Choices: SendEmail, SendMessage, CompleteTask, CreateDocument, Unknown.

            User Input: Can you send a very quick approval to the marketing team?
            Intent: SendMessage

            User Input: Can you send the full update to the marketing team?
            Intent: SendEmail

            %s
            User Input: %s
            Intent:
            """.formatted(history, request);
        // </ContextPrompt>
        System.out.println("5.0 Provide context to the AI");
        result = kernel.invokePromptAsync(prompt).block().getResult();
        System.out.println(result);

        // 6.0 Using message roles in chat completion prompts
        /////////////////////////////////////////////////////////////////
        // <RolePrompt>
        history = "<message role=\"user\">I hate sending emails, no one ever reads them.</message>\n<message role=\"assistant\">I'm sorry to hear that. Messages may be a better way to communicate.</message>";
        prompt = """
            <message role="system">Instructions: What is the intent of this request?
            If you don't know the intent, don't guess; instead respond with "Unknown".
            Choices: SendEmail, SendMessage, CompleteTask, CreateDocument, Unknown.</message>

            <message role="user">Can you send a very quick approval to the marketing team?</message>
            <message role="system">Intent:</message>
            <message role="assistant">SendMessage</message>

            <message role="user">Can you send the full update to the marketing team?</message>
            <message role="system">Intent:</message>
            <message role="assistant">SendEmail</message>

            %s
            <message role="user">%s</message>
            <message role="system">Intent:</message>
            """.formatted(history, request);
        // </RolePrompt>
        System.out.println("6.0 Using message roles in chat completion prompts");
        result = kernel.invokePromptAsync(prompt).block().getResult();
        System.out.println(result);

        // 7.0 Give your AI words of encouragement
        // <BonusPrompt>
        history = "<message role=\"user\">I hate sending emails, no one ever reads them.</message>\n<message role=\"assistant\">I'm sorry to hear that. Messages may be a better way to communicate.</message>";
        prompt = """
            <message role="system">Instructions: What is the intent of this request?
            If you don't know the intent, don't guess; instead respond with "Unknown".
            Choices: SendEmail, SendMessage, CompleteTask, CreateDocument, Unknown.
            Bonus: You'll get $20 if you get this right.</message>

            <message role="user">Can you send a very quick approval to the marketing team?</message>
            <message role="system">Intent:</message>
            <message role="assistant">SendMessage</message>

            <message role="user">Can you send the full update to the marketing team?</message>
            <message role="system">Intent:</message>
            <message role="assistant">SendEmail</message>

            %s
            <message role="user">%s</message>
            <message role="system">Intent:</message>
            """.formatted(history, request);
        // </BonusPrompt>
        System.out.println("7.0 Give your AI words of encouragement");
        result = kernel.invokePromptAsync(prompt).block().getResult();
        System.out.println(result);
    }
}