'use server';
/**
 * @fileOverview This file defines a Genkit flow to dynamically generate a structured daily plan based on user input,
 * calendar events, and preferences.
 *
 * - generateDynamicDailyPlan - A function that orchestrates the daily plan generation.
 * - GenerateDynamicDailyPlanInput - The input type for the generateDynamicDailyPlan function.
 * - GenerateDynamicDailyPlanOutput - The return type for the generateDynamicDailyPlan function.
 */

import {ai} from '@/ai/genkit';
import {z} from 'genkit';

// --- Input Schema ---
const CalendarEventSchema = z.object({
  id: z.string().describe('Unique ID of the calendar event.').uuid(),
  title: z.string().describe('Title of the calendar event.').min(1),
  start_time: z
    .string()
    .regex(/^([01]\d|2[0-3]):([0-5]\d)$/)
    .describe('Start time of the event in HH:MM format.'),
  end_time: z
    .string()
    .regex(/^([01]\d|2[0-3]):([0-5]\d)$/)
    .describe('End time of the event in HH:MM format.'),
  date: z
    .string()
    .regex(/^\d{4}-\d{2}-\d{2}$/)
    .describe('Date of the event in YYYY-MM-DD format.'),
});

const UserPreferencesSchema = z.object({
  planning_style: z
    .enum(['Structured', 'Flexible', 'Minimal'])
    .describe(
      'User preference for planning style: Structured (fixed times), Flexible (time estimates only), Minimal (key tasks only).'
    ),
  work_hours_start: z
    .string()
    .regex(/^([01]\d|2[0-3]):([0-5]\d)$/)
    .describe('User preferred work start time in HH:MM format.'),
  work_hours_end: z
    .string()
    .regex(/^([01]\d|2[0-3]):([0-5]\d)$/)
    .describe('User preferred work end time in HH:MM format.'),
  timezone: z.string().describe('User timezone, e.g., "America/New_York" or "UTC".').min(1),
});

const GenerateDynamicDailyPlanInputSchema = z.object({
  user_input: z
    .string()
    .describe('Natural language input from the user describing their day, tasks, and needs.')
    .min(1),
  date_for_plan: z
    .string()
    .regex(/^\d{4}-\d{2}-\d{2}$/)
    .describe('The date for which the plan needs to be generated in YYYY-MM-DD format.'),
  existing_calendar_events: z
    .array(CalendarEventSchema)
    .describe('A list of existing calendar events for the day, including id, title, start_time, end_time, and date. The AI MUST integrate these into the plan and NOT create conflicting new blocks.'),
  user_preferences: UserPreferencesSchema.describe('User specific planning preferences.'),
  user_goals: z
    .array(z.string().min(1))
    .describe('A list of general long-term goals or priorities for the user.').optional(),
  previous_day_incomplete_tasks: z
    .array(z.string().min(1))
    .optional()
    .describe('Optional: A list of tasks that were not completed on the previous day and might need to be carried over.'),
});
export type GenerateDynamicDailyPlanInput = z.infer<typeof GenerateDynamicDailyPlanInputSchema>;

// --- Output Schema ---
const SubtaskSchema = z.object({
  id: z.string().describe('Unique ID for the subtask.').uuid(),
  title: z.string().describe('Title of the subtask.').min(1),
  done: z.boolean().describe('Whether the subtask is completed.').default(false),
});

const TimeBlockSchema = z.object({
  id: z.string().describe('Unique ID for the time block.').uuid(),
  title: z.string().describe('Title of the time block.').min(1),
  type: z
    .enum(['work', 'meeting', 'break', 'personal', 'class', 'other'])
    .describe('Type of activity for the block.'),
  start_time: z
    .string()
    .regex(/^([01]\d|2[0-3]):([0-5]\d)$/)
    .describe('Start time of the block in HH:MM format.'),
  end_time: z
    .string()
    .regex(/^([01]\d|2[0-3]):([0-5]\d)$/)
    .describe('End time of the block in HH:MM format.'),
  duration_minutes: z.number().int().positive().describe('Duration of the block in minutes.'),
  priority: z.enum(['high', 'medium', 'low']).describe('Priority level of the block.'),
  tags: z.array(z.string().min(1)).describe('Relevant tags for the block.'),
  calendar_event_id: z
    .string().uuid()
    .nullable()
    .describe('Optional: ID of the linked Google Calendar event if applicable.'),
  agent_note: z
    .string()
    .describe('An insightful note or recommendation from the AI for this specific block.').min(1),
  subtasks: z.array(SubtaskSchema).describe('A list of subtasks within this time block.').default([]),
  completed: z.boolean().describe('Whether this block has been completed.').default(false),
  skipped: z.boolean().describe('Whether this block has been skipped.').default(false),
});

const GenerateDynamicDailyPlanOutputSchema = z.object({
  plan_date: z
    .string()
    .regex(/^\d{4}-\d{2}-\d{2}$/)
    .describe('The date for which the plan was generated in YYYY-MM-DD format.'),
  summary: z
    .string()
    .describe('A brief, agent-generated summary of the entire day\'s plan.').min(1),
  agent_notes: z
    .string()
    .describe('Overall follow-up suggestions or recommendations from the agent for the user.').min(1),
  blocks: z
    .array(TimeBlockSchema)
    .describe('A structured array of time blocks forming the daily plan.'),
});
export type GenerateDynamicDailyPlanOutput = z.infer<
  typeof GenerateDynamicDailyPlanOutputSchema
>;

// --- Wrapper Function ---
export async function generateDynamicDailyPlan(
  input: GenerateDynamicDailyPlanInput
): Promise<GenerateDynamicDailyPlanOutput> {
  return generateDynamicDailyPlanFlow(input);
}

// --- Genkit Prompt Definition ---
const generatePlanPrompt = ai.definePrompt({
  name: 'generatePlanPrompt',
  input: {schema: GenerateDynamicDailyPlanInputSchema},
  output: {schema: GenerateDynamicDailyPlanOutputSchema},
  prompt: `You are an intelligent daily planning agent. Your goal is to create a structured, productive, and intentional daily plan for the user based on their input, existing commitments, and preferences.

**Current Date for Planning**: {{{date_for_plan}}}

**User's Input for Today**:
{{{user_input}}}

**User's General Goals/Priorities**:
{{#if user_goals}}
{{#each user_goals}}- {{this}}
{{/each}}
{{else}}No specific goals provided.
{{/if}}

**User's Planning Preferences**:
- Planning Style: {{{user_preferences.planning_style}}}
- Work Hours: From {{{user_preferences.work_hours_start}}} to {{{user_preferences.work_hours_end}}}
- Timezone: {{{user_preferences.timezone}}}

**Existing Calendar Events (MUST integrate these into the plan and NOT create conflicting new blocks)**:
{{#if existing_calendar_events}}
{{#each existing_calendar_events}}
- {{this.title}} ({{this.date}} {{this.start_time}} - {{this.end_time}}, ID: {{this.id}})
{{/each}}
{{else}}No existing calendar events.
{{/if}}

**Incomplete Tasks from Previous Day (prioritize these if applicable)**:
{{#if previous_day_incomplete_tasks}}
{{#each previous_day_incomplete_tasks}}
- {{this}}
{{/each}}
{{else}}No incomplete tasks from the previous day.
{{/if}}

**Instructions for Generating the Plan**:
1.  **Understand Intent**: Carefully analyze the user's input to understand their tasks, priorities, and any specific requests for the day.
2.  **Integrate Calendar Events**: Absolutely ensure all existing_calendar_events are included in the plan AS IS, preventing any new blocks from overlapping with them. For calendar events, set type to 'meeting' or 'class' as appropriate, and calendar_event_id to the event's id. The title, start_time, end_time, and date for these blocks MUST match the provided calendar event details exactly. Generate unique UUIDs for id of calendar event blocks also.
3.  **Respect Preferences**: Adhere to the user_preferences for planning style (Structured, Flexible, Minimal), work hours, and timezone.
4.  **Structure**: Break down the day into distinct time blocks. For 'Structured' planning style, provide precise start and end times. For 'Flexible' or 'Minimal', still provide time estimates but allow for more leeway in agent_note. Ensure all blocks have a duration_minutes calculated correctly based on start_time and end_time.
5.  **Prioritization**: Assign priority (high, medium, low) to each task/block based on user input and goals.
6.  **Breaks & Well-being**: Recommend appropriate breaks, lunch, and personal time, especially for longer work blocks. Label these as type: "break" or type: "personal". Ensure these breaks are placed logically and do not conflict with existing calendar events.
7.  **Subtasks**: Where appropriate, break down larger tasks into smaller subtasks. Each subtask should have a unique UUID id.
8.  **Agent Notes**: Provide concise, helpful agent_note for each block (e.g., "Deep focus block", "Remember to hydrate").
9.  **Summary & Overall Notes**: Provide an overall summary of the day and agent_notes with general advice or follow-up suggestions.
10. **JSON Format**: The entire output MUST be a JSON object strictly adhering to the GenerateDynamicDailyPlanOutputSchema. Ensure all fields are present and correctly formatted. Do NOT include any extra text outside the JSON.
11. **IDs**: Generate unique UUID strings for all blocks.id and subtasks.id. These UUIDs should be unique within the generated plan.

Start generating the JSON output now.
`,
});

// --- Genkit Flow Definition ---
const generateDynamicDailyPlanFlow = ai.defineFlow(
  {
    name: 'generateDynamicDailyPlanFlow',
    inputSchema: GenerateDynamicDailyPlanInputSchema,
    outputSchema: GenerateDynamicDailyPlanOutputSchema,
  },
  async input => {
    // Generate the plan using the defined prompt.
    const {output} = await generatePlanPrompt(input);

    if (!output) {
      throw new Error('Failed to generate dynamic daily plan.');
    }

    // The output is already structured as per the schema due to prompt engineering.
    return output;
  }
);
