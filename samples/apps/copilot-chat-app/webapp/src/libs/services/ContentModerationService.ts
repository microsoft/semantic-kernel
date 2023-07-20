import { BaseService } from './BaseService';

type IContentModerationResult = Record<string, { category: string; riskLevel: number }>;

export class ContentModerationService extends BaseService {
    public analyzeImageAsync = async (base64Image: string, accessToken: string): Promise<IContentModerationResult> => {
        const result = await this.getResponseAsync<IContentModerationResult>(
            {
                commandPath: 'contentModerator/image',
                method: 'POST',
                body: base64Image,
            },
            accessToken,
        );

        return result;
    };

    public getContentModerationStatusAsync = async (accessToken: string): Promise<boolean> => {
        const result = await this.getResponseAsync<boolean>(
            {
                commandPath: 'contentModerator/status',
                method: 'GET',
            },
            accessToken,
        );
        return result;
    };
}
