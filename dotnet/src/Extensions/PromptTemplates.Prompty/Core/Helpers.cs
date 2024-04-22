// Copyright (c) Microsoft. All rights reserved.

using YamlDotNet.Serialization;

namespace Microsoft.SemanticKernel.Experimental.Prompty.Core;

internal static class Helpers
{
    // This is to load the appsettings.json file config 
    // These are the base configuration settings for the prompty file
    // These can be overriden by the prompty file, or the execute method
    public static Prompty GetPromptyModelConfigFromSettings(Prompty prompty)
    {
        // get variables from section and assign to promptymodelconfig
        var promptyModelConfig = new PromptyModelConfig();
        prompty.Model = promptyModelConfig;

        return prompty;
    }

    public static Prompty ParsePromptyYamlFile(Prompty prompty, string promptyFrontMatterYaml)
    {
        // desearialize yaml front matter
        // TODO: check yaml to see what props are missing? update to include template type, update so invoker descides based on prop
        var deserializer = new DeserializerBuilder().Build();
        var promptyFrontMatter = deserializer.Deserialize<Prompty>(promptyFrontMatterYaml);

        // override props if they are not null from file
        if (promptyFrontMatter.Name != null)
        {
            // check each prop and if not null override
            if (promptyFrontMatter.Name != null)
            {
                prompty.Name = promptyFrontMatter.Name;
            }
            if (promptyFrontMatter.Description != null)
            {
                prompty.Description = promptyFrontMatter.Description;
            }
            if (promptyFrontMatter.Tags is not null)
            {
                prompty.Tags = promptyFrontMatter.Tags;
            }
            if (promptyFrontMatter.Authors is not null)
            {
                prompty.Authors = promptyFrontMatter.Authors;
            }
            if (promptyFrontMatter.Inputs != null)
            {
                prompty.Inputs = promptyFrontMatter.Inputs;
            }
            if (promptyFrontMatter.Parameters != null)
            {
                prompty.Parameters = promptyFrontMatter.Parameters;
            }
            if (promptyFrontMatter.modelApiType != null)
            {
                //parse type to enum
                prompty.modelApiType = promptyFrontMatter.modelApiType;
            }
            if (promptyFrontMatter.Model != null)
            {
                //check for each prop of promptymodelconfig and override if not null
                if (promptyFrontMatter.Model.ModelType != null)
                {
                    //parse type to enum
                    prompty.Model.ModelType = promptyFrontMatter.Model.ModelType;
                }
                if (promptyFrontMatter.Model.ApiVersion != null)
                {
                    prompty.Model.ApiVersion = promptyFrontMatter.Model.ApiVersion;
                }
                if (promptyFrontMatter.Model.AzureEndpoint != null)
                {
                    prompty.Model.AzureEndpoint = promptyFrontMatter.Model.AzureEndpoint;
                }
                if (promptyFrontMatter.Model.AzureDeployment != null)
                {
                    prompty.Model.AzureDeployment = promptyFrontMatter.Model.AzureDeployment;
                }
                if (promptyFrontMatter.Model.ApiKey != null)
                {
                    prompty.Model.ApiKey = promptyFrontMatter.Model.ApiKey;
                }
            }
        }

        return prompty;
    }

}
