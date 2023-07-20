import { Divider, Switch, Text, makeStyles, tokens } from '@fluentui/react-components';
import { useCallback } from 'react';
import { useAppDispatch, useAppSelector } from '../../../redux/app/hooks';
import { RootState } from '../../../redux/app/store';
import { FeatureKeys, Setting } from '../../../redux/features/app/AppState';
import { setFeatureFlag } from '../../../redux/features/app/appSlice';

const useClasses = makeStyles({
    featureDescription: {
        paddingLeft: '5%',
        color: tokens.colorNeutralForeground2,
        paddingBottom: tokens.spacingVerticalS,
    },
});

interface ISettingsSectionProps {
    setting: Setting;
    contentOnly?: boolean;
}

export const SettingSection: React.FC<ISettingsSectionProps> = ({ setting, contentOnly }) => {
    const classes = useClasses();
    const { features } = useAppSelector((state: RootState) => state.app);
    const dispatch = useAppDispatch();

    const onFeatureChange = useCallback(
        (featureKey: FeatureKeys) => {
            dispatch(setFeatureFlag(featureKey));
        },
        [dispatch],
    );

    return (
        <>
            {!contentOnly && <h3>{setting.title}</h3>}
            {setting.description && <p>{setting.description}</p>}
            <div
                style={{
                    display: 'flex',
                    flexDirection: `${setting.stackVertically ? 'column' : 'row'}`,
                    flexWrap: 'wrap',
                }}
            >
                {setting.features.map((key) => {
                    const feature = features[key];
                    return (
                        <>
                            <Switch
                                key={key}
                                label={feature.label}
                                checked={feature.enabled}
                                disabled={feature.inactive}
                                onChange={() => onFeatureChange(key)}
                            />
                            <Text key={`${key}-description`} className={classes.featureDescription}>
                                {feature.description}
                            </Text>
                        </>
                    );
                })}
            </div>
            {!contentOnly && <Divider />}
        </>
    );
};
