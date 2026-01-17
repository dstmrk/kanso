# Kanso Roadmap

> **Philosophy**: Kanso stays simple. Features are added only if they serve the core use case: monthly financial check-ins with clarity and calm.

---

## 📍 v1.0.0 - Official Release (CURRENT FOCUS)

**Target**: Q1 2026

**Focus**: Polish, stability, and documentation. All features are implemented.

### To Do

**Polish & Quality:**
- [ ] Bug fixes for any remaining issues
- [x] Error handling improvements
- [x] Consistent loading states

**Testing:**
- [x] E2E coverage on critical user paths
- [x] Edge case handling (empty data, invalid inputs)

**Documentation:**
- [x] README with clear setup instructions
- [x] User guide
- [x] Troubleshooting guide

**Deployment:**
- [x] Docker image optimization
- [x] Publish to Docker Hub (ghcr.io)

---

## ✅ v1.0 Feature Set

| Category | Features |
|----------|----------|
| **Data Source** | Google Sheets (service account) |
| **Dashboard** | 4 KPI cards + 5 interactive charts |
| **Tables** | AG Grid with sorting, filtering, CSV export |
| **Quick Add** | Expense entry form with auto-complete |
| **Currencies** | 10 major currencies with locale formatting |
| **Themes** | Light/dark mode |
| **Mobile** | Responsive UI (tables desktop-only) |

---

## 🎯 v1.x - Post-Release

Features prioritized based on user feedback after v1.0 launch.

### Data Entry
- Quick Add Income form
- Inline editing in AG Grid tables
- Delete rows from UI
- Undo last change

### Import/Export
- CSV import with drag & drop
- Column mapping interface
- Import preview

### Alternative Storage
- SQLite mode (zero-config local storage)
- Storage mode switching with data migration

### Extended Currencies
- 30 most-traded currencies
- Currency search in onboarding

---

## 🚀 v2.0 - Future Vision

To be validated with user feedback:

- Multi-user support / household sharing
- Hosted SaaS option
- Plugin system
- Multi-language support (i18n)
- Bank sync integrations

---

## 🅿️ Parking Lot

Ideas to consider based on user demand:

### Visualizations
- **Heatmap Spese**: Mesi × Categorie, intensità colore per importo speso
- **Bar Race Chart**: Animated asset evolution over time showing ranking changes (ECharts timeline)

### Features
- Goals & savings targets
- Budget tracking per category
- Recurring transaction detection
- AI-powered categorization
- Native mobile apps
- PDF report generation

---

## 🎯 Design Principles

1. **Simplicity First**: Features must serve the core use case
2. **Your Data, Your Control**: Self-hosted, Google Sheets = your data
3. **Calm Technology**: Monthly check-ins, not daily anxiety

---

_Last updated: January 2026 | Current: v0.7.0 | Next: v1.0.0_
