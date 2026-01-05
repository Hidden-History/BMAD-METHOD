# BMAD Memory System - Documentation Index

Complete documentation for the BMAD Memory System.

---

## 📚 Documentation Overview

### For Complete Beginners

**Start here if you've never installed anything before:**

1. **[Getting Started (5 Minutes)](./GETTING_STARTED.md)** ⭐ **START HERE**
   - Super simple 3-step installation
   - No technical knowledge required
   - Includes troubleshooting for common issues
   - Perfect for first-timers

### For Experienced Users

**Fast installation and reference:**

2. **[Quick Start Guide](./README.md)**
   - Fast installation (experienced users)
   - Includes Qdrant MCP setup for Claude Code
   - Memory hooks overview
   - CLI tools reference

### For Everyone

**Complete guides:**

3. **[Complete Installation Guide](./COMPLETE_INSTALLATION_GUIDE.md)** 📖 **COMPREHENSIVE**
   - Prerequisites installation (Node, Docker, Python, Git)
   - BMAD Method installation
   - Qdrant MCP server setup (Claude Code)
   - Memory system installation
   - Full verification steps
   - Understanding memory hooks
   - Advanced troubleshooting

4. **[Hooks Reference](./HOOKS_REFERENCE.md)** 🔧 **TECHNICAL**
   - All 5 memory hooks explained
   - When each hook activates
   - Manual usage examples
   - Hook development guide
   - Collection details
   - Environment variables

5. **[Memory Setup Guide](./MEMORY_SETUP.md)** ⚙️ **DETAILED**
   - Manual installation steps
   - Configuration options
   - Architecture details
   - Advanced features

---

## 🎯 Quick Navigation

### Installation Paths

**I'm brand new to this:**
→ [Getting Started](./GETTING_STARTED.md) → Done in 5 minutes!

**I'm experienced with dev tools:**
→ [Quick Start](./README.md) → Fast installation

**I want to understand everything:**
→ [Complete Installation Guide](./COMPLETE_INSTALLATION_GUIDE.md) → Full walkthrough

**I use Claude Code:**
→ [Qdrant MCP Setup](./COMPLETE_INSTALLATION_GUIDE.md#part-2-install-qdrant-mcp-server-claude-code-only) → Direct memory access

### Usage Guides

**How do memory hooks work?**
→ [Hooks Reference](./HOOKS_REFERENCE.md) → All 5 hooks explained

**What can I configure?**
→ [Memory Setup Guide](./MEMORY_SETUP.md#configuration) → All options

**How do I troubleshoot?**
→ [Troubleshooting](./COMPLETE_INSTALLATION_GUIDE.md#troubleshooting) → Common issues

---

## 📖 Documentation by Topic

### Installation & Setup

| Document | Topic | Audience |
|----------|-------|----------|
| [Getting Started](./GETTING_STARTED.md) | 5-minute installation | Beginners |
| [Quick Start](./README.md) | Fast installation | Experienced |
| [Complete Guide](./COMPLETE_INSTALLATION_GUIDE.md) | Full installation | Everyone |
| [Memory Setup](./MEMORY_SETUP.md) | Detailed setup | Advanced |

### Memory Hooks

| Document | Topic | Audience |
|----------|-------|----------|
| [Hooks Reference](./HOOKS_REFERENCE.md) | All hooks explained | Developers |
| [Complete Guide - Hooks](./COMPLETE_INSTALLATION_GUIDE.md#understanding-memory-hooks) | Hook overview | Everyone |
| [Quick Start - Hooks](./README.md#how-memory-works-with-bmad-workflows) | Hook summary | Experienced |

### Claude Code Integration

| Document | Topic | Audience |
|----------|-------|----------|
| [Complete Guide - MCP](./COMPLETE_INSTALLATION_GUIDE.md#part-2-install-qdrant-mcp-server-claude-code-only) | Full MCP setup | Claude Code users |
| [Quick Start - MCP](./README.md#qdrant-mcp-server-claude-code-only) | Fast MCP setup | Experienced Claude users |

### Configuration & Advanced

| Document | Topic | Audience |
|----------|-------|----------|
| [Memory Setup](./MEMORY_SETUP.md) | Configuration options | Advanced users |
| [Hooks Reference - Collections](./HOOKS_REFERENCE.md#collection-details) | Collection structure | Developers |
| [Hooks Reference - Development](./HOOKS_REFERENCE.md#hook-development) | Create custom hooks | Developers |

### Troubleshooting

| Document | Topic | Audience |
|----------|-------|----------|
| [Getting Started - Troubleshooting](./GETTING_STARTED.md#troubleshooting) | Common beginner issues | Beginners |
| [Complete Guide - Troubleshooting](./COMPLETE_INSTALLATION_GUIDE.md#troubleshooting) | All issues | Everyone |
| [Hooks Reference - Debugging](./HOOKS_REFERENCE.md#troubleshooting) | Hook debugging | Developers |

---

## 🚀 Common Tasks

### First Time Installation

1. Read: [Getting Started](./GETTING_STARTED.md)
2. Install: Follow 3-step guide
3. Verify: Check dashboard
4. (Optional) Install Qdrant MCP: [Claude Code setup](./COMPLETE_INSTALLATION_GUIDE.md#part-2-install-qdrant-mcp-server-claude-code-only)

### Understanding How It Works

1. Read: [Complete Guide - How It Works](./COMPLETE_INSTALLATION_GUIDE.md#what-is-the-bmad-memory-system)
2. Learn hooks: [Hooks Reference](./HOOKS_REFERENCE.md#automatic-workflow-hooks)
3. See examples: [Quick Start - Examples](./README.md#how-memory-works-with-bmad-workflows)

### Configuring Memory System

1. Read: [Memory Setup - Configuration](./MEMORY_SETUP.md#configuration)
2. Edit `.env` file
3. Restart services: `docker compose restart`

### Creating Custom Hooks

1. Read: [Hooks Reference - Development](./HOOKS_REFERENCE.md#hook-development)
2. Use hook template
3. Follow best practices
4. Test manually before integration

### Troubleshooting Issues

1. Run: `python3 scripts/memory/health-check.py`
2. Check: [Getting Started - Troubleshooting](./GETTING_STARTED.md#troubleshooting)
3. If still stuck: [Complete Guide - Advanced Troubleshooting](./COMPLETE_INSTALLATION_GUIDE.md#troubleshooting)

---

## 🎓 Learning Path

### Beginner Path

**Day 1: Installation**
1. [Getting Started](./GETTING_STARTED.md) - Install in 5 minutes
2. Run first workflow - Watch memory activate
3. Check dashboard - See memories stored

**Day 2: Understanding**
1. [Quick Start - How It Works](./README.md#how-memory-works-with-bmad-workflows) - Learn the 5 hooks
2. Run more workflows - Observe patterns
3. Search memories - Use CLI tools

**Day 3: Optimization**
1. [Memory Setup - Configuration](./MEMORY_SETUP.md#configuration) - Customize settings
2. [Complete Guide - Hooks](./COMPLETE_INSTALLATION_GUIDE.md#understanding-memory-hooks) - Deep dive
3. Monitor dashboard - Analyze usage

### Advanced Path

**For Developers:**
1. [Hooks Reference](./HOOKS_REFERENCE.md) - Full technical reference
2. [Memory Setup](./MEMORY_SETUP.md) - Architecture & internals
3. [Hook Development](./HOOKS_REFERENCE.md#hook-development) - Create custom hooks

**For Claude Code Power Users:**
1. [Complete Guide - MCP Setup](./COMPLETE_INSTALLATION_GUIDE.md#part-2-install-qdrant-mcp-server-claude-code-only)
2. Use MCP tools in chat
3. Experiment with direct memory access

---

## 📊 Document Comparison

| Feature | Getting Started | Quick Start | Complete Guide | Hooks Reference | Memory Setup |
|---------|----------------|-------------|----------------|-----------------|--------------|
| **Target** | Beginners | Experienced | Everyone | Developers | Advanced |
| **Length** | 5 min | 10 min | 30 min | 20 min | 15 min |
| **Prerequisites** | Basic terminal | Dev tools | All included | Python knowledge | Advanced config |
| **Installation** | ✅ Simple | ✅ Fast | ✅ Detailed | ❌ | ✅ Manual |
| **MCP Setup** | ✅ Basic | ✅ Included | ✅ Complete | ❌ | ❌ |
| **Hooks** | ❌ | ✅ Overview | ✅ Explained | ✅ Complete | ❌ |
| **Troubleshooting** | ✅ Common | ✅ Included | ✅ Advanced | ✅ Debugging | ✅ Configuration |
| **Examples** | ✅ | ✅ | ✅ | ✅ | ❌ |
| **CLI Tools** | ❌ | ✅ | ✅ | ✅ Complete | ✅ |

---

## 🔗 External Resources

### Prerequisites

- **[Docker Desktop Download](https://www.docker.com/products/docker-desktop/)** - Required for Qdrant
- **[Python Download](https://www.python.org/downloads/)** - Required for memory scripts
- **[Node.js Download](https://nodejs.org/)** - Required for BMAD Method
- **[Git Download](https://git-scm.com/)** - Required for version control

### BMAD Method

- **[BMAD Main README](../../README.md)** - BMAD Method overview
- **[BMAD Documentation](../index.md)** - All BMAD docs
- **[Quick Start](../modules/bmm-bmad-method/quick-start.md)** - BMAD workflows

### Tools & Technologies

- **[Qdrant Documentation](https://qdrant.tech/documentation/)** - Vector database docs
- **[Model Context Protocol](https://modelcontextprotocol.io/)** - MCP specification
- **[Sentence Transformers](https://www.sbert.net/)** - Embedding model

### Community

- **[Discord Community](https://discord.gg/gk8jAdXWmj)** - Get help, share projects
- **[GitHub Issues](https://github.com/Hidden-History/BMAD-METHOD/issues)** - Report bugs
- **[YouTube Channel](https://www.youtube.com/@BMadCode)** - Video tutorials

---

## 📝 Document Status

| Document | Version | Last Updated | Status |
|----------|---------|--------------|--------|
| [Getting Started](./GETTING_STARTED.md) | 1.0.0 | 2026-01-05 | ✅ Production |
| [Quick Start](./README.md) | 1.0.0 | 2026-01-05 | ✅ Production |
| [Complete Guide](./COMPLETE_INSTALLATION_GUIDE.md) | 2.0.0 | 2026-01-05 | ✅ Production |
| [Hooks Reference](./HOOKS_REFERENCE.md) | 1.0.0 | 2026-01-05 | ✅ Production |
| [Memory Setup](./MEMORY_SETUP.md) | 1.0.0 | 2026-01-04 | ✅ Production |

---

## 🆘 Need Help?

**Choose your path:**

**"I'm completely stuck and confused"**
→ Start over with [Getting Started](./GETTING_STARTED.md)

**"Installation failed"**
→ Check [Troubleshooting](./COMPLETE_INSTALLATION_GUIDE.md#troubleshooting)

**"Memory hooks not working"**
→ See [Hooks Debugging](./HOOKS_REFERENCE.md#troubleshooting)

**"Need to customize configuration"**
→ Read [Memory Setup - Configuration](./MEMORY_SETUP.md#configuration)

**"Still need help!"**
→ [GitHub Issues](https://github.com/Hidden-History/BMAD-METHOD/issues) or [Discord](https://discord.gg/gk8jAdXWmj)

---

## 📅 Updates & Changelog

**Version 2.0.0 (2026-01-05)**
- ✅ Complete documentation overhaul
- ✅ Added Qdrant MCP setup for Claude Code
- ✅ New Getting Started guide for beginners
- ✅ Comprehensive Hooks Reference
- ✅ Updated all existing guides
- ✅ Added this index document

**Version 1.0.0 (2026-01-04)**
- ✅ Initial memory system release
- ✅ Basic installation guide
- ✅ Memory Setup documentation

---

**Welcome to BMAD Memory System! Choose your guide above and get started.** 🧠

**Created:** 2026-01-05
**Version:** 1.0.0
**Maintainer:** BMAD Code, LLC
