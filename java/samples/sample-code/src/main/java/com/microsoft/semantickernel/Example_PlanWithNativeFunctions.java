package com.microsoft.semantickernel;

import com.azure.ai.openai.OpenAIAsyncClient;
import com.microsoft.semantickernel.builders.SKBuilders;
import com.microsoft.semantickernel.connectors.ai.openai.util.OpenAIClientProvider;
import com.microsoft.semantickernel.exceptions.ConfigurationException;
import com.microsoft.semantickernel.orchestration.SKContext;
import com.microsoft.semantickernel.planner.actionplanner.Plan;
import com.microsoft.semantickernel.planner.sequentialplanner.SequentialPlanner;
import com.microsoft.semantickernel.skilldefinition.annotations.DefineSKFunction;
import com.microsoft.semantickernel.skilldefinition.annotations.SKFunctionInputAttribute;
import com.microsoft.semantickernel.skilldefinition.annotations.SKFunctionParameters;
import com.microsoft.semantickernel.textcompletion.TextCompletion;

public class Example_PlanWithNativeFunctions {

    public static void main(String[] args) throws ConfigurationException {
        OpenAIAsyncClient client = OpenAIClientProvider.getClient();

        TextCompletion textCompletionService = SKBuilders.textCompletionService().build(client, "text-davinci-003");

        Kernel kernel = SKBuilders.kernel()
                .withDefaultAIService(textCompletionService)
                .build();

        kernel.importSkill(new StringFunctions(), "StringFunctions");
        kernel.importSkill(new Emailer(), "Emailer");
        kernel.importSkill(new Names(), "Names");

        SequentialPlanner planner = new SequentialPlanner(kernel, null, null);


        Plan plan = planner
                .createPlanAsync("Send the input as an email to Steven and make sure I use his preferred name in the email")
                .block();

        System.out.println("\n\n=============================== Plan to execute ===============================");
        System.out.println(plan.toPlanString());
        System.out.println("===============================================================================");


        SKContext context = SKBuilders.context().build();
        context.setVariable("subject", "Update");

        String message = "Hay Steven, just wanted to let you know I have finished.";

        System.out.println("\n\nExecuting plan...");
        SKContext planResult = plan.invokeAsync(message, context, null).block();

        System.out.println("\n\nPlan Result: " + planResult.getResult());
    }

    public static class StringFunctions {
        @DefineSKFunction(
                name = "stringReplace",
                description = "Takes a message and substitutes string 'from' to 'to'")
        public String stringReplace(
                @SKFunctionInputAttribute(description = "The string to perform the replacement on")
                String input,
                @SKFunctionParameters(name = "from", description = "The string to replace")
                String from,
                @SKFunctionParameters(name = "to", description = "The string to replace with")
                String to
        ) {
            return input.replaceAll(from, to);
        }
    }

    public static class Names {
        @DefineSKFunction(name = "getNickName", description = "Retrieves the nick name for a given user")
        public String getNickName(
                @SKFunctionInputAttribute(description = "The name of the person to get an nick name for")
                String name) {
            switch (name) {
                case "Steven":
                    return "Code King";
                default:
                    throw new RuntimeException("Unknown user: " + name);
            }
        }

    }

    public static class Emailer {
        @DefineSKFunction(name = "getEmailAddress", description = "Retrieves the email address for a given user")
        public String getEmailAddress(
                @SKFunctionInputAttribute(description = "The name of the person to get an email address for")
                String name) {
            switch (name) {
                case "Steven":
                    return "codeking@example.com";
                default:
                    throw new RuntimeException("Unknown user: " + name);
            }
        }

        @DefineSKFunction(name = "sendEmail", description = "Sends an email")
        public String sendEmail(
                @SKFunctionParameters(name = "subject", description = "The email subject") String subject,
                @SKFunctionParameters(name = "message", description = "The message to email") String message,
                @SKFunctionParameters(name = "emailAddress", description = "The emailAddress to send the message to") String emailAddress) {
            System.out.println("================= Sending Email ====================");
            System.out.printf("To: %s%n", emailAddress);
            System.out.printf("Subject: %s%n", subject);
            System.out.printf("Message: %s%n", message);
            System.out.println("====================================================");
            return "Message sent";
        }
    }

}

