// Copyright (c) Microsoft. All rights reserved.

import { AdditionalApiRequirements, AuthHeaderTags } from '../../redux/features/plugins/PluginsState';
import { BaseService } from '../services/BaseService';
import { IAsk } from './model/Ask';
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
