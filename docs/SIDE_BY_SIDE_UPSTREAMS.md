# Side-by-Side Upstreams (Agent Zero + OpenClaw)

This workspace now supports side-by-side comparisons against both upstreams:

- Agent Zero: https://github.com/frdel/agent-zero
- OpenClaw: https://github.com/openclaw/openclaw

## Folder layout

- iTaK (this repo): `E:/test/iTaK`
- Agent Zero ref: `E:/test/iTaK/references/agent-zero`
- OpenClaw ref: `E:/test/iTaK/references/openclaw`

## One-command setup / refresh

From `E:/test/iTaK`:

```powershell
./tools/side_by_side_upstreams.ps1 -Refresh -Status
```

## Open all three folders quickly

```powershell
./tools/side_by_side_upstreams.ps1 -Open
```

## Useful compare commands

```powershell
code --diff "E:/test/iTaK/webui/server.py" "E:/test/iTaK/references/agent-zero/webui/server.py"
code --diff "E:/test/iTaK/security/ssrf_guard.py" "E:/test/iTaK/references/openclaw/src/security/ssrfGuard.ts"
```

## Recommended workflow

1. Keep iTaK as the working base.
2. Pull latest refs with `-Refresh`.
3. Port changes in small slices (UI sync, backend polling, security, doctor checks).
4. Validate each slice (`doctor`, lint, and targeted runtime checks) before the next.

## Notes

- The historical OpenClaw URL `Secure-Claw/OpenClaw` appears stale; use `openclaw/openclaw`.
- Keep upstream code under `references/` read-only and port via explicit diffs/cherry-picked patterns.
