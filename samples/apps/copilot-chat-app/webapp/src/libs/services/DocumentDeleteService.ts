// Copyright (c) Microsoft. All rights reserved.

import { BaseService } from './BaseService';

export class DocumentDeleteService extends BaseService {
    public deleteDocumentAsync = async (
        userId: string,
        chatId: string,
        documentId: string,
        accessToken: string,
    ) => {
        const formData = new FormData();
        formData.append('userId', userId);
        formData.append('chatId', chatId);
        formData.append('documentId', documentId);

        return await this.getResponseAsync<string>(
            {
                commandPath: 'deleteDocument',
                method: 'POST',
                body: formData,
            },
            accessToken,
        );
    };
}
