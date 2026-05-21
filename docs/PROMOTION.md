# Promotion playbook

Ready-to-use materials for launching Workout Agent publicly.

> Replace `[LIVE_URL]`, `[DEMO_URL]` (Loom/YouTube), and `[REPO_URL]` everywhere before posting.

---

## Launch sequence

1. Get the multi-user version working end-to-end and test with 2–3 friends. Iterate on rough edges.
2. Record a **2-minute demo video** (script below). Loom or QuickTime → upload to Loom/YouTube as unlisted, embed in the LinkedIn post and the GitHub README.
3. Update `README.md` with the live URL and demo link.
4. **Day-of:** publish the LinkedIn post in the morning (best engagement for B2C tech in EU is ~9–10am local time).
5. **Day 1 evening / Day 2:** cross-post a shorter version to X/Twitter and the relevant Reddit subs (timing: late evening UTC for r/fitness, anytime for r/sideproject).
6. **Optional, Day 3–7:** "Show HN" post if it's gaining traction.

---

## LinkedIn (primary post)

A longer, narrative-driven post — LinkedIn rewards story + insight, not links.

```
I built an AI workout coach as a side project — and just made it public.

Here's the thing about workout apps: they're rigid. They track your sets and reps, but real fitness is messy.

You play squash on Tuesday. You tweak your shoulder. You want to shift focus to legs this month.
And every time you ask ChatGPT for advice, you have to re-explain your entire training history.

So I built Workout Agent — an AI coach that already knows your workout history (via Hevy).
Ask anything. Adjust your routine on the fly. Get insights you'd never dig up manually.

A few things it can do:
• "Why has my bench stalled the last 3 weeks?"
• "I tweaked my shoulder, adjust my push day."
• "I'm playing squash twice this week — reduce my leg volume accordingly."
• "Build me a new push/pull/legs routine focused on hypertrophy."

It's free, open source, takes 2 minutes to set up, and runs as a PWA (add to your home screen and it looks like a native app).

Demo + link in the comments.

#fitness #AI #sideproject #opensource #pwa
```

**First comment** (LinkedIn ranks posts with links lower, so push them to the comments):

```
Try it: [LIVE_URL]
2-min demo: [DEMO_URL]
Source: [REPO_URL]

Built with FastAPI + Gemini + Firebase + the open-source hevy-mcp package. Feedback welcome 🙏
```

---

## X / Twitter (short)

Two variants. Pick one — the second is more "show, don't tell".

### Variant A — punchy

```
I built an AI workout coach that actually knows your training history.

No more re-explaining your background to ChatGPT every time.

Connect your Hevy account → ask anything:
• "Why is my bench stuck?"
• "Adjust my routine for a shoulder tweak"
• "What muscles am I neglecting?"

Free + open source 👇
[LIVE_URL]
```

### Variant B — story

```
Every workout app I've used is rigid.

But fitness is messy — you play other sports, you tweak something, your goals shift.

So I built Workout Agent: an AI coach that reads your Hevy data and chats with you about it.

Free, open source, works on your phone.

[LIVE_URL]
```

---

## Reddit

**Subs to consider, in order of fit:**

1. `r/sideproject` — always friendly to genuine builders, good first launch sub.
2. `r/hevyapp` — most directly relevant audience.
3. `r/selfhosted` — emphasize the "fork and host your own" angle.
4. `r/fitness` — be very careful; strict rules against self-promotion. Read [their rules](https://www.reddit.com/r/Fitness/wiki/rules) first. Probably skip.
5. `r/fitness30plus`, `r/xxfitness`, `r/weightroom` — only if the post adds genuine value beyond the link.

### r/sideproject template

```
Title: [Show] Workout Agent — AI coach that already knows your Hevy training history

I got tired of workout apps being one-size-fits-all. I wanted to ask things like
"am I overtraining chest?" or "I tweaked my shoulder, adjust my push day"
without explaining my entire training background to ChatGPT every time.

So I built this. It connects to your Hevy account (via the official API)
and gives you a chat interface to an AI that already knows your data.
It can read your history, spot trends, and even modify your routines for you.

Stack: FastAPI + Gemini 3 Flash on Vertex AI, Firebase Auth, Firestore,
hevy-mcp (open source), and a vanilla-JS PWA. Hosted on Cloud Run.

Free, open source. Hevy PRO subscription required (their API gate, not mine).

→ [LIVE_URL]
→ Source: [REPO_URL]
→ Demo: [DEMO_URL]

Feedback welcome — especially on the onboarding flow and whether
the AI's routine suggestions actually feel useful.
```

### r/hevyapp template

```
Title: I built a free AI coach that connects to your Hevy data — looking for feedback

Hi all! Built a side project on top of Hevy's API. It's a chat agent that
reads your workouts and routines and can adapt them for you.

Things I find genuinely useful:
- Adapting push day around a shoulder tweak.
- Reducing leg volume in weeks where I play squash a lot.
- Spotting muscle groups I've been neglecting.
- Asking "what should I do next" without manually checking my last 5 sessions.

It's free and open source. Hevy PRO is required (API limit).

→ [LIVE_URL]

Genuinely interested in what works and what doesn't for the Hevy community —
roast away.
```

---

## Demo video script (~2 min)

Aim for 90–120 seconds. Pace matters; record on a phone screen with QuickTime / Loom.

| # | Time | Action | Voice-over |
|---|------|--------|------------|
| 1 | 0:00 – 0:10 | Phone home screen → tap the Workout Agent icon | "This is Workout Agent — an AI workout coach that already knows your training history." |
| 2 | 0:10 – 0:25 | Sign in with Google (one tap), accept consent, paste Hevy key | "Sign in with Google, agree to the terms, paste your Hevy API key. That's the entire setup." |
| 3 | 0:25 – 0:45 | Type "Show me my last workout" → agent responds | "It can read your real Hevy data. Last workout, with the actual sets and weights." |
| 4 | 0:45 – 1:10 | "I tweaked my shoulder. Adjust my push day for next week." → agent modifies routine | "Now ask it to actually adapt your routine. It edits the routine in Hevy itself — open the Hevy app and the change is there." |
| 5 | 1:10 – 1:30 | "I'm playing squash twice this week. Reduce my leg volume accordingly." | "It also knows about other sports. Squash, climbing, running — it adapts your lifting around what you're already doing." |
| 6 | 1:30 – 1:45 | "What muscle groups am I neglecting this month?" → agent analyses trend | "And it can analyse trends across your training history that you'd never dig up yourself." |
| 7 | 1:45 – 2:00 | Show "Add to Home Screen" prompt; cut to the icon on the home screen | "It's a PWA, so you can install it on your phone. Free, open source — link below." |

**Recording tips:**
- Phone in portrait, screen recording at 60fps.
- Speak into the mic, don't rely on phone audio.
- Cut all dead air; the goal is dense, fast pacing.
- End with the live URL and GitHub URL on a static title card for 2 seconds.

---

## Talking points / pitch lines

For comments, replies, or impromptu conversations:

- **One-liner:** "An AI workout coach that already knows your training history."
- **Two-liner:** "It connects to your Hevy data and chats with you. Adapt routines on the fly, ask anything about your training, no more re-explaining your background to ChatGPT."
- **For technical folks:** "FastAPI + Gemini + hevy-mcp on Cloud Run. Per-user MCP subprocess, Fernet-encrypted API keys in Firestore, Firebase Auth."
- **For lifters:** "If you've ever wanted to ask 'should I deload?' or 'what muscle groups am I missing?' and have the AI actually look at your numbers — this is that."

---

## Things to avoid

- Don't oversell. It's a pet project, not a startup. People reward honesty.
- Don't claim it replaces a coach or a physio. The Terms make this clear; your posts should too.
- Don't promote on Reddit subs where you haven't posted before. Mods will remove it.
- Don't include UTM-tracked links or anything that looks like marketing automation. Plain URLs only.
