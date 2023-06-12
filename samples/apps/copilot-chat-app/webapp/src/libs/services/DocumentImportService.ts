// Copyright (c) Microsoft. All rights reserved.

import { BaseService } from './BaseService';

export interface DocumentImportResponse {
    name: string;
    size: number;
}

export class DocumentImportService extends BaseService {
    public importDocumentAsync = async (userId: string, chatId: string, document: File, accessToken: string) => {
        const formData = new FormData();
        formData.append('userId', userId);
        formData.append('chatId', chatId);
        formData.append('documentScope', 'Chat');
        formData.append('formFile', document);

        return await this.getResponseAsync<DocumentImportResponse>(
            {
                commandPath: 'importDocument',
                method: 'POST',
                body: formData,
            },
            accessToken,
        );
    };
}
