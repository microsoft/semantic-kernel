package com.microsoft.semantickernel.plugin;

import com.fasterxml.jackson.databind.JsonMappingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.microsoft.semantickernel.exceptions.SKException;
import com.microsoft.semantickernel.orchestration.KernelFunction;
import com.microsoft.semantickernel.orchestration.contextvariables.CaseInsensitiveMap;
import com.microsoft.semantickernel.plugin.annotations.DefineKernelFunction;
import com.microsoft.semantickernel.plugin.annotations.KernelFunctionParameter;
import com.microsoft.semantickernel.semanticfunctions.KernelFunctionFromPrompt.Builder;
import com.microsoft.semantickernel.semanticfunctions.KernelPromptTemplateFactory;
import com.microsoft.semantickernel.semanticfunctions.PromptTemplate;
import com.microsoft.semantickernel.semanticfunctions.PromptTemplateConfig;
import com.microsoft.semantickernel.semanticfunctions.PromptTemplateFactory;
import com.microsoft.semantickernel.util.EmbeddedResourceLoader;
import com.microsoft.semantickernel.util.EmbeddedResourceLoader.ResourceLocation;
import java.io.File;
import java.io.FileNotFoundException;
import java.io.IOException;
import java.lang.reflect.Method;
import java.nio.charset.Charset;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Arrays;
import java.util.Collections;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;
import javax.annotation.Nullable;
import org.reactivestreams.Publisher;
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
    public static KernelPlugin createFromObject(Object target, @Nullable String pluginName) {
        List<KernelFunction> methods = Arrays.stream(target.getClass().getMethods())
            .filter(method -> method.isAnnotationPresent(DefineKernelFunction.class))
            .map(method -> {
                DefineKernelFunction annotation = method.getAnnotation(DefineKernelFunction.class);
                Class<?> returnType = getReturnType(annotation, method);
                KernelReturnParameterMetadata kernelReturnParameterMetadata = new KernelReturnParameterMetadata(
                    annotation.returnDescription(),
                    returnType);

                return KernelFunctionFactory
                    .createFromMethod(
                        method,
                        target,
                        annotation.name(),
                        annotation.description(),
                        getParameters(method),
                        kernelReturnParameterMetadata);
            }).collect(Collectors.toList());

        return createFromFunctions(pluginName, methods);
    }

    private static Class<?> getReturnType(DefineKernelFunction annotation, Method method) {
        Class<?> returnType;
        if (annotation.returnType().isEmpty()) {
            returnType = method.getReturnType();

            if (Publisher.class.isAssignableFrom(returnType)) {
                LOGGER.warn(
                    "For method: " + method.getDeclaringClass().getName() + "." + method.getName()
                        + ", this is an async method, if a return type is required, please specify it in the annotation. Defaulting to Void return type");
                returnType = Void.class;
            }
        } else {
            try {
                returnType = Thread.currentThread().getContextClassLoader()
                    .loadClass(annotation.returnType());

                if (!Publisher.class.isAssignableFrom(method.getReturnType())
                    && !returnType.isAssignableFrom(method.getReturnType())) {
                    throw new SKException(
                        "Return type " + returnType.getName() + " is not assignable from "
                            + method.getReturnType());
                }

            } catch (ClassNotFoundException e) {
                throw new SKException("Could not find return type " + annotation.returnType()
                    + "  is not found on method " + method.getDeclaringClass().getName() + "."
                    + method.getName());
            }
        }

        return returnType;
    }

    /// <summary>Initializes the new plugin from the provided name and function collection.</summary>
    /// <param name="pluginName">The name for the plugin.</param>
    /// <param name="functions">The initial functions to be available as part of the plugin.</param>
    /// <exception cref="ArgumentException"><paramref name="pluginName"/> is null.</exception>
    /// <exception cref="ArgumentException"><paramref name="pluginName"/> is an invalid plugin name.</exception>
    /// <exception cref="ArgumentNullException"><paramref name="functions"/> contains a null function.</exception>
    /// <exception cref="ArgumentException"><paramref name="functions"/> contains two functions with the same name.</exception>
    public static KernelPlugin createFromFunctions(String pluginName,
        @Nullable List<KernelFunction> functions) {
        return createFromFunctions(pluginName, null, functions);
    }

    /// <summary>Initializes the new plugin from the provided name, description, and function collection.</summary>
    /// <param name="pluginName">The name for the plugin.</param>
    /// <param name="description">A description of the plugin.</param>
    /// <param name="functions">The initial functions to be available as part of the plugin.</param>
    /// <exception cref="ArgumentException"><paramref name="pluginName"/> is null.</exception>
    /// <exception cref="ArgumentException"><paramref name="pluginName"/> is an invalid plugin name.</exception>
    /// <exception cref="ArgumentNullException"><paramref name="functions"/> contains a null function.</exception>
    /// <exception cref="ArgumentException"><paramref name="functions"/> contains two functions with the same name.</exception>
    public static KernelPlugin createFromFunctions(String pluginName, @Nullable String description,
        @Nullable List<KernelFunction> functions) {
        Map<String, KernelFunction> funcs = new HashMap<>();
        if (functions != null) {
            funcs = functions.stream().collect(Collectors.toMap(KernelFunction::getName, f -> f));
        }
        return new KernelPlugin(pluginName, description, funcs);
    }


    private static List<KernelParameterMetadata> getParameters(Method method) {
        return Arrays.stream(method.getParameters())
            .filter(parameter -> parameter.isAnnotationPresent(KernelFunctionParameter.class))
            .map(parameter -> {
                KernelFunctionParameter annotation = parameter.getAnnotation(
                    KernelFunctionParameter.class);

                return new KernelParameterMetadata(annotation.name(), annotation.description(),
                    annotation.defaultValue(), annotation.required());
            }).collect(Collectors.toList());
    }


    public static KernelPlugin importPluginFromDirectory(Path parentDirectory,
        String pluginDirectoryName, PromptTemplateFactory promptTemplateFactory) {

        // Verify.ValidSkillName(pluginDirectoryName);
        File pluginDir = new File(parentDirectory.toFile(), pluginDirectoryName);
        // Verify.DirectoryExists(pluginDir);
        if (!pluginDir.exists() || !pluginDir.isDirectory()) {
            throw new SKException("Could not find directory " + pluginDir.getAbsolutePath());
        }
        File[] files = pluginDir.listFiles(File::isDirectory);
        if (files == null) {
            throw new SKException("No Plugins found in directory " + pluginDir.getAbsolutePath());
        }

        Map<String, KernelFunction> plugins = new CaseInsensitiveMap<>();

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

                KernelFunction plugin = getKernelFunction(pluginDirectoryName,
                    promptTemplateFactory, configPath, promptPath);

                plugins.put(dir.getName(), plugin);
            } catch (IOException e) {
                LOGGER.error("Failed to read file", e);
            }
        }

        return new KernelPlugin(
            pluginDirectoryName,
            null,
            plugins
        );
    }

    private static KernelFunction getKernelFunction(String pluginDirectoryName,
        PromptTemplateFactory promptTemplateFactory, File configPath, File promptPath)
        throws IOException {
        PromptTemplateConfig config = new ObjectMapper().readValue(configPath,
            PromptTemplateConfig.class);

        // Load prompt template
        String template = new String(Files.readAllBytes(promptPath.toPath()),
            Charset.defaultCharset());

        return getKernelFunction(pluginDirectoryName, promptTemplateFactory, config, template);
    }

    private static KernelFunction getKernelFunction(String pluginDirectoryName,
        PromptTemplateFactory promptTemplateFactory, PromptTemplateConfig config, String template) {
        PromptTemplate promptTemplate;

        if (promptTemplateFactory != null) {
            promptTemplate = promptTemplateFactory.tryCreate(config);
        } else {
            promptTemplate = new KernelPromptTemplateFactory().tryCreate(config);
        }

        return new Builder().withName(config.getName()).withDescription(config.getDescription())
            .withExecutionSettings(config.getExecutionSettings())
            .withInputParameters(config.getInputVariables()).withPromptTemplate(promptTemplate)
            .withPluginName(pluginDirectoryName).withTemplate(template)
            .withTemplateFormat(config.getTemplateFormat())
            .withOutputVariable(config.getOutputVariable())
            .withPromptTemplateFactory(promptTemplateFactory).build();
    }

    public static KernelPlugin importPluginFromResourcesDirectory(String parentDirectory,
        String pluginDirectoryName, String functionName,
        PromptTemplateFactory promptTemplateFactory, @Nullable Class<?> clazz) {

        String template = getTemplatePrompt(parentDirectory, pluginDirectoryName, functionName,
            clazz);

        PromptTemplateConfig promptTemplateConfig = getPromptTemplateConfig(parentDirectory,
            pluginDirectoryName, functionName, clazz);

        KernelFunction function = getKernelFunction(pluginDirectoryName, promptTemplateFactory,
            promptTemplateConfig, template);

        HashMap<String, KernelFunction> plugins = new HashMap<>();

        plugins.put(functionName, function);

        return new KernelPlugin(
            pluginDirectoryName,
            promptTemplateConfig.getDescription(),
            plugins
        );
    }

    private static String getTemplatePrompt(String pluginDirectory, String pluginName,
        String functionName, @Nullable Class clazz) {
        String promptFileName =
            pluginDirectory + File.separator + pluginName + File.separator + functionName
                + File.separator + PROMPT_FILE;

        try {
            return getFileContents(promptFileName, clazz);
        } catch (IOException e) {
            LOGGER.error("Failed to read file " + promptFileName, e);

            throw new SKException("No Skills found in directory " + promptFileName);
        }
    }

    private static String getFileContents(String file, @Nullable Class clazz)
        throws FileNotFoundException {
        return EmbeddedResourceLoader.readFile(file, clazz, ResourceLocation.CLASSPATH_ROOT,
            ResourceLocation.CLASSPATH, ResourceLocation.FILESYSTEM);
    }

    private static PromptTemplateConfig getPromptTemplateConfig(String pluginDirectory,
        String pluginName, String functionName, @Nullable Class clazz) {
        String configFileName =
            pluginDirectory + File.separator + pluginName + File.separator + functionName
                + File.separator + CONFIG_FILE;

        try {
            String config = getFileContents(configFileName, clazz);

            return new ObjectMapper().readValue(config, PromptTemplateConfig.class);
        } catch (IOException e) {
            if (e instanceof JsonMappingException) {
                LOGGER.error("Failed to parse config file " + configFileName, e);

                throw new SKException("Failed to parse config file " + configFileName, e);
            } else {
                LOGGER.debug("No config for " + functionName + " in " + pluginName);
            }
            return null;
        }
    }
}
