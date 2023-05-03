// Copyright (c) Microsoft. All rights reserved.

import { AdditionalApiRequirements, AuthHeaderTags } from '../../redux/features/plugins/PluginsState';
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
            apiRequirements?: AdditionalApiRequirements;
        }[],
    ): Promise<IAskResult> => {
        // If skill requires any additional api requirements, append to context
        if (enabledPlugins && enabledPlugins.length > 0) {
            const openApiSkillVariables: IAskVariables[] = [];

            for (var idx in enabledPlugins) {
                var plugin = enabledPlugins[idx];

                if (plugin.apiRequirements) {
                    const apiRequirments = plugin.apiRequirements;
                    for (var property in apiRequirments) {
                        openApiSkillVariables.push({
                            key: property,
                            value: apiRequirments[property].value!,
                        });
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
