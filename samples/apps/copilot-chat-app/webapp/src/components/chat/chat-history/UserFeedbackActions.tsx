import { Button, Text, Tooltip, makeStyles } from '@fluentui/react-components';
import { useCallback } from 'react';
import { UserFeedback } from '../../../libs/models/ChatMessage';
import { useAppDispatch, useAppSelector } from '../../../redux/app/hooks';
import { RootState } from '../../../redux/app/store';
import { FeatureKeys } from '../../../redux/features/app/AppState';
import { setUserFeedback } from '../../../redux/features/conversations/conversationsSlice';
import { ThumbDislike16, ThumbLike16 } from '../../shared/BundledIcons';

const useClasses = makeStyles({
    root: {
        display: 'flex',
        'place-content': 'flex-end',
        alignItems: 'center',
    },
});

interface IUserFeedbackProps {
    messageIndex: number;
}

export const UserFeedbackActions: React.FC<IUserFeedbackProps> = ({ messageIndex }) => {
    const classes = useClasses();

    const dispatch = useAppDispatch();
    const { selectedId } = useAppSelector((state: RootState) => state.conversations);
    const { features } = useAppSelector((state: RootState) => state.app);

    const onUserFeedbackProvided = useCallback(
        (positive: boolean) => {
            dispatch(
                setUserFeedback({
                    userFeedback: positive ? UserFeedback.Positive : UserFeedback.Negative,
                    messageIndex,
                    chatId: selectedId,
                }),
            );
        },
        [dispatch, messageIndex, selectedId],
    );

    return (
        <div className={classes.root}>
            <Text color="gray" size={200}>
                AI-generated content may be incorrect
            </Text>
            <Tooltip content={'Like bot message'} relationship="label">
                <Button
                    icon={<ThumbLike16 />}
                    appearance="transparent"
                    aria-label="Edit"
                    onClick={() => onUserFeedbackProvided(true)}
                    disabled={!features[FeatureKeys.RLHF].enabled}
                />
            </Tooltip>
            <Tooltip content={'Dislike bot message'} relationship="label">
                <Button
                    icon={<ThumbDislike16 />}
                    appearance="transparent"
                    aria-label="Edit"
                    onClick={() => onUserFeedbackProvided(false)}
                    disabled={!features[FeatureKeys.RLHF].enabled}
                />
            </Tooltip>
        </div>
    );
};
