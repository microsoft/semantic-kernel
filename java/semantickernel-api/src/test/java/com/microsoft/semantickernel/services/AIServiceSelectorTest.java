package com.microsoft.semantickernel.services;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertNull;
import org.junit.jupiter.api.Test;

import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.orchestration.PromptExecutionSettings;
import com.microsoft.semantickernel.semanticfunctions.KernelFunction;
import com.microsoft.semantickernel.semanticfunctions.KernelFunctionArguments;
import com.microsoft.semantickernel.semanticfunctions.PromptTemplateConfig;

public class AIServiceSelectorTest {
    
    @Test
    public void testReturnsRequestedType() {

        AIService aService = new AIService() {
            @Override
            public String getModelId() {
                return "a-model";
            }

            @Override
            public String getServiceId() {
                return "a-service";
            }
        };
        
        AIService bService = new AIService() {
            @Override
            public String getModelId() {
                return "b-model";
            }

            @Override
            public String getServiceId() {
                return "b-service";
            }
        };

        AIServiceSelection<?> expected = new AIServiceSelection<>(aService, null);

        Kernel kernel = Kernel.builder()
            .withAIService((Class<AIService>)aService.getClass(), aService)
            .withAIService((Class<AIService>)bService.getClass(), bService)
            .build();

        AIServiceSelector selector = kernel.getServiceSelector();

        AIServiceSelection<?> actual = selector.trySelectAIService(aService.getClass(), null, null);
        assertNotNull(actual);
        assertNull(actual.getSettings());
        assertEquals(expected.getService(), actual.getService());        
    }

    // used to test that the selector returns the requested super type
    interface TestService extends AIService{}

    @Test
    public void testReturnsRequestedSuperType() {

        AIService aService = new TestService() {
            @Override
            public String getModelId() {
                return "a-model";
            }

            @Override
            public String getServiceId() {
                return "a-service";
            }
        };
        
        AIService bService = new AIService() {
            @Override
            public String getModelId() {
                return "b-model";
            }

            @Override
            public String getServiceId() {
                return "b-service";
            }
        };

        AIServiceSelection<?> expected = new AIServiceSelection<>(aService, null);
       
        Kernel kernel = Kernel.builder()
            .withAIService((Class<AIService>)aService.getClass(), aService)
            .withAIService((Class<AIService>)bService.getClass(), bService)
            .build();
        
        AIServiceSelector selector = kernel.getServiceSelector();

        AIServiceSelection<?> actual = selector.trySelectAIService(TestService.class, null, null);
        assertNotNull(actual);
        assertNull(actual.getSettings());
        assertEquals(expected.getService(), actual.getService());        
    }

    @Test
    public void testReturnsUsingKernelFunction() {

        AIService aService = new AIService() {
            @Override
            public String getModelId() {
                return "a-model";
            }

            @Override
            public String getServiceId() {
                return "a-service";
            }
        };
        
        AIService bService = new AIService() {
            @Override
            public String getModelId() {
                return "b-model";
            }

            @Override
            public String getServiceId() {
                return "b-service";
            }
        };

        PromptExecutionSettings settings = PromptExecutionSettings.builder().withServiceId("a-service").build();
        AIServiceSelection<?> expected = new AIServiceSelection<>(aService, settings);

        PromptTemplateConfig promptTemplateConfig = PromptTemplateConfig.defaultTemplateBuilder()
            .withTemplate("{{aFunction 'input'}}")
            .build();

        KernelFunction<?> function = KernelFunction.createFromPrompt(promptTemplateConfig)
            .withDefaultExecutionSettings(settings)
            .build();
       
        Kernel kernel = Kernel.builder()
            .withAIService((Class<AIService>)aService.getClass(), aService)
            .withAIService((Class<AIService>)bService.getClass(), bService)
            .build();
        
        AIServiceSelector selector = kernel.getServiceSelector();

        // AIService could match aService or bService. Selector should use function to refine the selection. 
        AIServiceSelection<?> actual = selector.trySelectAIService(AIService.class, function, null);
        assertNotNull(actual);
        assertEquals(expected.getSettings(), actual.getSettings());
        assertEquals(expected.getService(), actual.getService());        

    }


    @Test
    public void testReturnsUsingKernelFunctionArguments() {

        AIService aService = new AIService() {
            @Override
            public String getModelId() {
                return "a-model";
            }

            @Override
            public String getServiceId() {
                return "a-service";
            }
        };
        
        AIService bService = new AIService() {
            @Override
            public String getModelId() {
                return "b-model";
            }

            @Override
            public String getServiceId() {
                return "b-service";
            }
        };

        AIServiceSelection<?> expected = new AIServiceSelection<>(aService, null);

        KernelFunctionArguments arguments = KernelFunctionArguments.builder().build();
       
        Kernel kernel = Kernel.builder()
            .withAIService((Class<AIService>)aService.getClass(), aService)
            .withAIService((Class<AIService>)bService.getClass(), bService)
            .build();
        
        AIServiceSelector selector = kernel.getServiceSelector();

        // arguments are not used in the current implementation
        // Could select either aService or bService.
        AIServiceSelection<?> actual = selector.trySelectAIService(AIService.class, null, arguments);
        assertNotNull(actual);
        assertNull(actual.getSettings());
        assertNotNull(expected.getService());        
    }

}
