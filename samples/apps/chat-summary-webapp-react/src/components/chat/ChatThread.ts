// Copyright (c) Microsoft. All rights reserved.

export interface IChatMessage {
    content: string;
    author: string;
    timestamp: string;
    mine: boolean;
}

export const ChatThread: IChatMessage[] = [
    {
        content: 'Hi, do you know much about cars?',
        author: 'Cecil Folk',
        timestamp: 'Yesterday, 10:15 PM',
        mine: true,
    },
    {
        content: 'Yeah, I love cars! What do you want to know?',
        author: 'John Doe',
        timestamp: 'Yesterday, 10:20 PM',
        mine: false,
    },
    {
        content: "I'm thinking of buying a new car, any recommendations?",
        author: 'Cecil Folk',
        timestamp: 'Yesterday, 10:25 PM',
        mine: true,
    },
    {
        content:
            "If you're looking for a sports car, I'd recommend the Porsche 911. If you want something more practical, the Honda Civic is a great option.",
        author: 'John Doe',
        timestamp: 'Yesterday, 10:30 PM',
        mine: false,
    },
    {
        content: "I'm leaning towards something more eco-friendly, any suggestions?",
        author: 'Cecil Folk',
        timestamp: 'Yesterday, 10:35 PM',
        mine: true,
    },
    {
        content:
            "The Toyota Prius is a great hybrid option. The Nissan Leaf is an all-electric car that's also a good choice.",
        author: 'John Doe',
        timestamp: 'Yesterday, 10:40 PM',
        mine: false,
    },
    {
        content:
            "Thanks for the suggestions, I'll take an action item for myself to go to the Nissan dealer this weekend.",
        author: 'Cecil Folk',
        timestamp: 'Yesterday, 10:45 PM',
        mine: true,
    },
    {
        content: 'No problem, let me know if you have any other questions.',
        author: 'John Doe',
        timestamp: 'Yesterday, 10:50 PM',
        mine: false,
    },
    {
        content: 'Actually, I do have one more question. How do you feel about electric cars?',
        author: 'Cecil Folk',
        timestamp: 'Yesterday, 10:55 PM',
        mine: true,
    },
    {
        content:
            "I think they're the future of transportation. They're more environmentally friendly and can be cheaper to operate in the long run.",
        author: 'John Doe',
        timestamp: 'Yesterday, 11:00 PM',
        mine: false,
    },
    {
        content: 'I agree, I am thinking about going for an electric car. Thanks for your help',
        author: 'Cecil Folk',
        timestamp: 'Yesterday, 11:05 PM',
        mine: true,
    },
    {
        content: "You're welcome, happy car shopping!",
        author: 'John Doe',
        timestamp: 'Yesterday, 11:10 PM',
        mine: false,
    },
    {
        content: 'Hey John, have you ever seen a penguin in the wild?',
        author: 'Cecil Folk',
        timestamp: 'Yesterday, 10:15 PM',
        mine: true,
    },
    {
        content: "No, I haven't. Have you?",
        author: 'John Doe',
        timestamp: 'Yesterday, 10:20 PM',
        mine: false,
    },
    {
        content: "Yeah, I saw some while I was on a trip to Antarctica. They're amazing swimmers.",
        author: 'Cecil Folk',
        timestamp: 'Yesterday, 10:25 PM',
        mine: true,
    },
    {
        content:
            "Wow, that must have been an incredible experience. That reminds me, I need to book that Antarctica trip for next summer. I've only seen them at the zoo.",
        author: 'John Doe',
        timestamp: 'Yesterday, 10:30 PM',
        mine: false,
    },
    {
        content: 'It was definitely a trip of a lifetime. Speaking of birds, have you ever heard a lyrebird?',
        author: 'Cecil Folk',
        timestamp: 'Yesterday, 10:35 PM',
        mine: true,
    },
    {
        content: "No, I haven't. What's special about them?",
        author: 'John Doe',
        timestamp: 'Yesterday, 10:40 PM',
        mine: false,
    },
    {
        content:
            "They're known for their incredible mimicry abilities. They can imitate all kinds of sounds, including other birds and even machinery.",
        author: 'Cecil Folk',
        timestamp: 'Yesterday, 10:45 PM',
        mine: true,
    },
    {
        content: "That's amazing! Let's plan on meeting up next weekend to go bird watching.",
        author: 'John Doe',
        timestamp: 'Yesterday, 10:50 PM',
        mine: false,
    },
    {
        content: "I highly recommend looking up some videos of them online. They're truly one of a kind.",
        author: 'Cecil Folk',
        timestamp: 'Yesterday, 10:55 PM',
        mine: true,
    },
    {
        content: "Thanks for the recommendation. I'll definitely check them out.",
        author: 'John Doe',
        timestamp: 'Yesterday, 11:00 PM',
        mine: false,
    },
];
