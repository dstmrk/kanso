# Kanso - AI Development Context

> **Purpose**: Essential context for AI-assisted development. Read this at the start of each session.

---

## 🎯 Project Overview

**Kanso** (簡素 - "simplicity") is a **self-hosted personal finance dashboard** that answers one question:

> **"Am I on track?"**

**Not**: Daily transaction tracker, budget enforcer, bank sync app
**Is**: Monthly check-in tool for people who manually track finances and want clarity

**Core Philosophy**:
1. **Simplicity**: 4 key metrics, not 50 categories
2. **Data Ownership**: User controls data (Google Sheets or local SQLite)
3. **Calm Technology**: Insights without anxiety, monthly not daily

---

## 📚 Detailed Context Files

For deep dives, see `.claude/` directory:

| File | When to Read |
|------|--------------|
| [documentation-style.md](.claude/documentation-style.md) | Before writing docs, README, or user-facing content |
| [architecture-principles.md](.claude/architecture-principles.md) | Before adding features or refactoring |
| [project-context.md](.claude/project-context.md) | For full project overview and history |
| [development-guidelines.md](.claude/development-guidelines.md) | Before testing, committing, or CI work |

---

## ⚠️ Critical Rules (Read Every Time!)

### Documentation Style 🎯

**Core Principle**: "Nobody cares about your product. They care about their quality of life improving."

**Super Mario Metaphor**:
- ❌ Don't show the fire flower (the product)
- ✅ Show Mario shooting fireballs (user achieving goals)

**Always Follow**:
```
Problem → Solution → Outcome → Action
```

### ✅ Documentation Dos

1. **Lead with user pain**, not product features
   - ✅ "Where did your money go? See exactly where every euro flows."
   - ❌ "Net worth tracking with stacked bar charts"

2. **Use concrete examples** with real numbers
   - ✅ "Save €400/month from 3 changes"
   - ❌ "Significantly reduce spending"

3. **Show outcomes, not features**
   - ✅ "Answer 'Am I on track?' in 10 seconds"
   - ❌ "Dashboard with KPI cards"

4. **Be honest about limitations**
   - Include "Is Kanso For You?" with explicit ✅/❌

5. **Use "you" language** (second person)
   - ✅ "You'll see your net worth trend"
   - ❌ "Users will see their net worth"

### ❌ Documentation Don'ts

1. **Never mention exact counts** (they go stale)
   - ❌ "322 unit tests", "10 chart types", "5,000 lines of code"
   - ✅ "Comprehensive test coverage", "Multiple chart types"

2. **Never mention non-existent features**
   - ❌ "Multi-currency support" (if not implemented)
   - Rule: If you can't test it right now, don't document it

3. **No jargon without context**
   - ❌ "Smart caching with TTL invalidation"
   - ✅ "Your data refreshes every 24 hours (or manually when you need it)"

4. **No feature lists without benefits**
   - ❌ "• Net worth tracking\n• Dark mode"
   - ✅ "• Answer 'Am I on track?' in 10 seconds\n• Comfortable viewing day or night"

5. **No buzzwords or empty promises**
   - ❌ "Revolutionary AI-powered insights"
   - ✅ "See where your money goes without guessing"

### Documentation Templates

**Feature Description**:
```markdown
### [Benefit Headline]

[User pain point]

**Solution**: [What Kanso reveals]

**Action**: [What user does with this insight]

**Example**:
- Problem: Earn €4k/month, account always near zero
- Solution: Expense breakdown shows 30% food delivery
- Action: Cook more, save €400/month
```

---

## 🏗️ Architecture Essentials

### Layer Structure

```
app/
├── core/       # Utilities (no business logic, no external deps)
├── logic/      # Business logic (pure functions, testable)
├── services/   # External integrations (data fetching)
└── ui/         # User interface (orchestrates, no logic)
```

**Dependency flow**: `ui` → `logic` → `core`, never reversed

### Key Patterns

1. **Async-first**: All I/O must be async (NiceGUI is async-native)
2. **Type hints everywhere**: mypy enforces this
3. **Pure business logic**: `app/logic/` = no side effects, no external calls
4. **Dependency injection**: Pass dependencies, don't instantiate inside functions

### Testing Strategy

```
      /\
     /E2E\      ← Few (~17 tests, critical paths only)
    /------\
   / Unit  \    ← Many (~322 tests, all logic)
  /----------\
```

**What to test**:
- ✅ Business logic, calculations, edge cases
- ✅ Critical user paths (onboarding, dashboard load)
- ❌ UI layout, third-party libraries, styling

---

## 🔄 CI/CD Strategy

**Path Filtering** (saves CI time):

| Files Changed | Tests Run? |
|---------------|------------|
| `app/`, `tests/`, `main.py` | ✅ Yes (unit + lint + E2E if UI) |
| `docs/`, `.claude/`, `README.md` | ❌ No (docs only, skip tests) |
| `static/**` (images) | ❌ Unit no, ✅ E2E yes |

**Why**: Documentation changes don't need code tests (~2-7 min saved)

---

## 📝 Commit Format

**Pattern**: `<type>: <description>`

**Types**: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`

**Examples**:
```
feat: add year-over-year expense comparison chart
fix: handle division by zero in savings ratio
docs: rewrite README with benefit-driven approach
```

---

## 🚀 Current State

**Version**: v0.5.0

**Completed**:
- ✅ Core financial tracking (income, expenses, assets, liabilities)
- ✅ Dashboard with 4 KPIs + 5 charts
- ✅ Google Sheets integration with 24h caching
- ✅ Advanced visualizations (net worth evolution, YoY comparison, merchant breakdown)
- ✅ Benefit-driven documentation
- ✅ Multi-currency support with browser locale auto-detection
- ✅ Dark/light mode

**Next Focus**: v0.6.0 - Data Tables & UI Improvements

**Roadmap** (internal reference): See [ROADMAP.md](./ROADMAP.md) for details
- Note: ROADMAP.md is detailed for internal use, not currently public

---

## 🛠️ Tech Stack

**Core**: Python 3.13, NiceGUI (async), pandas, gspread, ECharts
**Testing**: pytest, Playwright
**Deployment**: Docker, GitHub Actions
**Docs**: MkDocs Material

---

## 🔍 Quick Decision Framework

Before adding code, ask:

1. **Does this serve the core use case?** (Monthly check-ins)
2. **Is this the simplest approach?**
3. **Where does this belong?** (core/logic/services/ui)
4. **Can I test this easily?** (If no, refactor)
5. **Does this have type hints?**
6. **Have I handled errors gracefully?**

Before writing docs, ask:

1. **Did I lead with user pain?**
2. **Did I show concrete outcomes?**
3. **Did I avoid exact counts?**
4. **Did I only mention implemented features?**
5. **Did I include real examples with numbers?**

---

## 🎨 Example: Transform Feature to Benefit

| Feature | Benefit (Use This!) |
|---------|---------------------|
| Net worth tracking | "Am I on track?" answered in 10 seconds |
| Year-over-year comparison | Spot lifestyle inflation before it compounds |
| Merchant breakdown | "I didn't realize I spend that much there" moments |
| Dark mode | Comfortable viewing day or night |
| Self-hosted | Your data never leaves your control |

---

## 📖 Target User

### ✅ Kanso is For:
- Already tracks finances manually (wants better insights)
- Prefers monthly reviews (not daily tracking)
- Values data ownership and self-hosting
- Comfortable running Docker

### ❌ Kanso is NOT For:
- Needs automatic bank sync (we don't connect to banks)
- Wants envelope budgeting (we don't enforce budgets)
- Expects set-and-forget automation (requires manual data entry)

---

## 💡 When in Doubt

- **Documentation**: Read [.claude/documentation-style.md](.claude/documentation-style.md)
- **Architecture**: Read [.claude/architecture-principles.md](.claude/architecture-principles.md)
- **Testing/CI**: Read [.claude/development-guidelines.md](.claude/development-guidelines.md)
- **Project History**: Read [.claude/project-context.md](.claude/project-context.md)

---

**Remember**: Simplicity first. User outcomes over product features. Monthly clarity, not daily anxiety.

_This file is read automatically at session start. Update when fundamental aspects change._
