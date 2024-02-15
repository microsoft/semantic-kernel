// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.orchestration;

import com.microsoft.semantickernel.ai.AIRequestSettings;
import com.microsoft.semantickernel.services.AIServiceSupplier;
import com.microsoft.semantickernel.skilldefinition.KernelSkillsSupplier;
import com.microsoft.semantickernel.skilldefinition.ParameterView;
import java.util.List;
import javax.annotation.Nullable;

public abstract class AIFunction<RequestConfiguration extends AIRequestSettings>
        extends AbstractSkFunction<RequestConfiguration>
        implements SKFunction<RequestConfiguration> {

    @Nullable private AIServiceSupplier aiServiceSupplier;

    /**
     * Constructor.
     *
     * @param parameters The parameters of the function.
     * @param skillName The name of the skill.
     * @param functionName The name of the function.
     * @param description The description of the function.
     * @param returnParameters
     * @param skillsSupplier The skill supplier.
     */
    public AIFunction(
            List<ParameterView> parameters,
            String skillName,
            String functionName,
            String description,
            List<ParameterView> returnParameters,
            @Nullable KernelSkillsSupplier skillsSupplier,
            @Nullable AIServiceSupplier aiServiceSupplier) {
        super(parameters, skillName, functionName, description, returnParameters, skillsSupplier);
        this.aiServiceSupplier = aiServiceSupplier;
    }

    protected void setServiceSupplier(@Nullable AIServiceSupplier aiServiceSupplier) {
        this.aiServiceSupplier = aiServiceSupplier;
    }

    @Nullable
    protected AIServiceSupplier getAiServiceSupplier() {
        return aiServiceSupplier;
    }
}
