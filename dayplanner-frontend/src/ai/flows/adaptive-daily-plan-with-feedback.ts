'use server';
/**
 * @fileOverview This file implements Genkit flows for adaptive daily planning with feedback.
 *
 * - eveningCheckin: A function to handle the evening check-in process, recording daily progress and generating follow-up messages.
 * - EveningCheckinInput: The input type for the eveningCheckin function.
 * - EveningCheckinOutput: The return type for the eveningCheckin function.
 *
 * - morningBriefing: A function to generate a personalized morning briefing based on past performance and upcoming commitments.
 * - MorningBriefingInput: The input type for the morningBriefing function.
 * - MorningBriefingOutput: The return type for the morningBriefing function.
 */

import { ai } from '@/ai/genkit';
import { z } from 'genkit';

// --- Evening Check-in Flow ---

const EveningCheckinInputSchema = z.object({
  userId: z.string().describe('The ID of the user performing the check-in.'),
  planDate: z.string().regex(/^\d{4}-\d{2}-\d{2}$/).describe('The date for which the check-in is being performed (YYYY-MM-DD).'),
  dailyPlanSummary: z.string().describe('A summary of the daily plan for the checked-in day.'),
  completedTasksSummary: z.string().describe('A summary of tasks or blocks marked as completed.'),
  skippedTasksSummary: z.string().describe('A summary of tasks or blocks marked as skipped.'),
  userNotes: z.string().optional().describe('Any additional notes or reflections from the user about their day.'),
});
export type EveningCheckinInput = z.infer<typeof EveningCheckinInputSchema>;

const EveningCheckinOutputSchema = z.object({
  followUpMessage: z.string().describe("A personalized follow-up message for the user based on their day's progress."),
});
export type EveningCheckinOutput = z.infer<typeof EveningCheckinOutputSchema>;

export async function eveningCheckin(input: EveningCheckinInput): Promise<EveningCheckinOutput> {
  return eveningCheckinFlow(input);
}

const eveningCheckinPrompt = ai.definePrompt({
  name: 'eveningCheckinPrompt',
  input: { schema: EveningCheckinInputSchema },
  output: { schema: EveningCheckinOutputSchema },
  prompt: `You are Day Planner AI, a supportive and intelligent daily planning assistant.\nThe user is performing their evening check-in for the day {{{planDate}}}.\n\nHere's a summary of their plan for today:\n{{{dailyPlanSummary}}}\n\nTasks they reported as completed:\n{{{completedTasksSummary}}}\n\nTasks they reported as skipped:\n{{{skippedTasksSummary}}}\n\nUser's additional notes:\n{{{userNotes}}}\n\nBased on this information, provide a concise, encouraging follow-up message.\nAcknowledge their efforts, comment positively on their progress, and gently suggest how incomplete tasks might be handled tomorrow (e.g., "I'll plan tomorrow around your incomplete tasks" or "we can adjust tomorrow's plan").\nDo not ask questions. Keep it brief and to the point, concluding with a positive closing like "Sleep well!" or "Have a restful evening!".`,
});

const eveningCheckinFlow = ai.defineFlow(
  {
    name: 'eveningCheckinFlow',
    inputSchema: EveningCheckinInputSchema,
    outputSchema: EveningCheckinOutputSchema,
  },
  async (input) => {
    const { output } = await eveningCheckinPrompt(input);
    // In a full implementation, this is where the `memory_writer` node would be called
    // to embed the check-in data into the pgvector database for continuous learning.
    // For this Genkit flow, we focus on generating the message.
    return output!;
  }
);

// --- Morning Briefing Flow ---

const MorningBriefingInputSchema = z.object({
  userId: z.string().describe('The ID of the user requesting the briefing.'),
  briefingDate: z.string().regex(/^\d{4}-\d{2}-\d{2}$/).describe('The date for which the briefing is being generated (YYYY-MM-DD).'),
  yesterdaysPerformanceSummary: z.string().describe('A summary of yesterday\'s plan, completed tasks, and any incomplete items.'),
  todayCalendarSummary: z.string().describe('A summary of today\'s key calendar events and meetings.'),
  userGoalsAndPreferences: z.string().describe('A summary of retrieved user goals, preferences, and recurring patterns from memory.'),
});
export type MorningBriefingInput = z.infer<typeof MorningBriefingInputSchema>;

const MorningBriefingOutputSchema = z.object({
  briefingMessage: z.string().describe('A personalized morning briefing message for the user.'),
});
export type MorningBriefingOutput = z.infer<typeof MorningBriefingOutputSchema>;

export async function morningBriefing(input: MorningBriefingInput): Promise<MorningBriefingOutput> {
  return morningBriefingFlow(input);
}

const morningBriefingPrompt = ai.definePrompt({
  name: 'morningBriefingPrompt',
  input: { schema: MorningBriefingInputSchema },
  output: { schema: MorningBriefingOutputSchema },
  prompt: `Good morning, Day Planner AI user! It's {{{briefingDate}}}.\nYou are Day Planner AI, your intelligent and proactive daily planning assistant.\n\nHere's a quick look at your planning context:\nYesterday's performance:\n{{{yesterdaysPerformanceSummary}}}\n\nToday's key calendar events:\n{{{todayCalendarSummary}}}\n\nYour known goals and preferences:\n{{{userGoalsAndPreferences}}}\n\nBased on this, generate a personalized, motivating, and action-oriented morning briefing.\nStart with a warm greeting.\nAcknowledge yesterday's performance (positively spin incomplete tasks if any, e.g., "we'll carry these forward").\nHighlight key events for today and offer a proactive nudge or recommendation (e.g., "remember to block deep work before your 10 AM meeting" or "focus on your high-priority project first").\nKeep the tone encouraging and efficient. Do not ask questions. Aim for around 3-5 sentences.`,
});

const morningBriefingFlow = ai.defineFlow(
  {
    name: 'morningBriefingFlow',
    inputSchema: MorningBriefingInputSchema,
    outputSchema: MorningBriefingOutputSchema,
  },
  async (input) => {
    const { output } = await morningBriefingPrompt(input);
    return output!;
  }
);
