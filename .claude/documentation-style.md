# Documentation Style Guide

> **Purpose**: Maintain consistent, benefit-driven documentation across README, docs/, and all user-facing content.

---

## Core Philosophy

**"Nobody cares about your product. They care about their quality of life improving."**

We follow the **Super Mario and Fire Flower** metaphor:
- ❌ Don't show the fire flower (the product)
- ✅ Show Mario shooting fireballs and defeating enemies (the user achieving their goals)

**Translation**: Lead with outcomes users achieve, not features the product has.

---

## Writing Framework

### 1. Jobs-to-be-Done Structure

Every feature description should answer:
- **When I** [situation]
- **I want to** [motivation]
- **So I can** [expected outcome]

**Example**:
- ❌ "Net Worth Tracking with stacked bar charts"
- ✅ "When I wonder if I'm making progress, I want to see my wealth evolution at a glance, so I can feel confident I'm on track"

### 2. Before/After/Bridge Pattern

Always structure explanations as:
1. **Before** (The Pain): Describe user's current frustration
2. **After** (The Outcome): Show the desired state
3. **Bridge** (The Solution): Kanso as the path from pain to outcome

**Example**:
```markdown
### Before Kanso:
- Open 3 spreadsheets to see full picture
- Calculate net worth manually each month
- Feel anxious about money (but can't explain why)

### With Kanso (5 minutes per month):
1. Open dashboard → See net worth trend in 10 seconds
2. Check savings ratio → Green = doing great
3. Make one decision → Cancel subscription or celebrate progress

**Result**: Confidence. Control. Calm.
```

### 3. Real-World Scenarios

Every major feature MUST include concrete examples with:
- **Problem**: Specific, relatable pain point
- **Solution**: What Kanso reveals
- **Action**: What user does with this insight

**Template**:
```markdown
**Scenario: The "Where did it all go?" Mystery**

**Problem**: You earn €4k/month, but account is always near zero.

**Solution**: Kanso's expense breakdown shows:
- 30% food delivery (you didn't realize)
- €200/month subscriptions (you forgot about)
- Spending grew 15% vs last year (lifestyle inflation)

**Action**: Cook more, cancel 3 subscriptions, save €400/month.
```

---

## ✅ Dos

### Lead with User Pain
Start every section with the problem users feel:
```markdown
## The Problem

**You work hard. You earn money. But at the end of the month...**

- 🤔 "Where did it all go?" - Money disappears. You can't pinpoint where.
```

### Use Concrete Numbers
Avoid vague claims. Be specific:
- ✅ "Save €400/month from 3 changes"
- ❌ "Significantly reduce spending"

### Show Outcomes, Not Features
Transform feature lists into user benefits:
- ❌ "Stacked bar chart visualization"
- ✅ "See exactly where your wealth is growing"

### Be Honest About Limitations
Include "Is Kanso For You?" sections with explicit ✅/❌:
```markdown
### ❌ Kanso Might Not Be For You If...
- You need **automatic bank sync** (Kanso doesn't connect to banks)
- You want **envelope budgeting** or strict category limits
```

### Use "You" Language
Write in second person to make it personal:
- ✅ "You'll see your net worth trend in 10 seconds"
- ❌ "Users will see their net worth trend"

### Provide Anti-Patterns
Show what NOT to do:
```markdown
**Don't obsess daily**: Net worth is a long-term metric. Daily checks add stress without value.
```

---

## ❌ Don'ts

### Never Mention Exact Counts
Documentation gets stale fast. Avoid:
- ❌ "322 unit tests" → Changes every commit
- ❌ "10 chart types" → Changes with features
- ❌ "5,000 lines of code" → Meaningless metric

Instead use:
- ✅ "Comprehensive test coverage"
- ✅ "Multiple chart types"
- ✅ "Well-tested codebase"

### Never Mention Non-Existent Features
Only document what's actually implemented:
- ❌ "Multi-currency support" (if not implemented yet)
- ❌ "CSV import" (if in roadmap but not built)

**Rule**: If you can't test it right now, don't document it.

### No Jargon Without Context
Explain technical terms or avoid them:
- ❌ "Smart caching with TTL invalidation"
- ✅ "Your data refreshes every 24 hours (or manually when you need it)"

### No Feature Lists Without Benefits
Never write bullet lists of features alone:
- ❌ "• Net worth tracking\n• Dark mode\n• Dashboard"
- ✅ "• Answer 'Am I on track?' in 10 seconds\n• Comfortable viewing day or night\n• See your full financial picture at a glance"

### No Buzzwords
Avoid marketing fluff:
- ❌ "Revolutionary AI-powered insights"
- ❌ "Next-generation financial platform"
- ✅ "See where your money goes without guessing"

### No Empty Promises
Don't oversell:
- ❌ "Transform your financial life forever!"
- ✅ "Check your financial health in 5 minutes per month"

---

## Content Structure Templates

### README.md Structure
1. **Hero**: Outcome-focused tagline
2. **The Problem**: 4 relatable pain points
3. **The Solution**: Before/After comparison
4. **What You Get**: Benefits (not features)
5. **Quick Start**: Immediate action
6. **How It Works**: Simple flow
7. **Is Kanso For You**: Honest assessment
8. **Features**: Grouped by user benefit
9. **Real-World Use Cases**: 3 scenarios
10. **Tech Stack**: Brief, no buzzwords

### Feature Documentation Structure
1. **Purpose**: One-sentence outcome
2. **Why [Feature]**: The pain point
3. **What You See**: Visual description
4. **How to Read It**: Interpretation guide
5. **Real Examples**: 3+ concrete scenarios
6. **Common Patterns**: What users typically find
7. **How to [Action]**: Actionable steps
8. **Common Questions**: Troubleshooting

### Landing Page Structure (docs/index.md)
1. **Hero**: Tagline + subheadline
2. **The Problem**: Cards with pain points
3. **The Solution**: Before/After
4. **What You Get**: Benefits with links to details
5. **How It Works**: Diagram
6. **Quick Start**: Docker + local options
7. **Is Kanso For You**: ✅/❌ assessment
8. **Real-World Use Cases**: 3 scenarios
9. **Next Steps**: Clear CTAs

---

## Writing Style

### Tone
- **Conversational**: Like explaining to a friend
- **Honest**: Acknowledge limitations
- **Empathetic**: Recognize user's pain
- **Actionable**: Always show next steps
- **Calm**: No urgency manipulation

### Voice
- **Active voice**: "See your net worth" (not "Net worth can be seen")
- **Direct**: Short sentences
- **Personal**: Use "you" and "your"

### Formatting
- **Bold** for emphasis on key outcomes
- `Code` for technical terms
- > Blockquotes for important reminders
- **Examples** liberally throughout
- **Whitespace** for readability

---

## Examples by Type

### ✅ Good: Feature Description
```markdown
### 📊 Answer "Am I on track?" in 10 seconds

Net worth up? ✅ Keep going.
Savings ratio green? ✅ You're doing great.
No spreadsheet archaeology needed.

[:octicons-arrow-right-24: See Dashboard Features](features/dashboard.md)
```

### ❌ Bad: Feature Description
```markdown
### Net Worth Tracking

Kanso provides comprehensive net worth tracking with advanced visualizations including stacked bar charts, line graphs, and KPI cards. Our system calculates your total assets minus liabilities and displays the result with color-coded indicators.
```

---

### ✅ Good: Real-World Scenario
```markdown
**Scenario: The Raise That Disappeared**

**Problem**: Got 10% raise last year. Savings didn't increase. Where did money go?

**Solution**: Year-over-year expense comparison shows:
- Spending also up 10% (lifestyle inflation)
- Dining out doubled (celebrating new income)
- Savings ratio unchanged at 15%

**Action**: Freeze lifestyle. Save 100% of next raise.
```

### ❌ Bad: Feature Explanation
```markdown
Kanso's year-over-year comparison feature allows users to visualize their spending patterns across multiple time periods with forecasting capabilities.
```

---

### ✅ Good: Honest Assessment
```markdown
### ❌ Kanso Might Not Be For You If...

- You need **automatic bank sync** (Kanso doesn't connect to banks)
- You expect **set-and-forget** automation (Kanso requires monthly data entry)

**Honest assessment**: Kanso is for people who manually track finances and want better insights, not for people looking to automate everything.
```

### ❌ Bad: Generic Statement
```markdown
Kanso is perfect for anyone who wants to track their finances and is suitable for users of all experience levels.
```

---

## Content Review Checklist

Before committing documentation, verify:

- [ ] Leads with user pain (not product features)
- [ ] Shows concrete outcomes (not abstract benefits)
- [ ] Includes real-world examples with numbers
- [ ] Uses "you" language (second person)
- [ ] Avoids exact counts (test numbers, LOC, etc.)
- [ ] Only mentions implemented features
- [ ] No jargon without explanation
- [ ] No buzzwords or marketing fluff
- [ ] Honest about limitations
- [ ] Clear next action for reader

---

## Maintenance Guidelines

### When to Update

**Update documentation when**:
- New features are fully implemented
- User workflows change
- Common questions emerge
- Examples become outdated

**Don't update for**:
- Test count changes
- Minor refactoring
- Internal code structure changes
- Dependency updates

### Keeping Examples Fresh

Review scenarios quarterly:
- Are amounts realistic? (€4k/month might be outdated)
- Are pain points still relevant?
- Do examples reflect current UI?

### Consistency Checks

When adding new content:
1. Read existing docs for tone matching
2. Follow structure templates above
3. Use similar example formats
4. Maintain benefit-driven approach throughout

---

## Quick Reference

**Transform features to outcomes**:
| Feature | Outcome |
|---------|---------|
| Net worth tracking | "Am I on track?" answered in 10 seconds |
| Year-over-year comparison | Spot lifestyle inflation before it compounds |
| Merchant breakdown | "I didn't realize I spend that much there" moments |
| Dark mode | Comfortable viewing day or night |
| Self-hosted | Your data never leaves your control |

**Structure reminder**: Problem → Solution → Outcome → Action

---

_This guide is a living document. Update as we learn what resonates with users._
