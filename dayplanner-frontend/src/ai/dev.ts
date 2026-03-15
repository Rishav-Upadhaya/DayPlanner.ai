import { config } from 'dotenv';
config();

import '@/ai/flows/conversational-daily-plan-input.ts';
import '@/ai/flows/adaptive-daily-plan-with-feedback.ts';
import '@/ai/flows/learn-and-apply-user-memory.ts';
import '@/ai/flows/generate-dynamic-daily-plan.ts';