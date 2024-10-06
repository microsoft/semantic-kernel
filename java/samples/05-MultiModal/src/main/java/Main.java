
import java.io.IOException;

import com.azure.core.http.HttpClient;

import com.azure.ai.openai.OpenAIAsyncClient;
import com.azure.ai.openai.OpenAIClientBuilder;
import com.azure.core.credential.KeyCredential;
import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.SKBuilders;
import com.microsoft.semantickernel.exceptions.ConfigurationException;
import com.microsoft.semantickernel.orchestration.ContextVariables;
import com.microsoft.semantickernel.orchestration.SKFunction;
import com.microsoft.semantickernel.plugin.Plugin;
import com.microsoft.semantickernel.semanticfunctions.SemanticFunction;
import com.microsoft.semantickernel.templateengine.handlebars.HandlebarsPromptTemplateEngine;
import com.microsoft.semantickernel.aiservices.AIFunctionResultExtensions;
import com.microsoft.semantickernel.aiservices.huggingface.fillmasktask.HuggingFaceFillMaskTask;
import com.microsoft.semantickernel.aiservices.huggingface.questionansweringtask.HuggingFaceQuestionAnsweringTask;
import com.microsoft.semantickernel.aiservices.huggingface.summarizationtask.HuggingFaceSummarizationTask;
import com.microsoft.semantickernel.aiservices.ollama.OllamaGeneration;

public class Main {
    
    final static String GPT_35_TURBO_DEPLOYMENT_NAME = System.getenv("GPT_35_TURBO_DEPLOYMENT_NAME");
    final static String AZURE_OPENAI_ENDPOINT = System.getenv("AZURE_OPENAI_ENDPOINT");
    final static String AZURE_OPENAI_API_KEY = System.getenv("AZURE_OPENAI_API_KEY");
    final static String HUGGING_FACE_API_KEY = System.getenv("HUGGING_FACE_API_KEY");
    final static String HUGGING_FACE_FILL_MASK_TASK_ENDPOINT = System.getenv("HUGGING_FACE_FILL_MASK_TASK_ENDPOINT");
    final static String HUGGING_FACE_QUESTION_ANSWERING_TASK_ENDPOINT = System.getenv("HUGGING_FACE_QUESTION_ANSWERING_TASK_ENDPOINT");
    final static String HUGGING_FACE_SUMMARIZATION_TASK_ENDPOINT = System.getenv("HUGGING_FACE_SUMMARIZATION_TASK_ENDPOINT");
    final static String HUGGING_FACE_TEXT_TO_IMAGE_TASK_ENDPOINT = System.getenv("HUGGING_FACE_TEXT_TO_IMAGE_TASK_ENDPOINT");
    final static String OPENAI_API_KEY = System.getenv("OPENAI_API_KEY");
    final static String CURRENT_DIRECTORY = System.getProperty("user.dir");
    
    
    public static void main(String[] args) throws ConfigurationException, IOException  {

        OpenAIAsyncClient client = new OpenAIClientBuilder()
            .credential(new KeyCredential(AZURE_OPENAI_API_KEY))
            .endpoint(AZURE_OPENAI_ENDPOINT)
            .buildAsyncClient();


        HuggingFaceFillMaskTask huggingFaceFillMaskTask = new HuggingFaceFillMaskTask("bert-base-uncased", HUGGING_FACE_API_KEY,  HttpClient.createDefault(), HUGGING_FACE_FILL_MASK_TASK_ENDPOINT);
        HuggingFaceQuestionAnsweringTask huggingFaceQuestionAnsweringTask = new HuggingFaceQuestionAnsweringTask("deepset/roberta-base-squad2", HUGGING_FACE_API_KEY,  HttpClient.createDefault(), HUGGING_FACE_QUESTION_ANSWERING_TASK_ENDPOINT);
        HuggingFaceSummarizationTask huggingFaceSummarizationTask = new HuggingFaceSummarizationTask("facebook/bart-large-cnn", HUGGING_FACE_API_KEY,  HttpClient.createDefault(), HUGGING_FACE_SUMMARIZATION_TASK_ENDPOINT);
        OllamaGeneration ollamaGeneration = new OllamaGeneration("wizard-math");

        SKFunction fillMaskTaskFunction = SemanticFunction.fromYaml(CURRENT_DIRECTORY + "/Plugins/HuggingFace/FillMaskTask.prompt.yaml");
        SKFunction questionAnsweringTaskFunction = SemanticFunction.fromYaml(CURRENT_DIRECTORY + "/Plugins/HuggingFace/QuestionAnsweringTask.prompt.yaml");
        SKFunction summarizationTaskFunction = SemanticFunction.fromYaml(CURRENT_DIRECTORY + "/Plugins/HuggingFace/SummarizationTask.prompt.yaml");
        SKFunction textToImageTaskFunction = SemanticFunction.fromYaml(CURRENT_DIRECTORY + "/Plugins/HuggingFace/TextToImageTask.prompt.yaml");
        SKFunction imageToTextTaskFunction = SemanticFunction.fromYaml(CURRENT_DIRECTORY + "/Plugins/HuggingFace/ImageToTextTask.prompt.yaml");
        SKFunction ollamaGenerationFunction = SemanticFunction.fromYaml(CURRENT_DIRECTORY + "/Plugins/Ollama/Math.prompt.yaml");

        // Create plugin
        Plugin huggingFaceTaskPlugin = new com.microsoft.semantickernel.plugin.Plugin(
            "HuggingFace",
            fillMaskTaskFunction,
            questionAnsweringTaskFunction,
            summarizationTaskFunction,
            textToImageTaskFunction
        );   
        
        Plugin ollamaGenerationPlugin = new com.microsoft.semantickernel.plugin.Plugin(
            "Ollama",
            ollamaGenerationFunction
        );

        Kernel kernel = SKBuilders.kernel()
            //.withDefaultAIService(gpt35Turbo)
            //.withDefaultAIService(gpt4)
            //.withDefaultAIService(huggingFaceFillMaskTask)
            //.withDefaultAIService(huggingFaceQuestionAnsweringTask)
            //.withDefaultAIService(huggingFaceSummarizationTask)
            //.withDefaultAIService(huggingFaceTextToImageTask)
            .withDefaultAIService(ollamaGeneration)
            .withPlugins(ollamaGenerationPlugin)
            .withPromptTemplateEngine(new HandlebarsPromptTemplateEngine())
            .build();


        // // Running Face Mask Task
        // var faceMaskTaskResult = await kernel.RunAsync( fillMaskTaskFunction, variables: new() {});
        // faceMaskTaskResult.TryGetMetadataValue<List<FillMaskTaskResponse>>(AIFunctionResultExtensions.ModelResultsMetadataKey, out var fillMaskTaskResponses);
        // PrintResult("Face Mask Task", faceMaskTaskResult.GetValue<string>()!, fillMaskTaskResponses);

        // // Running Summarization Task
        // var summarizationTaskResult = await kernel.RunAsync( questionAnsweringTaskFunction, variables: new() {});
        // summarizationTaskResult.TryGetMetadataValue<List<SummarizationTaskResponse>>(AIFunctionResultExtensions.ModelResultsMetadataKey, out var summarizationTaskResponses);
        // PrintResult("Summarization Task", summarizationTaskResult.GetValue<string>()!, summarizationTaskResponses);

        // // Running Question Answering Task
        // var questionAnsweringTaskResult = await kernel.RunAsync( summarizationTaskFunction, variables: new() {});
        // questionAnsweringTaskResult.TryGetMetadataValue<QuestionAnsweringTaskResponse>(AIFunctionResultExtensions.ModelResultsMetadataKey, out var questionAnsweringTaskResponses);
        // PrintResult("Question Answering Task", questionAnsweringTaskResult.GetValue<string>()!, questionAnsweringTaskResponses);

        // // Running Text to Image Task
        // var questionTextToImageResult = await kernel.RunAsync( textToImageTaskFunction, variables: new() {});
        // Image image = questionTextToImageResult.GetValue<Image>()!;
        // var filePath = "/Users/matthewbolanos/Downloads/image.png";
        // await File.WriteAllBytesAsync(filePath, image.Bytes);
        // PrintResult("Text to Image Task", filePath, image.ToString());

        // // Running Image to Text Task
        // var imageToTextResult = await kernel.RunAsync( imageToTextTaskFunction, variables: new() {});
        // imageToTextResult.TryGetMetadataValue<OpenAIChatResponse>(AIFunctionResultExtensions.ModelResultsMetadataKey, out var imageToTextTaskResponses);
        // PrintResult("Image to Text Task", imageToTextResult.GetValue<string>()!, imageToTextTaskResponses);

        // Running local Ollama Generation
        var mathResult = kernel.runAsync(ContextVariables.builder().build(), ollamaGenerationFunction).block();
        mathResult.functionResults().forEach(
            functionResult -> {
                var ollamaGenerationResponses = functionResult.tryGetMetadataValue(AIFunctionResultExtensions.getModelResultsMetadataKey());
                printResult("Ollama Generation", functionResult.<String>getValue(), ollamaGenerationResponses);
            }
        );          
    }

    static void printResult(String title, String result, Object modelResults)
    {
        System.console().printf("%s%n====================================", title);
        System.console().printf("Reslt: %s\n", result);
        System.console().printf("Raw Results: %s\n", modelResults);
    }

}
