package com.microsoft.semantickernel.planner.handlebarsplanner;

import java.util.List;

import com.microsoft.semantickernel.Kernel;

import reactor.core.publisher.Mono;

public class HandlebarsPlanner {

    public static class HandlebarsPlannerConfiguration {
        public HandlebarsPlannerConfiguration() {}
        public List<String> getIncludedPlugins() { return null; }
        public HandlebarsPlannerConfiguration setIncludedPlugins(List<String> includedPlugins) { return this; }
        public List<String> getExcludedPlugins() { return null; }
        public HandlebarsPlannerConfiguration setExcludedPlugins(List<String> excludedPlugins) { return this; }
        public List<String> getIncludedFunctions() { return null; }
        public HandlebarsPlannerConfiguration setIncludedFunctions(List<String> includedFunctions) { return this; }
        public List<String> getExcludedFunctions() { return null; }
        public HandlebarsPlannerConfiguration setExcludedFunctions(List<String> excludedFunctions) { return this; }
        public HandlebarsPlan lastPlan() { return null; }
        public HandlebarsPlannerConfiguration setLastPlan(HandlebarsPlan lastPlan) { return this; }
        public String getLastError() { return null; }
        public HandlebarsPlannerConfiguration setLastError(String lastError) { return this; }
    }

    public HandlebarsPlanner(Kernel kernel, HandlebarsPlannerConfiguration configuration) {
        // TODO Auto-generated constructor stub
    }
    
    public Mono<HandlebarsPlan> createPlanAsync(String goal) {
        // TODO Auto-generated method stub
        return null;
    }
}
