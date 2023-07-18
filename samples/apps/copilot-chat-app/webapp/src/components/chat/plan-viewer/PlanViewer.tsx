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

/**
 * See Semantic Kernel's `Plan` object below for full definition.
 * Not explicitly defining the type here to avoid additional overhead of property maintenance.
 * https://github.com/microsoft/semantic-kernel/blob/df07fc6f28853a481dd6f47e60d39a52fc6c9967/dotnet/src/SemanticKernel/Planning/Plan.cs#
 */

/*
eslint-disable 
    @typescript-eslint/no-unsafe-assignment,
    @typescript-eslint/no-unsafe-member-access,
    @typescript-eslint/no-unsafe-call,
*/
export type Plan = any;

export const PlanViewer: React.FC<PlanViewerProps> = ({ message, messageIndex, getResponse }) => {
    const classes = useClasses();
    const dispatch = useAppDispatch();
    const { selectedId } = useAppSelector((state: RootState) => state.conversations);

    // Track original plan from user message
    const parsedContent: Plan = JSON.parse(message.content);
    const originalPlan = parsedContent.proposedPlan;

    const planState = message.state ?? parsedContent.state;

    // If plan came from ActionPlanner, use parameters from top-level of plan
    if (parsedContent.type === PlanType.Action) {
        originalPlan.steps[0].parameters = originalPlan.parameters;
    }

    const userIntentPrefix = 'User Intent:User intent: ';
    const userIntentIndex = originalPlan.description.indexOf(userIntentPrefix) as number;
    const description: string =
        userIntentIndex !== -1
            ? originalPlan.description.substring(userIntentIndex + userIntentPrefix.length).trim()
            : '';

    const [plan, setPlan] = useState(originalPlan);

    const onPlanAction = async (planState: PlanState.PlanApproved | PlanState.PlanRejected) => {
        dispatch(
            updateMessageState({
                newMessageState: planState,
                messageIndex,
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
            contextVariables,
            messageType: ChatMessageType.Message,
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
                        step={{ ...step, index }}
                        enableEdits={planState === PlanState.PlanApprovalRequired}
                        enableStepDelete={plan.steps.length > 1}
                        singleStepPlan={plan.steps.length === 1}
                        onDeleteStep={onDeleteStep}
                    />
                );
            })}
            {planState === PlanState.PlanApprovalRequired && (
                <>
                    Would you like to proceed with the plan?
                    <div className={classes.buttons}>
                        <Button
                            data-testid="cancelPlanButton"
                            appearance="secondary"
                            onClick={() => {
                                void onPlanAction(PlanState.PlanRejected);
                            }}
                        >
                            No, cancel plan
                        </Button>
                        <Button
                            data-testid="proceedWithPlanButton"
                            type="submit"
                            appearance="primary"
                            onClick={() => {
                                void onPlanAction(PlanState.PlanApproved);
                            }}
                        >
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
