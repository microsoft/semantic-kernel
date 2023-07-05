// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel;

import com.microsoft.semantickernel.exceptions.SkillsNotFoundException;
import com.microsoft.semantickernel.semanticfunctions.SemanticFunctionConfig;
import com.microsoft.semantickernel.skilldefinition.ReadOnlyFunctionCollection;
import com.microsoft.semantickernel.skilldefinition.ReadOnlySkillCollection;

import java.util.Map;

import javax.annotation.Nullable;

public interface SkillExecutor {

    /**
     * Import a set of skills
     *
     * @param skillName
     * @param skills
     * @return
     * @throws SkillsNotFoundException
     */
    ReadOnlyFunctionCollection importSkill(
            String skillName, Map<String, SemanticFunctionConfig> skills)
            throws SkillsNotFoundException;

    /**
     * Get function collection with the skill name
     *
     * @param skillName
     * @return
     * @throws SkillsNotFoundException
     */
    ReadOnlyFunctionCollection getSkill(String skillName) throws SkillsNotFoundException;

    /**
     * Imports the native functions annotated on the given object as a skill.
     *
     * @param skillName
     * @return
     */
    ReadOnlyFunctionCollection importSkillFromDirectory(
            String skillName, String parentDirectory, String skillDirectoryName);

    /** Imports the native functions annotated on the given object as a skill. */
    void importSkillsFromDirectory(String parentDirectory, String... skillNames);

    /**
     * Imports the native functions annotated on the given object as a skill. Assumes that the
     * directory that contains the skill is the same as skillName
     *
     * @param skillName
     * @return
     */
    ReadOnlyFunctionCollection importSkillFromDirectory(String skillName, String parentDirectory);

    /**
     * Imports the native functions annotated on the given object as a skill.
     *
     * @param nativeSkill
     * @param skillName
     * @return
     */
    ReadOnlyFunctionCollection importSkill(Object nativeSkill, @Nullable String skillName);

    /**
     * @return Reference to the read-only skill collection containing all the imported functions
     */
    ReadOnlySkillCollection getSkills();
}
