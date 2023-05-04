// Copyright (c) Microsoft. All rights reserved.

import { AdditionalApiProperties, AuthHeaderTags } from '../../redux/features/plugins/PluginsState';
import { BaseService } from '../services/BaseService';
import { IAsk, IAskVariables } from './model/Ask';
import { IAskResult } from './model/AskResult';

export class SemanticKernel extends BaseService {
    public invokeAsync = async (
        ask: IAsk,
        skillName: string,
        functionName: string,
        accessToken: string,
        enabledPlugins?: {
            headerTag: AuthHeaderTags;
            authData: string;
            apiProperties?: AdditionalApiProperties;
        }[],
    ): Promise<IAskResult> => {
        // If skill requires any additional api properties, append to context
        if (enabledPlugins && enabledPlugins.length > 0) {
            const openApiSkillVariables: IAskVariables[] = [];

            for (var idx in enabledPlugins) {
                var plugin = enabledPlugins[idx];

                if (plugin.apiProperties) {
                    const apiProperties = plugin.apiProperties;

                    for (var property in apiProperties) {
                        const propertyDetails = apiProperties[property];

                        if (propertyDetails.required && !propertyDetails.value) {
                            throw new Error(`Missing required property ${property} for ${plugin} skill.`);
                        }

                        if (propertyDetails.value) {
                            openApiSkillVariables.push({
                                key: `${property}`,
                                value: apiProperties[property].value!,
                            });
                        }
                    }
                }
            }

            ask.variables = ask.variables ? ask.variables.concat(openApiSkillVariables) : openApiSkillVariables;
        }

        const result = await this.getResponseAsync<IAskResult>(
            {
                commandPath: `skills/${skillName}/functions/${functionName}/invoke`,
                method: 'POST',
                body: ask,
            },
            accessToken,
            enabledPlugins,
        );

        return result;
    };
}
