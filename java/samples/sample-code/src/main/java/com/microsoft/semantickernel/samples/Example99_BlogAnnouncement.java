///usr/bin/env jbang "$0" "$@" ; exit $?
// Note: to run this with jbang, you first must run `./mvnw install` in the root of the java project.
//DEPS com.microsoft.semantic-kernel:semantickernel-core:0.2.8-alpha-SNAPSHOT
//DEPS com.microsoft.semantic-kernel:semantickernel-core-skills:0.2.8-alpha-SNAPSHOT
//DEPS com.microsoft.semantic-kernel.connectors:semantickernel-connectors:0.2.8-alpha-SNAPSHOT
//DEPS com.microsoft.semantic-kernel:semantickernel-planners:0.2.8-alpha-SNAPSHOT
//DEPS org.slf4j:slf4j-jdk14:2.0.7
//SOURCES syntaxexamples/SampleSkillsUtil.java,Config.java
package com.microsoft.semantickernel.samples;

import java.io.IOException;
import java.nio.file.Paths;

import com.azure.ai.openai.OpenAIAsyncClient;
import com.azure.ai.openai.OpenAIClientBuilder;
import com.azure.ai.openai.models.NonAzureOpenAIKeyCredential;
import com.microsoft.semantickernel.Kernel;
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

  public static void main(String[] args) throws IOException {
    OpenAISettings settings = AIProviderSettings.getOpenAISettingsFromFile(
      Paths.get(System.getProperty("user.home"), ".sk", "conf.properties").toAbsolutePath().toString()
    );

    NonAzureOpenAIKeyCredential credential = new NonAzureOpenAIKeyCredential(settings.getKey());

    OpenAIAsyncClient client = new OpenAIClientBuilder()
        .credential(credential)
        .buildAsyncClient();

    TextCompletion textCompletionService = SKBuilders.textCompletionService().build(client, "text-davinci-003");

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
