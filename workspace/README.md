# Research workspace (workspace 4)

Goal: Perplexity and Gemini side by side on one dedicated workspace, with separate logins.

## Setup
1. `chmod +x workspace/research-workspace.sh`
2. Run it. Log in to each app once; sessions persist in `~/.local/share/research-profiles/`.
3. Pin windows with `hyprland-research.conf.template` (see comments inside).
4. Use Super+4 to jump to the workspace.

## Not yet verified
- The exact `omarchy-launch-webapp` flag passing and the window classes depend on your Omarchy and Hyprland versions. Test on the machine and adjust.
- Saved window positions (Quattro) are a manual step after the first layout.

## Done when
Super+4 shows both apps and logins persist separately (issue #1).
