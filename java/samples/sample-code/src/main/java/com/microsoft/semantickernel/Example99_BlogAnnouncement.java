package com.microsoft.semantickernel;

import com.azure.ai.openai.OpenAIAsyncClient;
import com.azure.ai.openai.OpenAIClientBuilder;
import com.azure.ai.openai.models.NonAzureOpenAIKeyCredential;
import com.microsoft.semantickernel.builders.SKBuilders;
import com.microsoft.semantickernel.connectors.ai.openai.util.AIProviderSettings;
import com.microsoft.semantickernel.connectors.ai.openai.util.OpenAISettings;
import com.microsoft.semantickernel.planner.actionplanner.Plan;
import com.microsoft.semantickernel.planner.sequentialplanner.SequentialPlanner;
import com.microsoft.semantickernel.skilldefinition.annotations.DefineSKFunction;
import com.microsoft.semantickernel.skilldefinition.annotations.SKFunctionInputAttribute;
import com.microsoft.semantickernel.skilldefinition.annotations.SKFunctionParameters;
import com.microsoft.semantickernel.textcompletion.TextCompletion;

public class Example99_BlogAnnouncement {

  static {
    System.setProperty("client.openai.key", "");
  }

  public static void main(String[] args) {
    OpenAISettings settings = AIProviderSettings.getOpenAISettingsFromSystemProperties();

    NonAzureOpenAIKeyCredential credential = new NonAzureOpenAIKeyCredential(settings.getKey());

    OpenAIAsyncClient client = new OpenAIClientBuilder()
        .credential(credential)
        .buildAsyncClient();

    TextCompletion textCompletionService = SKBuilders.textCompletionService().build(client, "text-davinci-003");

    KernelConfig config = SKBuilders.kernelConfig().addTextCompletionService("davinci", k -> textCompletionService)
        .build();

    Kernel kernel = SKBuilders.kernel().withKernelConfig(config).build();
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
        @SKFunctionInputAttribute String input) {
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
