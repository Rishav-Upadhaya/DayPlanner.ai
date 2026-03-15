'use server';
/**
 * @fileOverview A Genkit flow for generating a personalized daily plan based on natural language input.
 *
 * - conversationalDailyPlanInput - A function that handles the daily plan generation process.
 * - ConversationalDailyPlanInputInput - The input type for the conversationalDailyPlanInput function.
 * - ConversationalDailyPlanInputOutput - The return type for the conversationalDailyPlanInput function.
 */

import {ai} from '@/ai/genkit';
import {z} from 'genkit';

const SubtaskSchema = z.object({
  id: z.string().describe('Unique ID for the subtask.'),
  title: z.string().describe('Title or description of the subtask.'),
  done: z.boolean().describe('Whether the subtask has been completed.').default(false),
});

const PlanBlockSchema = z.object({
  id: z.string().describe('Unique ID for the plan block.'),
  title: z.string().describe('Title or description of the activity.'),
  type: z.enum(['work', 'meeting', 'break', 'personal', 'class']).describe('Category of the activity.'),
  start_time: z.string().regex(/^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$/).describe('Start time in HH:MM format (24-hour).'),
  end_time: z.string().regex(/^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$/).describe('End time in HH:MM format (24-hour).'),
  duration_minutes: z.number().int().positive().describe('Duration of the block in minutes.'),
  priority: z.enum(['high', 'medium', 'low']).describe('Priority level of the activity.'),
  tags: z.array(z.string()).optional().describe('Relevant tags for the activity.'),
  calendar_event_id: z.string().nullable().optional().describe('ID of the linked Google Calendar event, if applicable.'),
  agent_note: z.string().optional().describe('Notes or suggestions from the AI agent for this block.'),
  subtasks: z.array(SubtaskSchema).optional().describe('List of subtasks for this block.'),
  completed: z.boolean().describe('Whether the block has been completed.').default(false),
  skipped: z.boolean().describe('Whether the block has been skipped.').default(false),
});

const ConversationalDailyPlanInputInputSchema = z.object({
  userMessage: z.string().describe('Natural language description of the user\'s day and commitments.'),
  currentDate: z.string().describe('The current date in YYYY-MM-DD format.'),
  existingCalendarEvents: z.array(z.object({
    title: z.string().describe('Title of the calendar event.'),
    startTime: z.string().datetime().describe('Start time of the event in ISO 8601 format.'),
    endTime: z.string().datetime().describe('End time of the event in ISO 8601 format.'),
    description: z.string().optional().describe('Description of the calendar event.'),
    calendar: z.string().optional().describe('Name of the calendar the event belongs to.'),
  })).optional().describe('List of existing calendar events for the day.'),
  userPreferences: z.object({
    planningStyle: z.enum(['Structured', 'Flexible', 'Minimal']).default('Structured').describe('User\'s preferred planning style.'),
    workHours: z.object({
      start: z.string().regex(/^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$/).describe('Start of work hours in HH:MM format.'),
      end: z.string().regex(/^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$/).describe('End of work hours in HH:MM format.'),
    }).optional().describe('User\'s preferred daily work hours.'),
  }).optional().describe('User planning preferences for personalization.'),
  contextualMemories: z.array(z.string()).optional().describe('Relevant past preferences, patterns, and completions retrieved from memory for personalization.'),
});
export type ConversationalDailyPlanInputInput = z.infer<typeof ConversationalDailyPlanInputInputSchema>;

const ConversationalDailyPlanInputOutputSchema = z.object({
  blocks: z.array(PlanBlockSchema).describe('A structured array of time blocks forming the daily plan.'),
  summary: z.string().describe('An agent-generated summary of the daily plan.'),
  agent_notes: z.string().optional().describe('Additional notes or suggestions from the AI agent.'),
});
export type ConversationalDailyPlanInputOutput = z.infer<typeof ConversationalDailyPlanInputOutputSchema>;

export async function conversationalDailyPlanInput(input: ConversationalDailyPlanInputInput): Promise<ConversationalDailyPlanInputOutput> {
  return conversationalDailyPlanInputFlow(input);
}

const conversationalDailyPlanPrompt = ai.definePrompt({
  name: 'conversationalDailyPlanPrompt',
  input: {schema: ConversationalDailyPlanInputInputSchema},
  output: {schema: ConversationalDailyPlanInputOutputSchema},
  prompt: `You are an expert daily planner AI. Your goal is to help the user create a structured, productive, and intentional daily plan based on their natural language input, existing commitments, personal preferences, and past patterns.

Today is {{{currentDate}}}.

Here is the user's description of their day and commitments:
{{{userMessage}}}

{{#if existingCalendarEvents}}
Here are the user's existing calendar events for today. You must integrate these into the plan and identify any potential conflicts or overlaps. Do not re-list events that are clearly not for today.
{{#each existingCalendarEvents}}
- {{this.title}} from {{this.startTime}} to {{this.endTime}}{{#if this.description}} ({{this.description}}){{/if}}{{#if this.calendar}} (Calendar: {{this.calendar}}){{/if}}
{{/each}}
{{else}}
No existing calendar events were provided.
{{/if}}

{{#if userPreferences}}
The user has the following planning preferences:
Planning Style: {{userPreferences.planningStyle}}
{{#if userPreferences.workHours}}
Work Hours: {{userPreferences.workHours.start}} to {{userPreferences.workHours.end}}
{{/if}}
Please consider these when creating the plan.
{{/if}}

{{#if contextualMemories}}
Here are some relevant past preferences, patterns, or completions for this user. Use this information to personalize the plan:
{{#each contextualMemories}}
- {{{this}}}
{{/each}}
{{/if}}

Based on all the provided information, generate a comprehensive daily plan as a JSON object. The plan should consist of an array of time blocks. Ensure each block includes:
- An 'id' (a unique string).
- A 'title' (e.g., "Deep Work: Project Alpha").
- A 'type' from the following: 'work', 'meeting', 'break', 'personal', 'class'.
- 'start_time' and 'end_time' in HH:MM (24-hour) format.
- 'duration_minutes' calculated from start_time and end_time.
- A 'priority' from: 'high', 'medium', 'low'.
- Optional 'tags' (array of strings).
- Optional 'calendar_event_id' (string, if directly from an existing event).
- Optional 'agent_note' (a helpful suggestion or instruction).
- Optional 'subtasks' (an array of objects, each with 'id', 'title', 'done').
- 'completed' (boolean, default to false).
- 'skipped' (boolean, default to false).

Pay close attention to scheduling events within work hours if specified, incorporating breaks, and prioritizing tasks based on the user's input and preferences. If you detect any conflicts with existing calendar events, try to resolve them intelligently or suggest a resolution in the 'agent_note'.

Also provide a 'summary' of the entire plan and optional 'agent_notes' for general advice or follow-up.`,
});

const conversationalDailyPlanInputFlow = ai.defineFlow(
  {
    name: 'conversationalDailyPlanInputFlow',
    inputSchema: ConversationalDailyPlanInputInputSchema,
    outputSchema: ConversationalDailyPlanInputOutputSchema,
  },
  async (input) => {
    const {output} = await conversationalDailyPlanPrompt(input);
    return output!;
  }
);