# Triptych — First Run Onboarding

*This file is read on first conversation with a new user. After completing onboarding, save preferences to CLAUDE.md and delete this file.*

## Welcome

Welcome to Triptych — an AI collaboration environment for hard problems. Before we start working together, I'd like to understand how you work so I can be most helpful.

## Questions to ask the user

1. **What kind of work do you do?** (e.g., physics, mathematics, engineering, data science, biology)

2. **What's your typical workflow?** (e.g., reading papers and deriving, working problem sets, designing experiments, analyzing data)

3. **How much intervention do you want from me while you work?**
   - Only speak up if you see a clear error
   - Flag possible errors and interesting observations
   - Be actively engaged — suggest ideas, ask questions, check my work

4. **What kinds of errors matter most to you?** (e.g., algebra mistakes, conceptual errors, unit mismatches, logical gaps)

5. **Are there specific things you DON'T want me to comment on?**

## After the conversation

Save the user's answers as a "Watcher Preferences" section in CLAUDE.md. Format:

```markdown
## Watcher Preferences

- Domain: [their field]
- Intervention level: [minimal / moderate / active]
- Priority errors: [what they care about]
- Avoid commenting on: [what they don't want flagged]
- Working style notes: [anything else relevant]
```

Then delete this file (`onboard.md`). It should only exist for first-run.
