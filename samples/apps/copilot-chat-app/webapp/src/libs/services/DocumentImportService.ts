// Copyright (c) Microsoft. All rights reserved.

import { IChatMessage } from '../models/ChatMessage';
import { BaseService } from './BaseService';

export class DocumentImportService extends BaseService {
    public importDocumentAsync = async (
        userId: string,
        userName: string,
        chatId: string,
        document: File,
        accessToken: string,
    ) => {
        const formData = new FormData();
        formData.append('userId', userId);
        formData.append('userName', userName);
        formData.append('chatId', chatId);
        formData.append('documentScope', 'Chat');
        formData.append('formFile', document);

        return await this.getResponseAsync<IChatMessage>(
            {
                commandPath: 'importDocument',
                method: 'POST',
                body: formData,
            },
            accessToken,
        );
    };
}
