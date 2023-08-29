// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.orchestration;

import com.microsoft.semantickernel.SKBuilders;
import com.microsoft.semantickernel.memory.NullMemory;
import com.microsoft.semantickernel.memory.SemanticTextMemory;
import com.microsoft.semantickernel.orchestration.FunctionNotRegisteredException.ErrorCodes;
import com.microsoft.semantickernel.skilldefinition.KernelSkillsSupplier;
import com.microsoft.semantickernel.skilldefinition.ParameterView;
import com.microsoft.semantickernel.skilldefinition.ReadOnlySkillCollection;
import com.microsoft.semantickernel.skilldefinition.annotations.SKFunctionParameters;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.stream.Collectors;
import javax.annotation.Nullable;
import reactor.core.publisher.Mono;

/** Abstract implementation of the SKFunction interface. */
public abstract class AbstractSkFunction<RequestConfiguration>
        implements SKFunction<RequestConfiguration>, RegistrableSkFunction {

    private final List<ParameterView> parameters;
    private final String skillName;
    private final String functionName;
    private final String description;
    @Nullable private KernelSkillsSupplier skillsSupplier;

    /**
     * Constructor.
     *
     * @param parameters The parameters of the function.
     * @param skillName The name of the skill.
     * @param functionName The name of the function.
     * @param description The description of the function.
     * @param skillsSupplier The skill supplier.
     */
    public AbstractSkFunction(
            List<ParameterView> parameters,
            String skillName,
            String functionName,
            String description,
            @Nullable KernelSkillsSupplier skillsSupplier) {

        this.parameters = new ArrayList<>(parameters);
        this.skillName = skillName;
        this.functionName = functionName;
        this.description = description;
        this.skillsSupplier = skillsSupplier;
    }

    /**
     * Asserts that the skill supplier is registered.
     *
     * @throws FunctionNotRegisteredException if the skill supplier is not registered.
     */
    protected void assertSkillSupplierRegistered() {
        if (skillsSupplier == null) {
            throw new FunctionNotRegisteredException(ErrorCodes.FUNCTION_NOT_REGISTERED, getName());
        }
    }

    /**
     * Sets the skill supplier.
     *
     * @param skillsSupplier The skill supplier.
     */
    protected void setSkillsSupplier(@Nullable KernelSkillsSupplier skillsSupplier) {
        this.skillsSupplier = skillsSupplier;
    }

    /**
     * Gets the skill supplier.
     *
     * @return The skill supplier.
     */
    @Nullable
    public KernelSkillsSupplier getSkillsSupplier() {
        return skillsSupplier;
    }

    @Override
    public Mono<SKContext> invokeAsync(
            @Nullable String input,
            @Nullable SKContext context,
            @Nullable RequestConfiguration settings) {
        if (context == null) {
            assertSkillSupplierRegistered();

            context =
                    SKBuilders.context()
                            .withMemory(NullMemory.getInstance())
                            .withSkills(skillsSupplier == null ? null : skillsSupplier.get())
                            .build();
        } else {
            context = context.copy();
        }

        if (input != null) {
            context = context.update(input);
        }

        return this.invokeAsync(context, settings);
    }

    @Override
    public Mono<SKContext> invokeAsync(String input) {
        return invokeAsync(input, null, null);
    }

    @Override
    public Mono<SKContext> invokeAsync(
            @Nullable SKContext context, @Nullable RequestConfiguration settings) {
        if (context == null) {
            context =
                    SKBuilders.context()
                            .withVariables(SKBuilders.variables().build())
                            .withMemory(NullMemory.getInstance())
                            .build();
        } else {
            context = context.copy();
        }

        return this.invokeAsyncInternal(context, settings);
    }

    /**
     * The function to invoke asynchronously.
     *
     * @param context The context.
     * @param settings The settings.
     * @return A mono of the context with the result.
     */
    protected abstract Mono<SKContext> invokeAsyncInternal(
            SKContext context, @Nullable RequestConfiguration settings);

    @Override
    public String getSkillName() {
        return skillName;
    }

    @Override
    public String getName() {
        return functionName;
    }

    /**
     * The parameters of the function.
     *
     * @return The parameters of the function.
     */
    public List<ParameterView> getParametersView() {
        return Collections.unmodifiableList(parameters);
    }

    /**
     * The function to create a fully qualified name for
     *
     * @return A fully qualified name for a function
     */
    @Override
    public String toFullyQualifiedName() {
        return skillName + "." + functionName;
    }

    @Override
    @Nullable
    public String getDescription() {
        return description;
    }

    @Override
    public String toEmbeddingString() {
        String inputs =
                parameters.stream()
                        .map(p -> "    - " + p.getName() + ": " + p.getDescription())
                        .collect(Collectors.joining("\n"));

        return getName() + ":\n  description: " + getDescription() + "\n  inputs:\n" + inputs;
    }

    @Override
    public String toManualString() {
        String inputs =
                parameters.stream()
                        .map(
                                parameter -> {
                                    String defaultValueString;
                                    if (parameter.getDefaultValue() == null
                                            || parameter.getDefaultValue().isEmpty()
                                            || parameter
                                                    .getDefaultValue()
                                                    .equals(
                                                            SKFunctionParameters
                                                                    .NO_DEFAULT_VALUE)) {
                                        defaultValueString = "";
                                    } else {
                                        defaultValueString =
                                                " (default value: "
                                                        + parameter.getDefaultValue()
                                                        + ")";
                                    }

                                    return "  - "
                                            + parameter.getName()
                                            + ": "
                                            + parameter.getDescription()
                                            + defaultValueString;
                                })
                        .collect(Collectors.joining("\n"));

        return toFullyQualifiedName()
                + ":\n"
                + "  description: "
                + getDescription()
                + "\n"
                + "  inputs:\n"
                + inputs;
    }

    @Override
    public Mono<SKContext> invokeWithCustomInputAsync(
            ContextVariables variables,
            @Nullable SemanticTextMemory semanticMemory,
            @Nullable ReadOnlySkillCollection skills) {
        SKContext tmpContext =
                SKBuilders.context()
                        .withVariables(variables)
                        .withMemory(semanticMemory)
                        .withSkills(skills)
                        .build();
        return invokeAsync(tmpContext, null);
    }

    @Override
    public Mono<SKContext> invokeAsync() {
        return invokeAsync(null, null, null);
    }

    @Override
    public Mono<SKContext> invokeAsync(SKContext context) {
        return invokeAsync(context, null);
    }
}
