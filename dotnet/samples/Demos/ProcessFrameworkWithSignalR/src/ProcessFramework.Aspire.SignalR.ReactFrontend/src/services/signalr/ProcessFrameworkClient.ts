import axios from 'axios';

const API_BASE_URL = 'http://localhost:5125'; // Replace with actual backend endpoint

export class ProcessFrameworkHttpClient {
    async generateDocumentation(request: {
        processId: string;
        content: string;
        title: string;
        assistantMessage: string;
    }): Promise<void> {
        try {
            await axios.post(`${API_BASE_URL}/api/generate-doc`, request);
        } catch (error) {
            console.error('[HTTP] Error publishing documentation', error);
            throw error;
        }
    }

    async requestDocumentationReview(request: {
        processId: string;
        documentationApproved: boolean;
        reason: string;
    }): Promise<void> {
        try {
            await axios.post(`${API_BASE_URL}/api/reviewed-doc`, request);
        } catch (error) {
            console.error('[HTTP] Error requesting documentation review', error);
            throw error;
        }
    }
}