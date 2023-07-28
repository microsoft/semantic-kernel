import { BaseService } from './BaseService';

type IContentModerationResult = Record<string, { category: string; riskLevel: number }>;

export class ContentModerationService extends BaseService {
    public analyzeImageAsync = async (base64Image: string, accessToken: string): Promise<IContentModerationResult> => {
        return await this.getResponseAsync<IContentModerationResult>(
            {
                commandPath: 'contentModerator/image',
                method: 'POST',
                body: base64Image,
            },
            accessToken,
        );
    };

    public getContentModerationStatusAsync = async (accessToken: string): Promise<boolean> => {
        return await this.getResponseAsync<boolean>(
            {
                commandPath: 'contentModerator/status',
                method: 'GET',
            },
            accessToken,
        );
    };
}
