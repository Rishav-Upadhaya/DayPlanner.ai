'use server';
/**
 * @fileOverview A Genkit flow to generate a personalized daily plan by applying user memory.
 *
 * - learnAndApplyUserMemory - A function that handles the daily plan generation process, incorporating user's past patterns, preferences, and goals.
 * - LearnAndApplyUserMemoryInput - The input type for the learnAndApplyUserMemory function.
 * - LearnAndApplyUserMemoryOutput - The return type for the learnAndApplyUserMemory function, representing a structured daily plan.
 */

import {ai} from '@/ai/genkit';
import {z} from 'genkit';

const TimeBlockSchema = z.object({
  id: z.string().uuid().describe('Unique identifier for the time block.'),
  title: z.string().describe('Title or description of the activity.'),
  type: z
    .enum(['work', 'meeting', 'break', 'personal', 'class'])
    .describe('Category of the time block.'),
  start_time: z
    .string()
    .regex(/^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$/)
    .describe('Start time in HH:MM format (e.g., "10:30").'),
  end_time: z
    .string()
    .regex(/^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$/)
    .describe('End time in HH:MM format (e.g., "12:30").'),
  duration_minutes: z
    .number()
    .int()
    .positive()
    .describe('Duration of the block in minutes.'),
  priority: z
    .enum(['high', 'medium', 'low'])
    .describe('Priority level of the activity.'),
  agent_note: z
    .string()
    .optional()
    .describe('Optional note or suggestion from the AI agent.'),
});

const LearnAndApplyUserMemoryInputSchema = z.object({
  userRequest: z
    .string()
    .describe(
      'The user\'s natural language request for their daily plan (e.g., "Plan my day tomorrow, I have a big project due").'
    ),
  currentDate: z
    .string()
    .describe('The current date in YYYY-MM-DD format (e.g., "2025-01-01").'),
  existingCalendarEvents: z
    .string()
    .describe(
      'A summary of existing calendar events for the day, formatted as a string (e.g., "10:00 AM - Standup, 2:00 PM - Client Meeting").'
    ),
  userPreferences: z
    .string()
    .describe(
      'A summary of the user\'s known preferences, such as work hours, preferred breaks, or planning style (e.g., "Work hours are 9 AM to 5 PM, prefers 30-min lunch at 1 PM, structured planning.").'
    ),
  userMemories: z
    .string()
    .describe(
      'Retrieved historical patterns, past completions, and goals relevant to the user, formatted as a string (e.g., "Last week you struggled with deep work after 3 PM. You often complete tasks faster in the morning. Goal: focus on project X this week.").'
    ),
});
export type LearnAndApplyUserMemoryInput = z.infer<
  typeof LearnAndApplyUserMemoryInputSchema
>;

const LearnAndApplyUserMemoryOutputSchema = z
  .array(TimeBlockSchema)
  .describe('A structured daily plan consisting of time blocks.');
export type LearnAndApplyUserMemoryOutput = z.infer<
  typeof LearnAndApplyUserMemoryOutputSchema
>;

export async function learnAndApplyUserMemory(
  input: LearnAndApplyUserMemoryInput
): Promise<LearnAndApplyUserMemoryOutput> {
  return learnAndApplyUserMemoryFlow(input);
}

const prompt = ai.definePrompt({
  name: 'planGeneratorPrompt',
  input: {schema: LearnAndApplyUserMemoryInputSchema},
  output: {schema: LearnAndApplyUserMemoryOutputSchema},
  prompt: `You are an intelligent daily planner AI. Your goal is to create a highly personalized and effective daily plan for the user.

Current Date: {{{currentDate}}}

User's Request: {{{userRequest}}}

Existing Calendar Events: {{{existingCalendarEvents}}}

User Preferences: {{{userPreferences}}}

User's Historical Patterns, Completions, and Goals (Memory): {{{userMemories}}}

Based on the user's request, their existing calendar commitments, their stated preferences, AND ESPECIALLY their historical patterns and goals from memory, generate a structured daily plan as an array of time blocks.

Ensure the plan is realistic, considers energy levels based on past patterns, and prioritizes tasks according to the user's goals. If there are conflicts, try to resolve them intelligently based on preferences and historical data, or note them for the user.

Your output MUST be a JSON array of time block objects, each adhering strictly to the provided JSON schema. Ensure 'id' for each block is a valid UUID, 'start_time' and 'end_time' are in HH:MM format, and 'duration_minutes' is accurate. Example:
[
  {
    "id": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
    "title": "Review project brief",
    "type": "work",
    "start_time": "09:00",
    "end_time": "10:00",
    "duration_minutes": 60,
    "priority": "high",
    "agent_note": "Deep focus required."
  },
  {
    "id": "f0e9d8c7-b6a5-4321-fedc-ba9876543210",
    "title": "Standup Meeting",
    "type": "meeting",
    "start_time": "10:00",
    "end_time": "10:15",
    "duration_minutes": 15,
    "priority": "high",
    "agent_note": null
  }
]`
});

const learnAndApplyUserMemoryFlow = ai.defineFlow(
  {
    name: 'learnAndApplyUserMemoryFlow',
    inputSchema: LearnAndApplyUserMemoryInputSchema,
    outputSchema: LearnAndApplyUserMemoryOutputSchema,
  },
  async (input) => {
    // In a real application, the 'userMemories', 'existingCalendarEvents',
    // and 'userPreferences' would be fetched from a database or other services
    // (e.g., via LangGraph's memory_retriever and calendar_reader nodes)
    // before being passed to this prompt. For this Genkit flow, we assume
    // they are pre-retrieved and provided as input.

    const {output} = await prompt(input);
    if (!output) {
      throw new Error('Failed to generate a personalized daily plan.');
    }
    return output;
  }
);
