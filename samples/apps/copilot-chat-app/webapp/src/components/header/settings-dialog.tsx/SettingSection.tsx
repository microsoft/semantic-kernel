import { Divider, Switch } from '@fluentui/react-components';
import { useCallback } from 'react';
import { useAppDispatch, useAppSelector } from '../../../redux/app/hooks';
import { RootState } from '../../../redux/app/store';
import { FeatureKeys, Setting } from '../../../redux/features/app/AppState';
import { setFeatureFlag } from '../../../redux/features/app/appSlice';

interface ISettingsSectionProps {
    setting: Setting;
}

export const SettingSection: React.FC<ISettingsSectionProps> = ({ setting }) => {
    const { features } = useAppSelector((state: RootState) => state.app);
    const dispatch = useAppDispatch();

    const onFeatureChange = useCallback(
        (featureKey: FeatureKeys) => {
            dispatch(setFeatureFlag(featureKey));
        },
        [dispatch],
    );

    const disableExperimentalFeatures =
        setting.title === 'Experimental' && features[FeatureKeys.SimplifiedExperience].enabled;

    return (
        <>
            <h3>{setting.title}</h3>
            {setting.description && <p>{setting.description}</p>}
            <div style={{ display: 'flex', flexDirection: `${setting.stackVertically ? 'column' : 'row'}` }}>
                {setting.features.map((key) => {
                    const feature = features[key];
                    return (
                        <Switch
                            key={key}
                            label={feature.label}
                            checked={!disableExperimentalFeatures && feature.enabled}
                            disabled={feature.disabled ?? disableExperimentalFeatures}
                            onChange={() => onFeatureChange(key)}
                        />
                    );
                })}
            </div>
            <Divider />
        </>
    );
};
