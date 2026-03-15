# Day Planner AI ☀️

**Turn your messy day into pure intention.**

Day Planner AI is an intelligent, conversation-first daily assistant designed to reduce the cognitive load of modern scheduling. It understands your goals, your energy levels, and your existing commitments to build a structured, visual timeline of your day.

## 🚀 The Vision
Day Planner AI feels like talking to a brilliant, calm, and organized friend. Unlike traditional planners that demand manual effort, our agent does the heavy lifting: listening, inferring, and planning based on natural language.

## ✨ Core Features
- **💬 Conversational Planning:** Describe your day naturally. "I have a big project due, plan my day around it, and I'm slow in the morning."
- **🧠 Contextual Memory:** The AI learns your working habits, preferred deep-work blocks, and recurring goals over time.
- **📅 Calendar Integration:** Multi-calendar sync to detect conflicts and proactively suggest resolutions.
- **📈 Performance History:** Analyze your completion rates and work patterns with beautiful visual analytics.
- **🌙 Evening Check-in:** A gentle feedback loop to record progress and carry over incomplete tasks to tomorrow.

## 🎨 Design Philosophy
- **Conversation-First:** No complex onboarding forms. The first interaction is the product.
- **Calm Technology:** Soft colors (indigo, teal, slate) and gentle animations to reduce planning anxiety.
- **Spatial Awareness:** A vertical timeline view that gives your day a "shape" rather than just a flat list.
- **Mobile-First:** Optimized for 375px screens where 70% of daily planning occurs.

## 🛠️ Technical Stack
- **Framework:** [Next.js 15 (App Router)](https://nextjs.org/)
- **UI:** [React 19](https://react.dev/), [Tailwind CSS](https://tailwindcss.com/), [ShadCN UI](https://ui.shadcn.com/)
- **AI Engine:** [Genkit](https://firebase.google.com/docs/genkit) (Google Gemini 2.0 Flash)
- **Database/Auth:** [Firebase](https://firebase.google.com/)
- **Icons:** [Lucide React](https://lucide.dev/)
- **Charts:** [Recharts](https://recharts.org/)

## 📂 Project Structure
- `src/app`: Next.js App Router pages and layouts.
- `src/ai/flows`: Genkit AI logic for plan generation, morning briefings, and evening check-ins.
- `src/components/planner`: Specialized UI components like the Timeline and TimeBlockCard.
- `src/components/chat`: The conversational interface for interacting with the agent.
- `src/firebase`: Firebase configuration and custom hooks for data persistence.

## 🏁 Getting Started
1. Open the **Chat** tab to tell the agent about your upcoming day.
2. View your proposed schedule in the **Today** tab.
3. Mark tasks as complete as you progress.
4. Set your check-in times in **Settings** to receive proactive nudges.

---
*Day Planner AI | Version 1.0 | 2025*