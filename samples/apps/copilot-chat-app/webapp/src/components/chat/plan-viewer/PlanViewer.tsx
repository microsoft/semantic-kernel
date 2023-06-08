import { Button, Text, makeStyles, mergeClasses, shorthands, tokens } from '@fluentui/react-components';
import { CheckmarkCircle24Regular, DismissCircle24Regular } from '@fluentui/react-icons';
import { useState } from 'react';
import { ChatMessageState, IChatMessage } from '../../../libs/models/ChatMessage';
import { IPlanInput } from '../../../libs/models/Plan';
import { IAskVariables } from '../../../libs/semantic-kernel/model/Ask';
import { useAppDispatch, useAppSelector } from '../../../redux/app/hooks';
import { RootState } from '../../../redux/app/store';
import { updateMessageState } from '../../../redux/features/conversations/conversationsSlice';
import { PlanStepCard } from './PlanStepCard';

const useClasses = makeStyles({
    container: {
        ...shorthands.gap(tokens.spacingVerticalM),
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'baseline',
    },
    buttons: {
        display: 'flex',
        flexDirection: 'row',
        marginTop: tokens.spacingVerticalM,
        marginBottom: tokens.spacingVerticalM,
        ...shorthands.gap(tokens.spacingHorizontalL),
    },
    status: {
        ...shorthands.gap(tokens.spacingHorizontalMNudge),
    },
    text: {
        alignSelf: 'center',
    },
});

interface PlanViewerProps {
    message: IChatMessage;
    messageIndex: number;
    getResponse: (
        value: string,
        contextVariables?: IAskVariables[],
        userApprovedPlan?: boolean,
        approvedPlanJson?: string,
        planUserIntent?: string,
    ) => Promise<void>;
}

export const PlanViewer: React.FC<PlanViewerProps> = ({ message, messageIndex, getResponse }) => {
    const classes = useClasses();
    const dispatch = useAppDispatch();
    const { selectedId } = useAppSelector((state: RootState) => state.conversations);

    // Track original plan from user message
    const parsedContent = JSON.parse(message.content);
    const originalPlan = parsedContent.proposedPlan;
    const planState = parsedContent.state;

    // If plan came from ActionPlanner, use parameters from top-level plan state
    if (parsedContent.Type === 'Action') {
        originalPlan.steps[0].parameters = originalPlan.state;
    }

    const userIntentPrefix = 'User Intent:User intent: ';
    const userIntentIndex = originalPlan.description.indexOf(userIntentPrefix);
    const description =
        userIntentIndex !== -1
            ? originalPlan.description.substring(userIntentIndex + userIntentPrefix.length).trim()
            : '';

    const [plan, setPlan] = useState(originalPlan);
    const [isDirty, setIsDirty] = useState(false);

    const onPlanApproval = async () => {
        dispatch(
            updateMessageState({
                newMessageState: ChatMessageState.PlanApproved,
                messageIndex: messageIndex,
                chatId: selectedId,
            }),
        );

        const planObject = {
            proposedPlan: plan,
            modified: isDirty,
            type: parsedContent.Type,
            state: ChatMessageState.PlanApproved,
            messageId: message.id,
        };

        // Invoke plan
        await getResponse(
            'Yes, proceed',
            [
                {
                    key: 'responseMessageId',
                    value: message.id ?? '',
                },
            ],
            true,
            JSON.stringify(planObject),
            description,
        );
    };

    const onPlanCancel = async () => {
        dispatch(
            updateMessageState({
                newMessageState: ChatMessageState.PlanRejected,
                messageIndex: messageIndex,
                chatId: selectedId,
            }),
        );
        // Bail out of plan
        await getResponse('No, cancel', undefined, false);
    };

    const onDeleteStep = (index: number) => {
        setPlan({
            ...plan,
            steps: plan.steps.filter((_step: IPlanInput, i: number) => i !== index),
        });
        setIsDirty(true);
    };

    return (
        <div className={classes.container}>
            <Text>Based on the request, Copilot Chat will run the following steps:</Text>
            <Text weight="bold">{`Goal: ${description}`}</Text>
            {plan.steps.map((step: any, index: number) => {
                return (
                    <PlanStepCard
                        key={`Plan step: ${index}`}
                        step={{ ...step, index: index }}
                        enableEdits={planState === ChatMessageState.PlanApprovalRequired}
                        enableStepDelete={plan.steps.length > 1}
                        onDeleteStep={onDeleteStep}
                        setIsPlanDirty={() => setIsDirty(true)}
                    />
                );
            })}
            {planState === ChatMessageState.PlanApprovalRequired && (
                <>
                    Would you like to proceed with the plan?
                    <div className={classes.buttons}>
                        <Button appearance="secondary" onClick={onPlanCancel}>
                            No, cancel plan
                        </Button>
                        <Button type="submit" appearance="primary" onClick={onPlanApproval}>
                            Yes, proceed
                        </Button>
                    </div>
                </>
            )}
            {planState === ChatMessageState.PlanApproved && (
                <div className={mergeClasses(classes.buttons, classes.status)}>
                    <CheckmarkCircle24Regular />
                    <Text className={classes.text}> Plan Executed</Text>
                </div>
            )}
            {planState === ChatMessageState.PlanRejected && (
                <div className={mergeClasses(classes.buttons, classes.status)}>
                    <DismissCircle24Regular />
                    <Text className={classes.text}> Plan Cancelled</Text>
                </div>
            )}
        </div>
    );
};
