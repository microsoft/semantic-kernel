package com.microsoft.semantickernel;

import com.azure.ai.openai.OpenAIAsyncClient;
import com.microsoft.semantickernel.connectors.ai.openai.util.OpenAIClientProvider;
import com.microsoft.semantickernel.exceptions.ConfigurationException;
import com.microsoft.semantickernel.planner.actionplanner.Plan;
import com.microsoft.semantickernel.planner.sequentialplanner.SequentialPlanner;
import com.microsoft.semantickernel.skilldefinition.annotations.DefineSKFunction;
import com.microsoft.semantickernel.skilldefinition.annotations.SKFunctionInputAttribute;
import com.microsoft.semantickernel.skilldefinition.annotations.SKFunctionParameters;
import com.microsoft.semantickernel.textcompletion.TextCompletion;

import java.io.IOException;

/**
 * Code for Microsoft Developer Blog
 * <a href="https://devblogs.microsoft.com/semantic-kernel/introducing-semantic-kernel-for-java/">
 * Introducing Semantic Kernel for Java</a>
 * <p>
 * Refer to the <a href=
 * "https://github.com/microsoft/semantic-kernel/blob/experimental-java/java/samples/sample-code/README.md">
 * README</a> for configuring your environment to run the examples.
 */
public class Example99_BlogAnnouncement {

  static {
    System.setProperty("client.openai.key", "");
  }

  public static void main(String[] args) throws IOException, ConfigurationException {
    OpenAIAsyncClient client = OpenAIClientProvider.getClient();

    TextCompletion textCompletionService = SKBuilders.textCompletion()
            .withModelId("text-davinci-003")
            .withOpenAIClient(client)
            .build();

    Kernel kernel = SKBuilders.kernel().withDefaultAIService(textCompletionService).build();
    kernel.importSkill(new MyAppSkills(), "MyAppSkills");

    SequentialPlanner planner = new SequentialPlanner(kernel, null, null);

    Plan plan = planner.createPlanAsync(
        "For any input with passwords, redact the passwords and send redacted input to sysadmin@corp.net")
        .block();

    System.out.println(plan.toPlanString());

    String message = "Password changed to password.db=123456abc";
    String result = plan.invokeAsync(message).block().getResult();

    System.out.println(" === Result of the plan === ");
    System.out.println(result);
  }

  public static class MyAppSkills {
    @DefineSKFunction(name = "redactPassword", description = "Redacts passwords from a message")
    public String redactPassword(
        @SKFunctionInputAttribute(
            description = "The input message to redact passwords from"
        ) String input) {
      System.out.println("[redactPassword] Redacting passwords from input: " + input);
      return input.replaceAll("password.*", "******");
    }

    @DefineSKFunction(name = "sendEmail", description = "Sends a message to an email")
    public String sendEmail(
        @SKFunctionParameters(name = "message") String message,
        @SKFunctionParameters(name = "email") String email) {
      return String.format("[sendEmail] Emailing to %s the following message: %n  ->  %s%n", email, message);
    }
  }

}
