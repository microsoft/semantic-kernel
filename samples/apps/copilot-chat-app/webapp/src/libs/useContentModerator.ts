// Copyright (c) Microsoft. All rights reserved.

import { useMsal } from '@azure/msal-react';
import { useAppDispatch } from '../redux/app/hooks';
import { FeatureKeys } from '../redux/features/app/AppState';
import { addAlert, setFeatureFlag } from '../redux/features/app/appSlice';
import { AuthHelper } from './auth/AuthHelper';
import { AlertType } from './models/AlertType';
import { ContentModerationService } from './services/ContentModerationService';

const riskThreshold = 4;

export const useContentModerator = () => {
    const dispatch = useAppDispatch();
    const { inProgress, instance } = useMsal();

    const contentModeratorService = new ContentModerationService(process.env.REACT_APP_BACKEND_URI as string);

    const analyzeImage = async (base64Image: string) => {
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
                const errorMessage = `Detect undesirable image content with potential risk: ${violations.join(', ')}`;
                dispatch(addAlert({ message: errorMessage, type: AlertType.Error }));
            }
        } catch (error) {
            const errorMessage = 'Unable to analyze image';
            dispatch(addAlert({ message: errorMessage, type: AlertType.Error }));
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
