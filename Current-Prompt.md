Claude, here’s your 1-Shot Seed Prompt:

---

BUSINESS\_CONTEXT: "We are building a **Next.js frontend UI** for a recruiting AI agent inside a multi-tenant real estate automation system. The recruiting flow is powered by LangFlow and accessed via FastAPI endpoints. This is a brand-new app scaffold, located at `C:\AI_src\ImpactLangFlow\frontend\`. The UI must be clean, mobile-first, themed in blues and cool grays, and built for long-term modularity with Atomic Design."

USER\_GOAL: "Generate a fully functional, production-ready React/Next.js frontend for the **Recruiting Agent** only. Include all globals, styling system, icon libraries, mobile responsiveness, and a light/dark toggle. Add support for chat history, SMS/telephony status indicators, and voice-ready toggles. Stub out placeholder routes for the other agents (supervisor, admin, ops)."

FLOW\_METADATA: { "name": "Recruiting Agent UI", "description": "Standalone frontend chat UI for Katelyn's recruiting assistant, with modular agent structure and clean multi-device UX." }

---

GUARDRAILS:

* Output goes to: `C:\AI_src\ImpactLangFlow\frontend\`
* Use **Next.js (App Router, TypeScript)** and **TailwindCSS**
* Follow **Atomic Design**: /app → /components → /lib → /styles
* Theme: Impact Blue `#1D4ED8` + Gray-100 to Gray-900 range
* Use **ShadCN** for UI primitives, **Lucide** for icons, **Framer Motion** for animations
* Dark/light toggle via `<ThemeToggle />` component
* Mobile-first design, no layout overflow, nav drawer on mobile
* Chat must be real-time friendly (WebSocket-ready), but use fetch/REST now
* Show **SMS/Call status** (idle, delivered, failed, queued) on each message bubble using icon + tooltip
* Support multi-session history panel on left
* No hardcoded API keys or URLs; all config via `process.env`

---

API ROUTES (REST, placeholder only):

* `POST /api/v1/agents/recruiting/invoke`
* `GET /api/v1/agents/recruiting/conversations`
* `POST /api/v1/agents/recruiting/conversations/:id/message`

---

FILE STRUCTURE:

```
/app
  /agents
    /recruiting/page.tsx        → Chat interface for recruiting
    /supervisor/page.tsx        → Placeholder
    /admin/page.tsx             → Placeholder
    /operations/page.tsx        → Placeholder
  layout.tsx                    → ThemeShell
  page.tsx                      → Redirect to recruiting

/components
  /chat/
    ChatInterface.tsx
    MessageBubble.tsx
    ComposeBar.tsx
    SmsStatusIcon.tsx
  /sidebar/
    ConversationSidebar.tsx
    AgentSelector.tsx
  /shared/
    ThemeToggle.tsx
    Avatar.tsx
    Button.tsx
    Badge.tsx
    ConfirmModal.tsx
    VoiceToggle.tsx

/context/
  AgentContext.tsx
  SessionContext.tsx

/hooks/
  useChat.ts
  useTheme.ts
  useSession.ts

/icons/
  SmsDelivered.tsx
  SmsFailed.tsx
  SmsQueued.tsx
  SmsIdle.tsx

/lib/
  api.ts
  constants.ts
  utils.ts

/public/assets/
  avatars/
  logos/

/styles/
  globals.css
  tailwind.config.ts
  postcss.config.js
  theme.ts

.env.example → include:
  NEXT_PUBLIC_API_URL=
  NEXT_PUBLIC_ENV=dev
  NEXT_PUBLIC_SUPPORT_PHONE=
  NEXT_PUBLIC_USE_WEBSOCKETS=false
```

---

DESIGN NOTES:

* Chat layout: left = conversation list, center = chat, right = agent metadata (on desktop)
* Mobile: only chat + toggleable drawer
* Each chat message: avatar, name, timestamp, SMS status icon (if sent via telephony), bubble
* SMS status: small icon (Lucide + color-coded), shown inline right-aligned with hover tooltip
* Compose bar: TTS toggle, send button, input field
* All components must be themed and use Tailwind spacing/padding tokens

---

SELF-AUDIT:

* [x] Recruiting page fully functional
* [x] Icons for SMS/Call statuses present
* [x] All layouts are mobile-first
* [x] Placeholder routes scaffolded
* [x] All styling centralized in Tailwind config
* [x] State hooks scoped to session, agent ID
* [x] No backend logic implemented
* [x] API client fetch-ready for REST endpoints

---

FINAL TASK:
Generate `frontend/` folder under `C:\AI_src\ImpactLangFlow\frontend\` with all files listed and the **Recruiting Agent UI fully operational**. Placeholder pages must not break routing. Voice/SMS toggles must be present but non-functional. Use stubs where necessary.
