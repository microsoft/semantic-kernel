/**
 * Copyright (c) Microsoft Corporation. All rights reserved.
 * Licensed under the MIT License.
 */

import { Verify } from '../../../diagnostics';
import { ILogger } from '../../../utils/logger';
import { ICompleteRequestSettings } from '../../completeRequestSettings';
import { ITextCompletionClient } from '../../iTextCompletionClient';
import { AzureOpenAIClientAbstract } from '../clients';

export class AzureTextCompletion extends AzureOpenAIClientAbstract implements ITextCompletionClient {
    private deploymentName: string;
    private apiKey: string;
    private apiVersion: string;
    private apiType: string;

    constructor(
        deploymentName: string,
        endpoint: string,
        apiKey: string,
        apiVersion: string = '2022-12-01',
        log?: ILogger,
        adAuth = false
    ) {
        super(log);

        Verify.notEmpty(deploymentName, 'The Azure Deployment name cannot be empty');
        Verify.notEmpty(endpoint, 'The Azure endpoint cannot be empty');
        Verify.startsWith(endpoint, 'https://', 'The Azure endpoint cannot be empty');
        Verify.notEmpty(apiKey, 'The Azure API key cannot be empty');

        this.deploymentName = deploymentName;
        this.endpoint = endpoint;
        this.apiKey = apiKey;
        this.apiVersion = apiVersion;
        this.apiType = adAuth ? 'azure_ad' : 'azure';
    }

    public async completeAsync(text: string, requestSettings: ICompleteRequestSettings): Promise<string> {
        // TODO
        return '';
    }
}
