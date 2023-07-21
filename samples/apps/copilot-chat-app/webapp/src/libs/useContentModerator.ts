// Copyright (c) Microsoft. All rights reserved.

import { useMsal } from '@azure/msal-react';
import { useAppDispatch, useAppSelector } from '../redux/app/hooks';
import { RootState } from '../redux/app/store';
import { FeatureKeys } from '../redux/features/app/AppState';
import { addAlert, toggleFeatureState } from '../redux/features/app/appSlice';
import { AuthHelper } from './auth/AuthHelper';
import { AlertType } from './models/AlertType';
import { ContentModerationService } from './services/ContentModerationService';

// Controls how the content moderation API categorizes the input content based on the level of offensive or unwanted elements
const riskThreshold = 4;

export const useContentModerator = () => {
    const dispatch = useAppDispatch();
    const { inProgress, instance } = useMsal();
    const { features } = useAppSelector((state: RootState) => state.app);

    const contentModeratorService = new ContentModerationService(process.env.REACT_APP_BACKEND_URI as string);

    const analyzeImage = async (base64Image: string) => {
        const VIOLATIONS_FLAG = 'ContainsViolations';
        try {
            // remove image prefix
            const image = base64Image.replace(/data:image\/(png|jpeg);base64,/, '');

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
        } catch (e) {
            const ANALYSIS_FAILURE_ERROR_MESSAGE = 'Unable to analyze image';
            const error = e as Error;
            const SERVICE_DISABLED_MESSAGE = 'Content Moderation is currently disabled.';

            if (error.message.includes(SERVICE_DISABLED_MESSAGE)) {
                dispatch(
                    toggleFeatureState({ feature: FeatureKeys.AzureContentSafety, deactivate: true, enable: false }),
                );

                if (features[FeatureKeys.AzureContentSafety].enabled) {
                    dispatch(
                        addAlert({
                            type: AlertType.Warning,
                            message: `${ANALYSIS_FAILURE_ERROR_MESSAGE}: ${SERVICE_DISABLED_MESSAGE} Please contact your admin to enable.`,
                        }),
                    );
                }
            } else {
                if (error.cause === VIOLATIONS_FLAG) throw error;
                throw new Error(ANALYSIS_FAILURE_ERROR_MESSAGE);
            }
        }
    };

    const getContentModerationStatus = async () => {
        try {
            const result = await contentModeratorService.getContentModerationStatusAsync(
                await AuthHelper.getSKaaSAccessToken(instance, inProgress),
            );

            if (result) {
                dispatch(
                    toggleFeatureState({ feature: FeatureKeys.AzureContentSafety, deactivate: false, enable: true }),
                );
            }
        } catch (error) {
            /* Do nothing, leave feature disabled */
        }
    };

    return {
        analyzeImage,
        getContentModerationStatus,
    };
};
