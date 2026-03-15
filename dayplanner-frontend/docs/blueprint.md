# **App Name**: Day Planner AI

## Core Features:

- Conversational AI Planning: Users describe their day naturally via a chat interface, and the AI agent uses a planning tool to infer intent, integrate existing commitments, and generate a personalized daily schedule.
- Dynamic Daily Plan Generation: Based on conversational input, calendar data, and learned preferences, the AI agent dynamically generates a structured plan with time blocks, priorities, and break recommendations.
- Multi-Calendar Synchronization: Securely connects and synchronizes with multiple Google Calendar accounts to read existing events, detect conflicts, and inform plan generation.
- Persistent Contextual Memory: Leverages a vector database (pgvector) as a memory tool to continuously learn and retrieve user-specific patterns, past completions, goals, and preferences over time, enabling highly personalized planning.
- Interactive 'Today' View: Presents the AI-generated daily plan in a dynamic, draggable timeline interface, allowing users to intuitively view, edit, and mark tasks as complete.
- Automated Daily Engagement: Delivers personalized morning briefings with an AI tool for daily nudges and prompts evening check-ins to review completed tasks and refine future plans.
- Essential User & Integration Settings: Provides an intuitive interface for managing fundamental preferences such as notification schedules, timezones, and connecting external calendar services.

## Style Guidelines:

- Primary color: A bold, professional blue (#1A56DB), conveying clarity and efficiency, used for primary calls to action and active states.
- Background color: A muted, light blue-grey (#D6DEED), creating a calm and expansive environment for daily planning.
- Accent color: A vibrant teal (#0D9488), providing a refreshing contrast and signaling key interactive elements or categories like meetings.
- Supporting colors: Accent Indigo (#4338CA) for AI-related elements, Success Green (#059669) for completions, and Warning Amber (#D97706) for conflicts or check-ins.
- Headlines and display text: 'Plus Jakarta Sans' (sans-serif) for its modern and confident presence. Body and UI text: 'Inter' (sans-serif) for optimal readability and a clean aesthetic. Note: currently only Google Fonts are supported.
- Clean, line-art style icons that intuitively represent application sections and planning categories, maintaining a calm and organized aesthetic. The AI agent avatar features a gradient circle with a monogram and subtle pulse animation.
- A responsive, mobile-first design featuring a spatial timeline view for daily plans over flat lists. It adapts from a single-column layout on mobile to multi-column arrangements on larger screens, guided by a 12-column grid.
- Subtle and purposeful micro-animations enhance user feedback and reduce cognitive load. Examples include a three-dot pulse for the agent's 'thinking' state, a spring-bounce with confetti on task completion, and smooth cross-fades for page transitions.