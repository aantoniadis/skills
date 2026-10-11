# setup-tools

Discover and prepare tools that help the work you plan to do. Reuse existing
project commands and native host integrations, check a real operation, and
leave useful preparation for later skills.

Setup is optional. Start an investigation directly when existing capabilities
are sufficient; use this skill when reusable preparation or repair would help.

## How it works

1. **Discover.** Read project configuration, scripts, CI, existing instructions,
   and the current host's tools. Select capabilities that fit the work.
2. **Try existing operations.** Run a small relevant operation through the
   interface the next skill will use. Record what worked and its limits.
3. **Prepare gaps and verify.** Reuse existing environments and supported
   setup commands. Perform authorized preparation, then check the affected
   operation. Reuse unchanged successful checks. Optional tools remain optional.
4. **Save locally.** Keep useful commands, environment details, and traps in
   the [local tool record](../skills/TOOL-SETUP.md). Later skills locate it
   themselves and select the operations relevant to their question.

Prompt shape:

```text
/aantoniadis-skills:setup-tools I plan to run explain, plan-change, and pr-review-guide here.
```

## Local storage

The record lives under
`$XDG_STATE_HOME/aantoniadis-skills/projects/<project-key>/tools.md`, defaulting
to `~/.local/state`; [TOOL-SETUP.md](../skills/TOOL-SETUP.md) has the lookup
command and the project-file rules. Setup leaves `CLAUDE.md`, `AGENTS.md`, and
other tracked files unchanged; if a tool needs tracked configuration, setup
reports that and uses an alternative. The record belongs to this user and
checkout; a new machine or moved checkout rediscovers the tools.

## Separate workflow configuration

Matt's original engineering setup configures trackers and domain conventions
and writes project files. It is a separate, explicitly selected workflow;
our setup does not invoke it. See the [combined workflow](workflow.md) when
that project configuration is wanted.

