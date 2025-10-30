# .claude/ - AI Context Directory

> **Purpose**: This directory contains context files that help AI assistants (like Claude) maintain consistency across development sessions.

---

## Why This Directory Exists

As projects grow and conversations get longer, it's easy to:
- Lose track of architectural decisions
- Forget documentation style guidelines
- Introduce inconsistencies
- Repeat explanations

**Solution**: Maintain written "institutional memory" that AI can reference.

---

## Files in This Directory

### 1. [documentation-style.md](./documentation-style.md) 🎯 **Most Important**

**What**: Comprehensive guide for writing user-facing documentation

**When to read**: Before writing/updating README, docs/, or any user-facing content

**Key principles**:
- Benefit-driven approach (outcomes, not features)
- Super Mario metaphor (show user achieving goals, not the product)
- Before/After/Bridge structure
- Real-world scenarios with concrete examples
- ❌ Never mention exact counts (test numbers, LOC)
- ❌ Never mention non-existent features

---

### 2. [architecture-principles.md](./architecture-principles.md) 🏗️

**What**: Technical design decisions, patterns, and constraints

**When to read**: Before adding features, refactoring, or making architectural changes

**Key principles**:
- Clean architecture (core/logic/services/ui separation)
- Async-first (no blocking I/O)
- Type hints everywhere (mypy enforcement)
- Pure business logic (no side effects in app/logic/)
- Test pyramid (many unit tests, few E2E tests)

---

### 3. [project-context.md](./project-context.md) 📋

**What**: High-level overview of Kanso (philosophy, users, tech stack, current state)

**When to read**: At the start of new sessions or when context is needed

**Covers**:
- What is Kanso? (simplicity-focused financial dashboard)
- Target users (manual trackers, monthly check-ins)
- Tech stack (Python, NiceGUI, pandas, Docker)
- Project structure
- Current version and roadmap position

---

### 4. [development-guidelines.md](./development-guidelines.md) 🛠️

**What**: Day-to-day development practices (testing, commits, workflow)

**When to read**: Before starting development work

**Covers**:
- Setup and daily workflow
- Testing (how to write unit/E2E tests)
- Git workflow (branching, commits, PRs)
- CI/CD (what runs when)
- Common tasks (add chart, add page, refactor)

---

## How to Use These Files

### For AI Assistants (Claude)

**At session start**:
1. Read `project-context.md` for general context
2. Read relevant specific file based on task:
   - Writing docs? → `documentation-style.md`
   - Adding feature? → `architecture-principles.md`
   - Testing/commits? → `development-guidelines.md`

**During conversation**:
- Reference these files when making decisions
- Suggest updates if principles evolve
- Use as guardrails for consistency

### For Human Contributors

**These files are useful for you too!**

- New to the project? Read `project-context.md` first
- Writing docs? Follow `documentation-style.md`
- Contributing code? Check `architecture-principles.md` and `development-guidelines.md`

---

## Maintenance

### When to Update

**Update these files when**:
- Major architectural decisions change
- Documentation approach evolves
- New patterns emerge that should be standardized
- Common mistakes need prevention

**Don't update for**:
- Minor feature additions (those go in code/docs)
- Temporary experiments
- Version number changes

### How to Update

1. **Propose change**: Discuss if significant
2. **Update relevant file**: Make targeted changes
3. **Commit**: `docs: update .claude/architecture-principles.md with new pattern`
4. **Verify**: Ensure consistency with other context files

---

## Relationship to Other Documentation

### .claude/ vs docs/ vs README.md

| Directory | Audience | Purpose |
|-----------|----------|---------|
| `.claude/` | AI assistants + contributors | Internal context, patterns, guardrails |
| `docs/` | End users | User-facing feature guides |
| `README.md` | Users + developers | Project landing page |
| `ROADMAP.md` | Users + contributors | Product roadmap (public) |
| `CONTRIBUTING.md` | Contributors | How to contribute |

**Think of .claude/ as**: The project's "style guide + architecture guide + best practices" consolidated for AI reference.

---

## Benefits of This Approach

### ✅ Consistency
- Documentation follows same style across sessions
- Code follows same patterns
- Decisions are remembered

### ✅ Efficiency
- Less repeated explanations
- Faster onboarding (for AI and humans)
- Clear guidelines prevent back-and-forth

### ✅ Quality
- Standards enforced automatically
- Common pitfalls documented
- Best practices captured

### ✅ Scalability
- Handles growing complexity
- Context doesn't degrade over time
- New contributors have clear guide

---

## Alternative Approaches

### Why not just use code comments?

**Code comments explain "why"** (local decisions).

**.claude/ explains "how"** (project-wide patterns).

Both are needed.

### Why not just use docs/?

**docs/** is for **end users** (how to use Kanso).

**.claude/** is for **developers** (how to build Kanso).

Different audiences, different needs.

### Why not just use CONTRIBUTING.md?

**CONTRIBUTING.md** covers **contribution process** (how to submit PRs).

**.claude/** covers **development philosophy** (how to think about code/docs).

Complementary, not redundant.

---

## Questions?

**"Should I commit .claude/ to git?"**

✅ Yes. These files are **part of the project's institutional knowledge**. They help all contributors (human and AI).

**"Can I suggest changes to these files?"**

✅ Absolutely! Open a PR or discussion. These files evolve as we learn.

**"Do I need to read all files before contributing?"**

⚠️ Skim `project-context.md`, then deep-dive on relevant file for your task.

---

_This directory helps maintain project consistency. Update files as the project evolves._
