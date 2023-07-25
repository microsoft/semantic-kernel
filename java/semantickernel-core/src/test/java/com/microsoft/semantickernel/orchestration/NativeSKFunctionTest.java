// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.orchestration;

import com.microsoft.semantickernel.ai.AIException;
import com.microsoft.semantickernel.builders.SKBuilders;
import com.microsoft.semantickernel.coreskills.SkillImporter;
import com.microsoft.semantickernel.skilldefinition.DefaultSkillCollection;
import com.microsoft.semantickernel.skilldefinition.FunctionCollection;
import com.microsoft.semantickernel.skilldefinition.FunctionNotFound;
import com.microsoft.semantickernel.skilldefinition.annotations.DefineSKFunction;
import com.microsoft.semantickernel.skilldefinition.annotations.SKFunctionInputAttribute;
import com.microsoft.semantickernel.skilldefinition.annotations.SKFunctionParameters;

import org.junit.jupiter.api.Assertions;
import org.junit.jupiter.api.Test;
import org.mockito.Mockito;

import reactor.core.publisher.Mono;

import java.util.Objects;

public class NativeSKFunctionTest {

    @Test
    public void singleStringIsBoundToInput() {
        class SinleStringSkill {
            @DefineSKFunction
            public String doSomething(String anInput) {
                return "";
            }
        }

        SinleStringSkill skill = Mockito.spy(new SinleStringSkill());
        FunctionCollection skills =
                SkillImporter.importSkill(skill, "test", DefaultSkillCollection::new);
        SKContext ignore = skills.getFunction("doSomething").invokeAsync("foo").block();
        Mockito.verify(skill, Mockito.times(1)).doSomething("foo");
    }

    @Test
    public void annotatedWithSKFunctionInputAttributeIsBoundToInput() {
        class With2Inputs {
            @DefineSKFunction
            public String doSomething(
                    @SKFunctionInputAttribute(description = "") String anInput,
                    @SKFunctionParameters(name = "secondInput") String secondInput) {
                return "";
            }
        }
        With2Inputs skill = Mockito.spy(new With2Inputs());
        FunctionCollection skills =
                SkillImporter.importSkill(skill, "test", DefaultSkillCollection::new);
        ContextVariables variables = SKBuilders.variables().build();
        variables = variables.writableClone().appendToVariable("input", "foo");
        variables = variables.writableClone().appendToVariable("secondInput", "ignore");
        skills.getFunction("doSomething").invokeWithCustomInputAsync(variables, null, null).block();
        Mockito.verify(skill, Mockito.times(1)).doSomething("foo", "ignore");
    }

    @Test
    public void annotatedWithNonInputIsBound() {
        class With2InputParameters {
            @DefineSKFunction
            public String doSomething(
                    @SKFunctionParameters(name = "anInput") String anInput,
                    @SKFunctionParameters(name = "secondInput") String secondInput) {
                return "";
            }
        }
        With2InputParameters skill = Mockito.spy(new With2InputParameters());
        FunctionCollection skills =
                SkillImporter.importSkill(skill, "test", DefaultSkillCollection::new);
        ContextVariables variables = SKBuilders.variables().build();
        variables = variables.writableClone().appendToVariable("anInput", "foo");
        variables = variables.writableClone().appendToVariable("secondInput", "ignore");
        skills.getFunction("doSomething").invokeWithCustomInputAsync(variables, null, null).block();
        Mockito.verify(skill, Mockito.times(1)).doSomething("foo", "ignore");
    }

    @Test
    public void nonExistantVariableCreatesError() {
        class DoesNotExist {
            @DefineSKFunction
            public String doSomething(@SKFunctionParameters(name = "doesNotExist") String anInput) {
                return "";
            }
        }
        DoesNotExist skill = Mockito.spy(new DoesNotExist());
        FunctionCollection skills =
                SkillImporter.importSkill(skill, "test", DefaultSkillCollection::new);
        ContextVariables variables =
                SKBuilders.variables().build().writableClone().appendToVariable("input", "foo");
        Assertions.assertThrows(
                AIException.class,
                () -> {
                    skills.getFunction("doSomething")
                            .invokeWithCustomInputAsync(variables, null, null)
                            .block();
                });
        Mockito.verify(skill, Mockito.never()).doSomething("foo");
    }

    @Test
    public void noAnnotationCreatesError() {
        class AnnotationDoesNotExist {
            public String doSomething(String anInput) {
                return "";
            }
        }

        AnnotationDoesNotExist skill = Mockito.spy(new AnnotationDoesNotExist());
        Assertions.assertThrows(
                FunctionNotFound.class,
                () -> {
                    FunctionCollection skills =
                            SkillImporter.importSkill(skill, "test", DefaultSkillCollection::new);
                    skills.getFunction("doSomething").invokeAsync("foo");
                });
        Mockito.verify(skill, Mockito.never()).doSomething("foo");
    }

    @Test
    public void contextIsBound() {
        class WithContext {
            @DefineSKFunction
            public String doSomething(SKContext context) {
                return "";
            }
        }

        WithContext skill = Mockito.spy(new WithContext());
        FunctionCollection skills =
                SkillImporter.importSkill(skill, "test", DefaultSkillCollection::new);
        SKContext ignore = skills.getFunction("doSomething").invokeAsync("foo").block();
        Mockito.verify(skill, Mockito.only()).doSomething(Mockito.notNull());
    }

    @Test
    public void withMonoReturn() {
        class WithMono {
            @DefineSKFunction
            public Mono<String> doSomething() {
                return Mono.just("A-RESULT");
            }
        }

        WithMono skill = Mockito.spy(new WithMono());
        FunctionCollection skills =
                SkillImporter.importSkill(skill, "test", DefaultSkillCollection::new);
        SKContext result = skills.getFunction("doSomething").invokeAsync("foo").block();
        Assertions.assertEquals("A-RESULT", Objects.requireNonNull(result).getResult());
    }
}
