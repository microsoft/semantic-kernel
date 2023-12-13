// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.skilldefinition;

import com.microsoft.semantickernel.Kernel;
import java.util.function.Supplier;

public interface KernelSkillsSupplier extends Supplier<ReadOnlySkillCollection> {

    @Deprecated
    static KernelSkillsSupplier getInstance(Kernel kernel) {
        return null; // kernel::getSkills;
    }
}
