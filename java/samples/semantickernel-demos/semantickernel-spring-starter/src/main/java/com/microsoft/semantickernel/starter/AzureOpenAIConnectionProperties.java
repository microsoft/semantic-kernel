package com.microsoft.semantickernel.starter;

import org.springframework.boot.context.properties.ConfigurationProperties;

@ConfigurationProperties(AzureOpenAIConnectionProperties.CONFIG_PREFIX)
public class AzureOpenAIConnectionProperties {

    public static final String CONFIG_PREFIX = "client.azureopenai";

    /**
     * Azure OpenAI API endpoint.From the Azure AI OpenAI at 'Resource Management' select `Keys and
     * Endpoint` and find it on the right side.
     */
    private String endpoint;

    /**
     * Azure OpenAI API key.From the Azure AI OpenAI at 'Resource Management' select `Keys and
     * Endpoint` and find it on the right side.
     */
    private String key;

    /**
     * Azure OpenAI API deployment name specified in the Azure Open AI studio under Management ->
     * Deployments.
     */
    private String deploymentName;

    public String getEndpoint() {
        return endpoint;
    }

    public String getKey() {
        return key;
    }

    public void setEndpoint(String endpoint) {
        this.endpoint = endpoint;
    }

    public void setKey(String key) {
        this.key = key;
    }

    public String getDeploymentName() {
        return deploymentName;
    }

    public void setDeploymentName(String deploymentName) {
        this.deploymentName = deploymentName;
    }
}
