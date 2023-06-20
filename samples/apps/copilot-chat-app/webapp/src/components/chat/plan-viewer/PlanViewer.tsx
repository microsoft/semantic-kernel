import { Button, Text, makeStyles, mergeClasses, shorthands, tokens } from '@fluentui/react-components';
import { CheckmarkCircle24Regular, DismissCircle24Regular, Info24Regular } from '@fluentui/react-icons';
import { useState } from 'react';
import { ChatMessageType, IChatMessage } from '../../../libs/models/ChatMessage';
import { IPlanInput, PlanState, PlanType } from '../../../libs/models/Plan';
import { IAskVariables } from '../../../libs/semantic-kernel/model/Ask';
import { GetResponseOptions } from '../../../libs/useChat';
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
    getResponse: (options: GetResponseOptions) => Promise<void>;
}

export const PlanViewer: React.FC<PlanViewerProps> = ({ message, messageIndex, getResponse }) => {
    const classes = useClasses();
    const dispatch = useAppDispatch();
    const { selectedId } = useAppSelector((state: RootState) => state.conversations);

    // Track original plan from user message
    const parsedContent = JSON.parse(message.content);
    const originalPlan = parsedContent.proposedPlan;

    var planState = message.state ?? parsedContent.state;

    // If plan came from ActionPlanner, use parameters from top-level plan state
    // TODO: Can remove this after consuming nugets with #997 fixed
    if (parsedContent.type === PlanType.Action) {
        originalPlan.steps[0].parameters = originalPlan.state;
    }

    const userIntentPrefix = 'User Intent:User intent: ';
    const userIntentIndex = originalPlan.description.indexOf(userIntentPrefix);
    const description =
        userIntentIndex !== -1
            ? originalPlan.description.substring(userIntentIndex + userIntentPrefix.length).trim()
            : '';

    const [plan, setPlan] = useState(originalPlan);

    const onPlanAction = async (planState: PlanState.PlanApproved | PlanState.PlanRejected) => {
        dispatch(
            updateMessageState({
                newMessageState: planState,
                messageIndex: messageIndex,
                chatId: selectedId,
            }),
        );

        const contextVariables: IAskVariables[] = [
            {
                key: 'responseMessageId',
                value: message.id ?? '',
            },
            {
                key: 'proposedPlan',
                value: JSON.stringify({
                    proposedPlan: plan,
                    type: parsedContent.type,
                    state: planState,
                }),
            },
        ];

        contextVariables.push(
            planState === PlanState.PlanApproved
                ? {
                      key: 'planUserIntent',
                      value: description,
                  }
                : {
                      key: 'userCancelledPlan',
                      value: 'true',
                  },
        );

        // Invoke plan
        await getResponse({
            value: planState === PlanState.PlanApproved ? 'Yes, proceed' : 'No, cancel',
            contextVariables: contextVariables,
            messageType: ChatMessageType.Plan,
            chatId: selectedId,
        });
    };

    const onDeleteStep = (index: number) => {
        setPlan({
            ...plan,
            steps: plan.steps.filter((_step: IPlanInput, i: number) => i !== index),
        });
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
                        enableEdits={planState === PlanState.PlanApprovalRequired}
                        enableStepDelete={plan.steps.length > 1}
                        onDeleteStep={onDeleteStep}
                    />
                );
            })}
            {planState === PlanState.PlanApprovalRequired && (
                <>
                    Would you like to proceed with the plan?
                    <div className={classes.buttons}>
                        <Button appearance="secondary" onClick={() => onPlanAction(PlanState.PlanRejected)}>
                            No, cancel plan
                        </Button>
                        <Button type="submit" appearance="primary" onClick={() => onPlanAction(PlanState.PlanApproved)}>
                            Yes, proceed
                        </Button>
                    </div>
                </>
            )}
            {planState === PlanState.PlanApproved && (
                <div className={mergeClasses(classes.buttons, classes.status)}>
                    <CheckmarkCircle24Regular />
                    <Text className={classes.text}> Plan Executed</Text>
                </div>
            )}
            {planState === PlanState.PlanRejected && (
                <div className={mergeClasses(classes.buttons, classes.status)}>
                    <DismissCircle24Regular />
                    <Text className={classes.text}> Plan Cancelled</Text>
                </div>
            )}
            {(planState === PlanState.NoOp || planState === PlanState.Disabled) && (
                <div className={mergeClasses(classes.buttons, classes.status)}>
                    <Info24Regular />
                    <Text className={classes.text}>
                        {planState === PlanState.NoOp
                            ? 'Your app state has changed since this plan was generated, making it unreliable for the planner. Please request a fresh plan to avoid potential conflicts.'
                            : 'Only the person who prompted this plan can take action on it.'}
                    </Text>
                </div>
            )}
        </div>
    );
};
