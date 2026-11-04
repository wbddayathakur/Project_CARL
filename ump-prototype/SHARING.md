# Sharing the prototype

The deliverable is one self-contained HTML file. React is inlined, it makes no
network calls, and it needs no build step, no server and no install. That is the
whole point of the format: it runs in anyone's browser without anyone else's
environment.

## How to distribute it

Upload the file to SharePoint or a Teams channel and share the **link to the file**,
not the file as an email attachment — many mail gateways strip or quarantine `.html`
attachments. A SharePoint link also inherits your tenant's permissions, so access
control is handled for you.

Name it with a date on upload, e.g. `UMP-Prototype-r1-2026-09-11.html`. Files get
forwarded, and without a date in the name you cannot tell which round someone is
looking at when they give you feedback.

## What to tell recipients

SharePoint will **not** run the file in its preview pane — it serves `.html` as a
download rather than executing it. So the instruction is always two steps:

1. Download the file.
2. Double-click it. It opens in your default browser.

Chrome, Edge and Safari all work. Nothing loads from the internet, so it works
offline and on a plane.

## Where to point them first

- **How the desk works** — the flow diagrams. Start here for the shape of the system.
- **Load the worked example** at the bottom of the left rail — replays the decisions a
  planner would have made up to a chosen phase, leaving that phase to be done. This is
  the fastest way to see the thing working rather than empty.
- **Tide — Global Summer** — the plan itself, through all five phases.

If you want to send someone to a specific screen, the URL hash works on a local file
too: append `#plan/discovery/worked` to the `file://` path in the address bar. Useful
in a live walkthrough; too fragile to paste into a message.

## Before it goes wider

The data is synthetic and internally consistent — CPMs, avails, universes and
sell-out rates are anchored to public market ranges, not to WBD's actual book. The
*design* is not synthetic: the personas, tenets, agent architecture, handoff gates and
the way P&I's yield position is represented all derive from internal UMP documents.

Treat it as internal-only. It should not go on a public URL, an unauthenticated host,
or any third-party service, because a public link is readable by anyone who has it and
the content amounts to a design brief for an unreleased product.

If you later want a real URL instead of a file, the route that preserves this is
Azure Static Web Apps or App Service with Entra ID authentication restricted to the
WBD tenant. GitHub Pages cannot serve this privately from a personal account, and a
shared password on a third-party host is not the same thing as "WBD employees".
