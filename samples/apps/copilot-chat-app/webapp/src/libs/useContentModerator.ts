// Copyright (c) Microsoft. All rights reserved.

import { useMsal } from '@azure/msal-react';
import { useAppDispatch } from '../redux/app/hooks';
import { FeatureKeys } from '../redux/features/app/AppState';
import { setFeatureFlag } from '../redux/features/app/appSlice';
import { AuthHelper } from './auth/AuthHelper';
import { ContentModerationService } from './services/ContentModerationService';

const riskThreshold = 4;

export const useContentModerator = () => {
    const dispatch = useAppDispatch();
    const { inProgress, instance } = useMsal();

    const contentModeratorService = new ContentModerationService(process.env.REACT_APP_BACKEND_URI as string);

    const analyzeImage = async (base64Image: string) => {
        const VIOLATIONS_FLAG = 'ContainsViolations';
        try {
            // remove image prefix
            const image = base64Image.replace('data:image/png;base64,', '').replace('data:image/jpeg;base64,', '');

            const result = await contentModeratorService.analyzeImageAsync(
                image,
                await AuthHelper.getSKaaSAccessToken(instance, inProgress),
            );

            const violations: string[] = [];
            Object.keys(result).forEach((key) => {
                if (result[key].riskLevel > riskThreshold) {
                    violations.push(result[key].category);
                }
            });

            if (violations.length > 0) {
                throw new Error(`Detected undesirable image content with potential risk: ${violations.join(', ')}`, {
                    cause: VIOLATIONS_FLAG,
                });
            }
        } catch (error) {
            if ((error as Error).cause === VIOLATIONS_FLAG) throw error;
            throw new Error('Unable to analyze image');
        }
    };

    const getContentModerationStatus = async () => {
        try {
            const result = await contentModeratorService.getContentModerationStatusAsync(
                await AuthHelper.getSKaaSAccessToken(instance, inProgress),
            );

            if (result) {
                dispatch(setFeatureFlag(FeatureKeys.AzureContentSafety));
            }
        } catch (error) {
            /* empty */
        }
    };

    return {
        analyzeImage,
        getContentModerationStatus,
    };
};
