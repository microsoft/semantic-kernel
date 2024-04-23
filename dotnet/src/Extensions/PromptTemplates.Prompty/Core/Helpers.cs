// Copyright (c) Microsoft. All rights reserved.

using YamlDotNet.Serialization;

namespace Microsoft.SemanticKernel.Experimental.Prompty.Core;

internal static class Helpers
{
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
            if (promptyFrontMatter.Tags != null)
            {
                prompty.Tags = promptyFrontMatter.Tags;
            }
            if (promptyFrontMatter.Authors != null)
            {
                prompty.Authors = promptyFrontMatter.Authors;
            }
            if (promptyFrontMatter.Inputs != null)
            {
                prompty.Inputs = promptyFrontMatter.Inputs;
            }
            if (promptyFrontMatter.Model != null)
            {
                prompty.Model.Api = promptyFrontMatter.Model.Api;
                prompty.Model.ModelConfiguration = promptyFrontMatter.Model.ModelConfiguration;
                prompty.Model.Parameters = promptyFrontMatter.Model.Parameters;
                prompty.Model.Response = promptyFrontMatter.Model.Response;

            }
        }

        return prompty;
    }

}
