package com.microsoft.semantickernel.orchestration;

import com.microsoft.semantickernel.Todo;
import java.util.Collections;
import java.util.Map;
import javax.annotation.Nullable;

public abstract class DefaultKernelFunction implements KernelFunction {

    /// <summary>
    /// Gets the metadata describing the function.
    /// </summary>
    /// <returns>An instance of <see cref="KernelFunctionMetadata"/> describing the function</returns>
    private final KernelFunctionMetadata metadata;

    /// <summary>
    /// Gets the prompt execution settings.
    /// </summary>
    @Nullable
    private final Map<String, PromptExecutionSettings> executionSettings;

    protected DefaultKernelFunction(
        KernelFunctionMetadata metadata,
        @Nullable
        Map<String, PromptExecutionSettings> executionSettings) {
        this.metadata = metadata;
        this.executionSettings = executionSettings;
    }

    @Override
    public KernelFunctionMetadata getMetadata() {
        return metadata;
    }


    @Override
    public String getSkillName() {
        return metadata.getName();
    }

    @Override
    public String getName() {
        return metadata.getName();
    }

    @Override
    @Nullable
    public String getDescription() {
        return metadata.getDescription();
    }

    @Override
    public String toEmbeddingString() {
        throw new Todo();
    }

    @Override
    public String toManualString(boolean includeOutputs) {
        throw new Todo();
    }

    @Override
    @Nullable
    public Map<String, PromptExecutionSettings> getExecutionSettings() {
        if (executionSettings != null) {
            return Collections.unmodifiableMap(executionSettings);
        } else {
            return null;
        }
    }
}
