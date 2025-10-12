# Laakhay TA - Documentation Index

**Last Updated**: October 12, 2025

---

## 📚 Documentation Overview

This repository contains comprehensive documentation for the `laakhay-ta` project, a stateless technical analysis engine for cryptocurrency markets.

### Core Documents

1. **[ARCHITECTURE.md](./ARCHITECTURE.md)** - Technical Specification

   - System design and architectural principles
   - Core contracts and interfaces (API specifications)
   - Data models and type system
   - Execution flow and operational model
   - Testing strategy and error handling
   - ~450 lines of concise technical documentation
2. **[PLANS.md](./PLANS.md)** - Implementation Roadmap (includes status)

   - **Current Status** at top (30% complete, what's done/blocked)
   - Commit-by-commit implementation plan (6 phases)
   - Detailed code examples for each commit
   - Testing strategies and git workflow
   - ~350 lines combining status + plans
3. **[CONTRIBUTING.md](./CONTRIBUTING.md)** - Contributor Guide

   - Quick setup and workflow
   - Core architecture (30-second version)
   - Non-negotiable rules (stateless, deterministic, type-safe)
   - Indicator template with tests
   - Commit format and code style
   - Common pitfalls
   - ~310 lines of focused technical guidance
4. **[README.md](./README.md)** - User-Facing Guide

   - Philosophy and quick start
   - Data models and basic usage
   - Installation instructions
   - Examples and use cases
5. **[MIGRATION.md](./MIGRATION.md)** - Data-Source Agnosticism

   - Breaking changes from legacy structure
   - Import path updates
   - Migration guide for existing code
6. **[QUICKREF.md](./QUICKREF.md)** - Quick Reference Card

   - Current state and priorities
   - Core architecture (30-second version)
   - Essential commands and templates
   - Common pitfalls

---

## 🎯 Quick Navigation

### For Developers Starting Work

**Read First**:

1. [CONTRIBUTING.md](./CONTRIBUTING.md) - Development guide (setup, workflow, guidelines)
2. [PLANS.md](./PLANS.md) - Current status (30% complete) + roadmap
3. [ARCHITECTURE.md](./ARCHITECTURE.md) - Learn the design

**Then**:

- Follow CONTRIBUTING.md for setup and workflow
- Start Phase 1 in PLANS.md (Testing Infrastructure)
- Proceed to Phase 2 (Planner Implementation - CRITICAL PATH)
- Follow Phase 3 in PLANS.md (Core Indicators)

### For Architects & Technical Leads

**Read**:

1. [ARCHITECTURE.md](./ARCHITECTURE.md) - Deep dive into design decisions
2. [PLANS.md](./PLANS.md) - Understand implementation strategy & status

**Focus**:

- Architectural tenets (stateless, deterministic, composable)
- Dependency model (DAG, WindowSpec)
- Performance and security considerations

### For Project Managers & Stakeholders

**Read**:

1. [PLANS.md](./PLANS.md) - Status summary + timeline (top section)
2. [README.md](./README.md) - Project overview and goals

**Key Metrics**:

- Current: 30% complete (contracts done, planner + indicators pending)
- Critical path: Phase 2 (Planner) blocks everything
- Timeline: 4-6 weeks to v0.1.0

### For End Users

**Read**:

1. [README.md](./README.md) - Philosophy and quick start
2. Wait for Phase 3 completion (indicators) before using

**Note**: Library is **not yet usable** (30% complete). Core indicators need implementation.

---

## 📊 Project Status at a Glance

| Component            | Status          | Progress | Blocker?      |
| -------------------- | --------------- | -------- | ------------- |
| Core Contracts       | ✅ Complete     | 100%     | -             |
| Data Models          | ✅ Complete     | 100%     | -             |
| Registry System      | ✅ Complete     | 100%     | -             |
| Utilities            | ✅ Complete     | 100%     | -             |
| **Planner**    | ⚠️ Stub Only  | 10%      | **YES** |
| **Indicators** | ❌ Not Started  | 0%       | **YES** |
| Tests                | ❌ Not Started  | 0%       | YES           |
| Documentation        | ✅ Complete     | 95%      | -             |
| Examples             | ⚠️ Incomplete | 20%      | -             |
| CI/CD                | ❌ Not Started  | 0%       | -             |

**Overall Completion**: ~30%

**Critical Path**: Planner → Indicators → Tests

---

## 🏗️ Architecture Highlights

### Key Design Principles

1. **Stateless by Contract**: No instances, no internal state, no side effects
2. **Deterministic**: Same input → same output, always
3. **Composable**: Indicators declare dependencies; planner resolves DAG
4. **Multi-Asset Ready**: Native support for multiple symbols
5. **No Heavy Dependencies**: Only pydantic; no numpy/pandas

### Core Abstraction

```python
class BaseIndicator(ABC):
    name: ClassVar[str]
  
    @classmethod
    def requirements(cls) -> IndicatorRequirements:
        """Declare dependencies (raw data + upstream indicators)"""
  
    @classmethod
    def compute(cls, input: TAInput, **params) -> TAOutput:
        """Pure computation: no I/O, no mutation, deterministic"""
```

### Data Flow

```
Request → Planner (DAG) → Adapter (fetch) → Executor (compute) → Result
```

---

## 🚀 Getting Started (For Contributors)

### 1. Setup Environment

```bash
cd /Users/sashankneupane/Documents/laakhay/ta

# Create virtual environment
python3.13 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -e ".[dev]"
```

### 2. Read Documentation

```bash
# In order:
cat PLANS.md          # Status + roadmap
cat ARCHITECTURE.md   # Technical design
cat CONTRIBUTING.md   # Workflow & guidelines
```

### 3. Start Phase 1 (Testing)

```bash
# Follow PLANS.md § Phase 1: Foundation & Testing Infrastructure
# Create tests/ directory
mkdir -p tests/{unit/{core,models},integration,property}

# Add conftest.py (see PLANS.md § Commit 1.1)
# Add test_*.py files (see PLANS.md § Commit 1.3)
```

### 4. Run Tests

```bash
# After tests are created:
make test           # Run pytest with coverage
make lint          # Check code style
make type-check    # Run mypy
make ci            # Run all checks
```

---

## 📝 Document Maintenance

### When to Update Each Document

**ARCHITECTURE.md**:

- When adding new contracts or interfaces
- When changing core design decisions
- When adding new data models or specs
- **Owner**: Lead architect

**PLANS.md**:

- When completing a phase/commit
- When adjusting priorities or timeline
- When adding new features to roadmap
- When status changes significantly
- **Owner**: Tech lead / PM

**README.md**:

- When changing user-facing API
- When adding examples
- After major releases
- **Owner**: Developer relations

---

## 🎓 Learning Path

### Beginner (New to Project)

1. Read README.md (philosophy)
2. Skim PLANS.md top section (current status)
3. Read ARCHITECTURE.md § Core Contracts
4. Follow PLANS.md § Phase 1

### Intermediate (Implementing Features)

1. Deep read ARCHITECTURE.md (full spec)
2. Read PLANS.md (specific phase)
3. Write code following templates in PLANS.md

### Advanced (Architectural Changes)

1. Update ARCHITECTURE.md first (design)
2. Update PLANS.md (implementation + status impact)
3. Create RFC if major change

---

## 🔗 Related Documents

- `requirements.txt` - Python dependencies
- `pyproject.toml` - Package configuration
- `makefile` - Build and test commands
- `.github/workflows/` - CI/CD (to be created)

---

## ❓ FAQ

**Q: Can I use laakhay-ta now?**
A: No, it's 30% complete. Core indicators not implemented yet.

**Q: When will it be ready?**
A: MVP in 3-4 weeks, production-ready in 2-3 months (if following PLANS.md).

**Q: What should I work on first?**
A: Phase 1 (Testing Infrastructure) from PLANS.md.

**Q: Do I need to read all documents?**
A: Start with PLANS.md (status at top) → ARCHITECTURE.md § Core Contracts → PLANS.md (your phase).

**Q: How do I contribute?**
A: Follow PLANS.md commit-by-commit. Each commit is a self-contained PR.

---

## 📞 Contact

- **Repository**: `github.com/laakhay/api.laakhay.com`
- **Issues**: GitHub Issues
- **Discussions**: GitHub Discussions

---

**Last Updated**: October 12, 2025
**Documentation Version**: 1.0
**Project Version**: 0.0.1 (pre-release)
