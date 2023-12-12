// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel;

import java.util.Map;

import javax.annotation.Nullable;

import com.microsoft.semantickernel.exceptions.SkillsNotFoundException;
import com.microsoft.semantickernel.semanticfunctions.SemanticFunctionConfig;
import com.microsoft.semantickernel.skilldefinition.ReadOnlyFunctionCollection;
import com.microsoft.semantickernel.skilldefinition.ReadOnlySkillCollection;

public interface SkillExecutor {

    /**
     * Import a set of skills
     *
     * @param skillName name of the skill
     * @param skills map of skill names to skill configs
     * @return the function collection
     * @throws SkillsNotFoundException if the skill is not found
     */
    @Deprecated
    default ReadOnlyFunctionCollection importSkill(
            String skillName, Map<String, SemanticFunctionConfig> skills)
            throws SkillsNotFoundException { 
                throw new UnsupportedOperationException("Deprecated"); 
        }

    /**
     * Get function collection with the skill name
     *
     * @param skillName name of the skill
     * @return the function collection
     * @throws SkillsNotFoundException if the skill is not found
     */
    @Deprecated
    default ReadOnlyFunctionCollection getSkill(String skillName) throws SkillsNotFoundException { 
                throw new UnsupportedOperationException("Deprecated"); 
        }

    /**
     * Imports the native functions annotated on the given object as a skill.
     *
     * @param skillName name of the skill
     * @return the function collection
     */
    @Deprecated
    default ReadOnlyFunctionCollection importSkillFromDirectory(
            String skillName, String parentDirectory, String skillDirectoryName) { 
                throw new UnsupportedOperationException("Deprecated"); 
        }

    /** Imports the native functions annotated on the given object as a skill. */
    @Deprecated
    default void importSkillsFromDirectory(String parentDirectory, String... skillNames) { 
                throw new UnsupportedOperationException("Deprecated"); 
        }

    /**
     * Imports the native functions annotated on the given object as a skill. Assumes that the
     * directory that contains the skill is the same as skillName
     *
     * @param skillName name of the skill
     * @param parentDirectory directory that contains the skill
     * @return the function collection
     */
    @Deprecated
    default ReadOnlyFunctionCollection importSkillFromDirectory(String skillName, String parentDirectory) { 
                throw new UnsupportedOperationException("Deprecated"); 
        }

    /**
     * Imports a skill using ClassLoader.getResourceAsStream to load skills from the classpath.
     *
     * @param pluginDirectory directory within the classpath that contains the skill
     * @param skillName name of the skill
     * @param functionName name of the function
     * @return the function collection
     * @throws KernelException if it is not possible to correctly load the skill
     */
    @Deprecated
    default ReadOnlyFunctionCollection importSkillFromResources(
            String pluginDirectory, String skillName, String functionName) throws KernelException { 
                throw new UnsupportedOperationException("Deprecated"); 
        }

    /**
     * Imports a skill using clazz.getResourceAsStream to load skills from the classpath.
     *
     * @param skillName name of the skill
     * @param functionName name of the function
     * @param clazz class that contains the skill
     * @return the function collection
     * @throws KernelException if it is not possible to correctly load the skill
     */
    @Deprecated
    default  ReadOnlyFunctionCollection importSkillFromResources(
            String pluginDirectory, String skillName, String functionName, @Nullable Class clazz)
            throws KernelException { 
                throw new UnsupportedOperationException("Deprecated"); 
        }

    /**
     * Imports the native functions annotated on the given object as a skill.
     *
     * @param nativeSkill object containing the native functions
     * @param skillName name of the skill
     * @return the function collection
     */
    @Deprecated
    default ReadOnlyFunctionCollection importSkill(Object nativeSkill, @Nullable String skillName) { 
                throw new UnsupportedOperationException("Deprecated"); 
        }

    /**
     * @return Reference to the read-only skill collection containing all the imported functions
     */
    @Deprecated
    default ReadOnlySkillCollection getSkills() { 
                throw new UnsupportedOperationException("Deprecated"); 
        }
}
