// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.skilldefinition;

import java.util.function.Supplier;

import com.microsoft.semantickernel.Kernel;

public interface KernelSkillsSupplier extends Supplier<ReadOnlySkillCollection> {

    @Deprecated
    static KernelSkillsSupplier getInstance(Kernel kernel) {
        return null; //kernel::getSkills;
    }
}
