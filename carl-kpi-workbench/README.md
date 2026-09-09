# CARL KPI Discovery & Standardization Workbench

React prototype for reviewing MicroStrategy metric candidates and promoting them into a
certified semantic KPI layer. All data in `src/App.jsx` is synthetic sample data.

## Run it

```bash
./start.sh
```

Then open http://localhost:5173.

Node.js is installed at `~/.local/node` and is not on the default `PATH`, so `start.sh`
adds it before running Vite. To use `npm` directly in a terminal, run:

```bash
export PATH="$HOME/.local/node/bin:$PATH"
```

## Other commands

| Command | Purpose |
| --- | --- |
| `npm run dev` | Dev server with hot reload |
| `npm run build` | Production bundle into `dist/` |
| `npm run preview` | Serve the production bundle locally |

## Stack

Vite, React 19, Tailwind CSS 3, framer-motion, recharts, lucide-react, and
shadcn-style primitives in `src/components/ui` (built on Radix) resolved through the
`@/` alias configured in `vite.config.js`.
