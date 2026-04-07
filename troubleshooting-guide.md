# Agentic Extensions Troubleshooting & Tips Guide

Comprehensive guide for Cline, Kilo, and OpenCode/Oh-My-OpenAgent including common issues, solutions, tips, and community resources.

---

## Part 1: CLINE - Common Issues & Solutions

### Known Issues (2026)

| Issue | Status | Solution |
|-------|--------|----------|
| Extension host slow to stop | Open (#10051) | Disable extension when not in use |
| Freezes on question | Open (#9094) | Restart VSCode, clear cache |
| Hangs on command with no output | Open (#8448) | Add output redirection `> /dev/null 2>&1` |
| CLI not detected on Windows | Open (#9136) | Ensure CLI in PATH, restart VSCode |
| Extension restart loops on SSH | Open (#9248) | Use local VSCode instead |

### Quick Fixes

```bash
# Clear Cline cache
rm -rf ~/.vscode-server/data/User/globalStorage/saoudrizwan.claude-dev/cache/

# Reinstall extension
code --uninstall-extension saudrizwan.claude-dev
code --install-extension saudrizwan.claude-dev

# Check CLI version
cline --version
```

### Tips & Best Practices

1. **Use rules for consistency** - Define coding standards in `.clinerules/`
2. **Conditional rules** - Use `paths:` frontmatter to avoid context bloat
3. **Skills for complex workflows** - Create reusable skills in `.cline/skills/`
4. **Browser automation** - Use for web testing, scraping (VSCode only)
5. **Checkpoint for long tasks** - Cline saves progress automatically

### Community Resources

| Resource | Link |
|----------|------|
| GitHub | https://github.com/cline/cline |
| Reddit | https://www.reddit.com/r/CLine/ |
| Discord | https://discord.gg/cline (unofficial) |
| Discussions | https://github.com/cline/cline/discussions |

### Top Tips from Community

- Use specific prompts - "Create a React component that..." works better than "Create component"
- Checkpoints save your progress - use them for multi-step tasks
- Rules are always loaded - keep them concise
- Skills load on-demand - great for specialized workflows

---

## Part 2: KILO - Common Issues & Solutions

### Known Issues (2026)

| Issue | Status | Solution |
|-------|--------|----------|
| Extension crash | Open (#7187) | Reinstall extension, clear cache |
| Freezes in VSC | Open (#5941) | Disable other extensions, restart |
| IO resource high usage | Open (#7000) | Use .kilocodeignore for large files |
| Crash on upgrade | Open (#6721) | Clear old .kilocode data |

### Quick Fixes

```bash
# Clear Kilo cache
rm -rf ~/.vscode-server/data/User/globalStorage/kilocode.kilo-code/cache/

# Reinstall Kilo
code --uninstall-extension kilocode.kilo-code
code --install-extension kilocode.kilo-code

# Check CLI
kilo --version
kilo config
```

### Tips & Best Practices

1. **MCP servers** - Configure in `.kilo/kilo.jsonc` for external tools
2. **Custom modes** - Create specialized modes for different workflows
3. **Skills** - Use `.kilo/skills/` with EXACT name matching
4. **Global config** - Use `~/.kilo/kilo.jsonc` for cross-project settings
5. **500+ models** - Access via Kilo Gateway

### Community Resources

| Resource | Link |
|----------|------|
| GitHub | https://github.com/Kilo-Org/kilocode |
| Reddit | https://www.reddit.com/r/kilocode/ |
| Docs | https://kilo.ai/docs |
| Blog | https://blog.kilo.ai |

### Top Tips from Community

- Drag Kilo to Secondary Sidebar to see Explorer while working
- Use `/mode` commands to switch between modes
- Configure MCP servers for database/CLI tools
- Skills work across both CLI and extension
- Start new session after adding skills

---

## Part 3: OPENCODE / OH-MY-OPENAGENT - Common Issues & Solutions

### Known Issues (2026)

| Issue | Status | Solution |
|-------|--------|----------|
| Plugin not loading on Windows | Open (#21032) | Check OpenCode version compatibility |
| Agents fail to load on Ubuntu | Open (#3137) | Update to latest version |
| Sub-agent errors | Open (#1224) | Check model availability |
| Model config ignored | Open (#1573) | Ensure model in cache |

### Quick Fixes

```bash
# Run doctor check
bunx oh-my-opencode doctor

# Clear cache
rm -rf ~/.config/opencode/cache/

# Check config
cat oh-my-openagent.jsonc | jq .

# Update plugin
bunx oh-my-openagent update
```

### Tips & Best Practices

1. **Ralph Loop** - Use `/ralph-loop` for continuous development
2. **Categories + Skills** - Combine for specialized agents
3. **Background agents** - Run parallel tasks
4. **tmux integration** - Enable for visual multi-agent
5. **Built-in hooks** - Leverage 30+ hooks for automation

### Community Resources

| Resource | Link |
|----------|------|
| GitHub | https://github.com/code-yeongyu/oh-my-openagent |
| Reddit | https://www.reddit.com/r/opencodeCLI/ |
| Troubleshooting Docs | https://mintlify.com/code-yeongyu/oh-my-opencode/resources/troubleshooting |
| Anomaly Fork | https://github.com/anomalyco/opencode |

### Top Tips from Community

- Use `/init-deep` to generate hierarchical AGENTS.md
- Categories (visual-engineering, deep, quick) auto-select models
- git-master skill for commit analysis
- frontend-ui-ux skill for design
- Use task system for dependencies

---

## Part 4: Unified Troubleshooting Matrix

### All Agents

| Problem | Cline | Kilo | OpenCode |
|---------|-------|------|----------|
| Extension won't load | Reinstall | Reinstall | Update plugin |
| No skills showing | Start new session | Start new session | Check SKILL.md format |
| Model not available | Check API key | Check config | Check fallback chain |
| Slow performance | Disable streaming | Use .kilocodeignore | Use categories |
| Can't connect to API | Check network | Check proxy | Check firewall |

### Reset Commands

```bash
# Cline - full reset
code --uninstall-extension saudrizwan.claude-dev
rm -rf ~/.vscode-server/extensions/saoudrizwan.claude-dev*
rm -rf ~/.vscode-server/data/User/globalStorage/saoudrizwan.claude-dev/
code --install-extension saudrizwan.claude-dev

# Kilo - full reset  
code --uninstall-extension kilocode.kilo-code
rm -rf ~/.vscode-server/extensions/kilocode.kilo-code*
rm -rf ~/.vscode-server/data/User/globalStorage/kilocode.kilo-code/
code --install-extension kilocode.kilo-code

# OpenCode - full reset
rm -rf ~/.config/opencode/
rm -rf ~/.cache/opencode/
```

---

## Part 5: Performance Optimization

### For All Agents

```bash
# Add to .gitignore / .clineignore / .kilocodeignore
node_modules/
dist/
build/
*.log
*.mp4
*.zip
.env.local
```

### Agent-Specific

**Cline:**
- Use conditional rules: only load rules for relevant files
- Disable skills when not needed
- Use checkpoints for long tasks

**Kilo:**
- Use .kilocodeignore aggressively
- Configure MCP timeout appropriately
- Use lightweight models for simple tasks

**OpenCode:**
- Enable tmux only when needed
- Use categories instead of full agents
- Disable unused hooks

---

## Part 6: Feature Comparison Summary

| Feature | Cline | Kilo | OpenCode |
|---------|-------|------|----------|
| Skills | ✅ | ✅ | ✅ |
| Rules | ✅ | ✅ | ✅ |
| Commands | ✅ | ✅ | ✅ |
| Hooks | ✅ | ❌ | ✅ (30+) |
| MCP Servers | ✅ | ✅ | ✅ |
| Task System | ❌ | ❌ | ✅ |
| Multiple Agents | ❌ | ❌ | ✅ (11) |
| Categories | ❌ | ✅ | ✅ |
| Background Agents | ❌ | ❌ | ✅ |
| Browser Automation | ✅ (Puppeteer) | ❌ | ✅ (Playwright) |
| Models | 100+ | 500+ | 100+ |

---

## Part 7: When to Use Each

### Use Cline When:
- You want browser automation in VSCode
- You need GitHub/Claude API integration
- You prefer simple, straightforward setup
- You use Cursor or Windsurf rules

### Use Kilo When:
- You want 500+ models via Kilo Gateway
- You need MCP server integration
- You want custom modes
- You're migrating from OpenCode

### Use OpenCode/OMO When:
- You need 11 specialized agents
- You want advanced hooks (30+)
- You need task system with dependencies
- You want background agents
- You're doing complex multi-agent workflows

---

## Part 8: Community & Learning Resources

### Cline
- **Medium Guide**: https://medium.com/@ravisat/cline-for-developers-the-practical-guide
- **Best Practices**: https://localskills.sh/blog/cline-rules-guide
- **YouTube**: Search "Cline AI coding tutorial 2026"

### Kilo
- **Official Tips**: https://kilocode.ai/docs/tips-and-tricks
- **Reddit**: https://www.reddit.com/r/kilocode/comments/1pcgp6f/
- **Blog**: https://blog.kilo.ai

### OpenCode/Oh-My-OpenAgent
- **Troubleshooting**: https://mintlify.com/code-yeongyu/oh-my-opencode/resources/troubleshooting
- **Agents Guide**: https://www.glukhov.org/ai-devtools/opencode/oh-my-opencode-agents/
- **Reddit**: https://www.reddit.com/r/opencodeCLI/
- **Fork with extras**: https://github.com/opensoft/oh-my-opencode

---

*Generated: 2026-04-06*
*Sources: GitHub Issues, Reddit, Official Docs, Community Discussions*
