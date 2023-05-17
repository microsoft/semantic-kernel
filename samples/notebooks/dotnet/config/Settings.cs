// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.IO;
using System.Text.Json;
using System.Threading.Tasks;
using Microsoft.DotNet.Interactive;
using InteractiveKernel = Microsoft.DotNet.Interactive.Kernel;

// ReSharper disable InconsistentNaming

public static class Settings
{
    private const string DefaultConfigFile = "config/settings.json";
    private const string TypeKey = "type";
    private const string CompletionModelKey = "model";
    private const string EmbeddingModelKey = "embeddingModel";
    private const string EndpointKey = "endpoint";
    private const string SecretKey = "apikey";
    private const string OrgKey = "org";
    private const bool StoreConfigOnFile = true;

    // Prompt user for Azure Endpoint URL
    public static async Task<string> AskAzureEndpoint(bool _useAzureOpenAI = true, string configFile = DefaultConfigFile)
    {
        var (useAzureOpenAI, model, azureEndpoint, apiKey, orgId, embeddingModel) = ReadSettings(_useAzureOpenAI, configFile);

        // If needed prompt user for Azure endpoint
        if (useAzureOpenAI && string.IsNullOrWhiteSpace(azureEndpoint))
        {
            azureEndpoint = await InteractiveKernel.GetInputAsync("Please enter your Azure OpenAI endpoint");
        }

        WriteSettings(configFile, useAzureOpenAI, model, azureEndpoint, apiKey, orgId, embeddingModel);

        // Print report
        if (useAzureOpenAI)
        {
            Console.WriteLine("Settings: " + (string.IsNullOrWhiteSpace(azureEndpoint)
                ? "ERROR: Azure OpenAI endpoint is empty"
                : $"OK: Azure OpenAI endpoint configured [{configFile}]"));
        }

        return azureEndpoint;
    }

    // Prompt user for OpenAI model name / Azure OpenAI deployment name
    public static async Task<string> AskModel(bool _useAzureOpenAI = true, string configFile = DefaultConfigFile)
    {
        var (useAzureOpenAI, model, azureEndpoint, apiKey, orgId, embeddingModel) = ReadSettings(_useAzureOpenAI, configFile);

        // If needed prompt user for model name / deployment name
        if (string.IsNullOrWhiteSpace(model))
        {
            if (useAzureOpenAI)
            {
                model = await InteractiveKernel.GetInputAsync("Please enter your Azure OpenAI deployment name");
            }
            else
            {
                // Use the best model by default, and reduce the setup friction, particularly in VS Studio.
                model = "text-davinci-003";
            }
        }

        WriteSettings(configFile, useAzureOpenAI, model, azureEndpoint, apiKey, orgId, embeddingModel);

        // Print report
        if (useAzureOpenAI)
        {
            Console.WriteLine("Settings: " + (string.IsNullOrWhiteSpace(model)
                ? "ERROR: deployment name is empty"
                : $"OK: deployment name configured [{configFile}]"));
        }
        else
        {
            Console.WriteLine("Settings: " + (string.IsNullOrWhiteSpace(model)
                ? "ERROR: model name is empty"
                : $"OK: AI model configured [{configFile}]"));
        }

        return model;
    }

    // Prompt user for API Key
    public static async Task<string> AskApiKey(bool _useAzureOpenAI = true, string configFile = DefaultConfigFile)
    {
        var (useAzureOpenAI, model, azureEndpoint, apiKey, orgId, embeddingModel) = ReadSettings(_useAzureOpenAI, configFile);

        // If needed prompt user for API key
        if (string.IsNullOrWhiteSpace(apiKey))
        {
            if (useAzureOpenAI)
            {
                apiKey = await InteractiveKernel.GetPasswordAsync("Please enter your Azure OpenAI API key");
                orgId = "";
            }
            else
            {
                apiKey = await InteractiveKernel.GetPasswordAsync("Please enter your OpenAI API key");
            }
        }

        WriteSettings(configFile, useAzureOpenAI, model, azureEndpoint, apiKey, orgId, embeddingModel);

        // Print report
        Console.WriteLine("Settings: " + (string.IsNullOrWhiteSpace(apiKey)
            ? "ERROR: API key is empty"
            : $"OK: API key configured [{configFile}]"));

        return apiKey;
    }

    // Prompt user for embedding model name
    public static async Task<string> AskEmbeddingModel(bool _useAzureOpenAI = true, string configFile = DefaultConfigFile)
    {
        var (useAzureOpenAI, model, azureEndpoint, apiKey, orgId, embeddingModel) = ReadSettings(_useAzureOpenAI, configFile);

        // If needed prompt user for embedding model name
        if (string.IsNullOrWhiteSpace(embeddingModel))
        {
            if (useAzureOpenAI)
            {
                embeddingModel = await InteractiveKernel.GetInputAsync("Please enter your Azure OpenAI embedding model deployment name");
            }
            else
            {
                // Use the best model by default, and reduce the setup friction, particularly in VS Studio.
                embeddingModel = "text-embedding-ada-002";
            }
        }

        WriteSettings(configFile, useAzureOpenAI, model, azureEndpoint, apiKey, orgId, embeddingModel);

        // Print report
        if (useAzureOpenAI)
        {
            Console.WriteLine("Settings: " + (string.IsNullOrWhiteSpace(embeddingModel)
                ? "ERROR: deployment name of embedding model is empty"
                : $"OK: deployment name configured [{configFile}]"));
        }
        else
        {
            Console.WriteLine("Settings: " + (string.IsNullOrWhiteSpace(embeddingModel)
                ? "ERROR: embeddingModel name is empty"
                : $"OK: AI model configured [{configFile}]"));
        }
        return embeddingModel;
    }

    // Prompt user for OpenAI Organization Id
    public static async Task<string> AskOrg(bool _useAzureOpenAI = true, string configFile = DefaultConfigFile)
    {
        var (useAzureOpenAI, model, azureEndpoint, apiKey, orgId, embeddingModel) = ReadSettings(_useAzureOpenAI, configFile);

        // If needed prompt user for OpenAI Org Id
        if (!useAzureOpenAI && string.IsNullOrWhiteSpace(orgId))
        {
            orgId = await InteractiveKernel.GetInputAsync("Please enter your OpenAI Organization Id (enter 'NONE' to skip)");
        }

        WriteSettings(configFile, useAzureOpenAI, model, azureEndpoint, apiKey, orgId, embeddingModel);

        return orgId;
    }

    // Load settings from file
    public static (bool useAzureOpenAI, string model, string azureEndpoint, string apiKey, string orgId)
        LoadFromFile(string configFile = DefaultConfigFile)
    {
        (bool useAzureOpenAI, string model, string azureEndpoint, string apiKey, string orgId, string embeddingModel) = LoadFromFileInternal(configFile);
        return (useAzureOpenAI, model, azureEndpoint, apiKey, orgId);
    }

    // Load settings from file
    public static (bool useAzureOpenAI, string model, string azureEndpoint, string apiKey, string orgId, string embeddingModel)
        LoadFromFileWithEmbeddingModel(string configFile = DefaultConfigFile)
    {
        return LoadFromFileInternal(configFile);
    }

    private static (bool useAzureOpenAI, string model, string azureEndpoint, string apiKey, string orgId, string embeddingModel)
        LoadFromFileInternal(string configFile)
    {
        if (!File.Exists(DefaultConfigFile))
        {
            Console.WriteLine("Configuration not found: " + DefaultConfigFile);
            Console.WriteLine("\nPlease run the Setup Notebook (0-AI-settings.ipynb) to configure your AI backend first.\n");
            throw new Exception("Configuration not found, please setup the notebooks first using notebook 0-AI-settings.pynb");
        }

        try
        {
            var config = JsonSerializer.Deserialize<Dictionary<string, string>>(File.ReadAllText(DefaultConfigFile));
            bool useAzureOpenAI = config[TypeKey] == "azure";
            string model = config[CompletionModelKey];
            string azureEndpoint = config[EndpointKey];
            string apiKey = config[SecretKey];
            string orgId = config[OrgKey];
            if (orgId == "none") { orgId = ""; }
            if(!config.TryGetValue(EmbeddingModelKey, out string embeddingModel))
            {
                embeddingModel = string.Empty;
            }

            return (useAzureOpenAI, model, azureEndpoint, apiKey, orgId, embeddingModel);
        }
        catch (Exception e)
        {
            Console.WriteLine("Something went wrong: " + e.Message);
            return (true, "", "", "", "", "");
        }
    }

    // Delete settings file
    public static void Reset(string configFile = DefaultConfigFile)
    {
        if (!File.Exists(configFile)) { return; }

        try
        {
            File.Delete(configFile);
            Console.WriteLine("Settings deleted. Run the notebook again to configure your AI backend.");
        }
        catch (Exception e)
        {
            Console.WriteLine("Something went wrong: " + e.Message);
        }
    }

    // Read and return settings from file
    private static (bool useAzureOpenAI, string model, string azureEndpoint, string apiKey, string orgId, string embeddingModel)
        ReadSettings(bool _useAzureOpenAI, string configFile)
    {
        // Save the preference set in the notebook
        bool useAzureOpenAI = _useAzureOpenAI;
        string model = "";
        string azureEndpoint = "";
        string apiKey = "";
        string orgId = "";
        string embeddingModel = "";

        try
        {
            if (File.Exists(configFile))
            {
                (useAzureOpenAI, model, azureEndpoint, apiKey, orgId, embeddingModel) = LoadFromFileInternal(configFile);
            }
        }
        catch (Exception e)
        {
            Console.WriteLine("Something went wrong: " + e.Message);
        }

        // If the preference in the notebook is different from the value on file, then reset
        if (useAzureOpenAI != _useAzureOpenAI)
        {
            Reset(configFile);
            useAzureOpenAI = _useAzureOpenAI;
            model = "";
            azureEndpoint = "";
            apiKey = "";
            orgId = "";
        }

        return (useAzureOpenAI, model, azureEndpoint, apiKey, orgId, embeddingModel);
    }

    // Write settings to file
    private static void WriteSettings(
        string configFile, bool useAzureOpenAI, string completionModel, string azureEndpoint, string apiKey, string orgId, string embeddingModel)
    {
        try
        {
            if (StoreConfigOnFile)
            {
                var data = new Dictionary<string, string>
                {
                    { TypeKey, useAzureOpenAI ? "azure" : "openai" },
                    { CompletionModelKey, completionModel },
                    { EndpointKey, azureEndpoint },
                    { SecretKey, apiKey },
                    { OrgKey, orgId },
                    { EmbeddingModelKey, embeddingModel },
                };

                var options = new JsonSerializerOptions { WriteIndented = true };
                File.WriteAllText(configFile, JsonSerializer.Serialize(data, options));
            }
        }
        catch (Exception e)
        {
            Console.WriteLine("Something went wrong: " + e.Message);
        }

        // If asked then delete the credentials stored on disk
        if (!StoreConfigOnFile && File.Exists(configFile))
        {
            try
            {
                File.Delete(configFile);
            }
            catch (Exception e)
            {
                Console.WriteLine("Something went wrong: " + e.Message);
            }
        }
    }
}
