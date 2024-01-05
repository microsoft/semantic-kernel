package com.microsoft.semantickernel.plugin;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.microsoft.semantickernel.Todo;
import com.microsoft.semantickernel.exceptions.SKException;
import com.microsoft.semantickernel.orchestration.KernelFunction;
import com.microsoft.semantickernel.orchestration.contextvariables.CaseInsensitiveMap;
import com.microsoft.semantickernel.plugin.annotations.DefineKernelFunction;
import com.microsoft.semantickernel.plugin.annotations.KernelFunctionParameter;
import com.microsoft.semantickernel.semanticfunctions.KernelFunctionFromPrompt;
import com.microsoft.semantickernel.semanticfunctions.KernelPromptTemplateFactory;
import com.microsoft.semantickernel.semanticfunctions.PromptTemplate;
import com.microsoft.semantickernel.semanticfunctions.PromptTemplateConfig;
import com.microsoft.semantickernel.semanticfunctions.PromptTemplateFactory;
import java.io.File;
import java.io.IOException;
import java.lang.reflect.Method;
import java.nio.charset.Charset;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Arrays;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;
import javax.annotation.Nullable;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class KernelPluginFactory {

    private static final Logger LOGGER = LoggerFactory.getLogger(KernelPluginFactory.class);
    private static final String CONFIG_FILE = "config.json";
    private static final String PROMPT_FILE = "skprompt.txt";

    /// <summary>Creates a plugin that wraps the specified target object.</summary>
    /// <param name="target">The instance of the class to be wrapped.</param>
    /// <param name="pluginName">
    /// Name of the plugin for function collection and prompt templates. If the value is null, a plugin name is derived from the type of the <paramref name="target"/>.
    /// </param>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    /// <remarks>
    /// Public methods decorated with <see cref="KernelFunctionAttribute"/> will be included in the plugin.
    /// Attributed methods must all have different names; overloads are not supported.
    /// </remarks>
    public static KernelPlugin createFromObject(
        Object target,
        @Nullable String pluginName) {
        List<KernelFunction> methods =
            Arrays.stream(target.getClass().getMethods())
                .filter(method -> method.isAnnotationPresent(DefineKernelFunction.class))
                .map(
                    method -> {
                        DefineKernelFunction annotation = method.getAnnotation(
                            DefineKernelFunction.class);
                        KernelReturnParameterMetadata kernelReturnParameterMetadata =
                            new KernelReturnParameterMetadata(
                                annotation.returnDescription()
                            );

                        return KernelFunctionFactory
                            .createFromMethod(
                                method,
                                target,
                                annotation.name(),
                                annotation.description(),
                                getParameters(method),
                                kernelReturnParameterMetadata);
                    })
                .collect(Collectors.toList());

        return createFromFunctions(pluginName, methods);
    }

    /// <summary>Initializes the new plugin from the provided name and function collection.</summary>
    /// <param name="pluginName">The name for the plugin.</param>
    /// <param name="functions">The initial functions to be available as part of the plugin.</param>
    /// <exception cref="ArgumentException"><paramref name="pluginName"/> is null.</exception>
    /// <exception cref="ArgumentException"><paramref name="pluginName"/> is an invalid plugin name.</exception>
    /// <exception cref="ArgumentNullException"><paramref name="functions"/> contains a null function.</exception>
    /// <exception cref="ArgumentException"><paramref name="functions"/> contains two functions with the same name.</exception>
    public static KernelPlugin createFromFunctions(
        String pluginName,
        @Nullable List<KernelFunction> functions) {

        if (functions == null) {
            return new DefaultKernelPlugin(
                pluginName,
                null,
                new HashMap<>()
            );
        }

        return new DefaultKernelPlugin(
            pluginName,
            null,
            functions.stream().collect(Collectors.toMap(KernelFunction::getName, f -> f))
        );
    }

    /// <summary>Initializes the new plugin from the provided name, description, and function collection.</summary>
    /// <param name="pluginName">The name for the plugin.</param>
    /// <param name="description">A description of the plugin.</param>
    /// <param name="functions">The initial functions to be available as part of the plugin.</param>
    /// <exception cref="ArgumentException"><paramref name="pluginName"/> is null.</exception>
    /// <exception cref="ArgumentException"><paramref name="pluginName"/> is an invalid plugin name.</exception>
    /// <exception cref="ArgumentNullException"><paramref name="functions"/> contains a null function.</exception>
    /// <exception cref="ArgumentException"><paramref name="functions"/> contains two functions with the same name.</exception>
    public static KernelPlugin createFromFunctions(String pluginName,
        @Nullable String description,
        @Nullable List<KernelFunction> functions) {
        throw new Todo();
    }


    private static List<KernelParameterMetadata> getParameters(Method method) {
        return Arrays.stream(method.getParameters())
            .filter(
                parameter ->
                    parameter.isAnnotationPresent(KernelFunctionParameter.class))
            .map(
                parameter -> {
                    KernelFunctionParameter annotation =
                        parameter.getAnnotation(KernelFunctionParameter.class);

                    return new KernelParameterMetadata(
                        annotation.name(),
                        annotation.description(),
                        annotation.defaultValue(),
                        annotation.required());
                })
            .collect(Collectors.toList());
    }


    public static KernelPlugin importPluginFromDirectory(
        Path parentDirectory,
        String skillDirectoryName,
        PromptTemplateFactory promptTemplateFactory) {

        // Verify.ValidSkillName(skillDirectoryName);
        File skillDir = new File(parentDirectory.toFile(), skillDirectoryName);
        // Verify.DirectoryExists(skillDir);
        if (!skillDir.exists() || !skillDir.isDirectory()) {
            throw new SKException(
                "Could not find directory " + skillDir.getAbsolutePath());
        }
        File[] files = skillDir.listFiles(File::isDirectory);
        if (files == null) {
            throw new SKException(
                "No Skills found in directory " + skillDir.getAbsolutePath());
        }

        Map<String, KernelFunction> skills = new CaseInsensitiveMap<>();

        for (File dir : files) {
            try {
                // Continue only if prompt template exists
                File promptPath = new File(dir, PROMPT_FILE);
                if (!promptPath.exists()) {
                    continue;
                }

                File configPath = new File(dir, CONFIG_FILE);
                if (!configPath.exists()) {
                    continue;

                    // Verify.NotNull(config, $"Invalid prompt template
                    // configuration, unable to parse {configPath}");
                }
                PromptTemplateConfig config = new ObjectMapper()
                    .readValue(configPath, PromptTemplateConfig.class);

                // kernel.Log.LogTrace("Config {0}: {1}", functionName,
                // config.ToJson());

                // Load prompt template
                String template = new String(Files.readAllBytes(promptPath.toPath()),
                    Charset.defaultCharset());

                PromptTemplate promptTemplate;

                if (promptTemplateFactory != null) {
                    promptTemplate = promptTemplateFactory.tryCreate(config);
                } else {
                    promptTemplate = new KernelPromptTemplateFactory().tryCreate(config);
                }

                skills.put(dir.getName(), new KernelFunctionFromPrompt.Builder()
                    .withName(config.getName())
                    .withDescription(config.getDescription())
                    .withExecutionSettings(config.getExecutionSettings())
                    .withInputParameters(config.getInputVariables())
                    .withPromptTemplate(promptTemplate)
                    .withPluginName(skillDirectoryName)
                    .withTemplate(template)
                    .withTemplateFormat(config.getTemplateFormat())
                    .withOutputVariable(config.getOutputVariable())
                    .withPromptTemplateFactory(promptTemplateFactory)
                    .build());
            } catch (IOException e) {
                LOGGER.error("Failed to read file", e);
            }
        }

        return new DefaultKernelPlugin(
            skillDirectoryName,
            null,
            skills
        );
    }
/*
    public static Map<String, SemanticFunctionConfig> importSemanticSkillFromResourcesDirectory(
        String pluginDirectory,
        String pluginName,
        String functionName,
        @Nullable Class clazz,
        PromptTemplateEngine promptTemplateEngine)
        throws KernelException {

        PromptConfig config =
            getPromptTemplateConfig(pluginDirectory, pluginName, functionName, clazz);

        if (config == null) {
            config = new PromptConfig("", "", null);
        }

        String template = getTemplatePrompt(pluginDirectory, pluginName, functionName, clazz);

        HashMap<String, SemanticFunctionConfig> skills = new HashMap<>();

        PromptTemplate promptTemplate =
            SKBuilders.promptTemplate()
                .withPromptTemplate(template)
                .withPromptTemplateConfig(config)
                .withPromptTemplateEngine(promptTemplateEngine)
                .build();

        skills.put(functionName, new SemanticFunctionConfig(config, promptTemplate));

        return skills;
    }

    private static String getTemplatePrompt(
        String pluginDirectory, String pluginName, String functionName, @Nullable Class clazz) {
        String promptFileName =
            pluginDirectory
                + File.separator
                + pluginName
                + File.separator
                + functionName
                + File.separator
                + PROMPT_FILE;

        try {
            return EmbeddedResourceLoader.readFile(
                promptFileName,
                clazz,
                ResourceLocation.CLASSPATH_ROOT,
                ResourceLocation.CLASSPATH,
                ResourceLocation.FILESYSTEM);
        } catch (IOException e) {
            LOGGER.error("Failed to read file " + promptFileName, e);

            throw new KernelException(
                ErrorCodes.FUNCTION_NOT_AVAILABLE,
                "No Skills found in directory " + promptFileName);
        }
    }

    private static PromptConfig getPromptTemplateConfig(
        String pluginDirectory, String pluginName, String functionName, @Nullable Class clazz)
        throws KernelException {
        String configFileName =
            pluginDirectory
                + File.separator
                + pluginName
                + File.separator
                + functionName
                + File.separator
                + CONFIG_FILE;

        try {
            String config =
                EmbeddedResourceLoader.readFile(
                    configFileName,
                    clazz,
                    ResourceLocation.CLASSPATH_ROOT,
                    ResourceLocation.CLASSPATH,
                    ResourceLocation.FILESYSTEM);

            return new ObjectMapper().readValue(config, PromptConfig.class);
        } catch (IOException e) {
            if (e instanceof JsonMappingException) {
                LOGGER.error("Failed to parse config file " + configFileName, e);

                throw new KernelException(
                    ErrorCodes.FUNCTION_CONFIGURATION_ERROR,
                    "Failed to parse config file " + configFileName,
                    e);
            } else {
                LOGGER.debug("No config for " + functionName + " in " + pluginName);
            }
            return null;
        }
    }

 */
}
