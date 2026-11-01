# ReLoop AI — Frontend Client

The web application for ReLoop AI, built with **Next.js 16 (App Router)**, **React 19**, and **Tailwind CSS v4**. It guides users through multimodal hardware scanning, visual defect inspection, telemetry diagnostics, symptom entry, and interactive circular disposition recommendations.

---

## 🚀 Getting Started

### 1. Prerequisites
- **Node.js**: v18.18+ or v20+
- **Package Manager**: npm, pnpm, or yarn

### 2. Install Dependencies
```bash
cd frontend
npm install
```

### 3. Environment Configuration
Copy `.env.example` to `.env.local`:
```bash
cp .env.example .env.local
```
Configure your environment variables:
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_GOOGLE_CLIENT_ID=
```

### 4. Run Development Server
```bash
npm run dev
```
Open [http://localhost:3000](http://localhost:3000) in your browser.

---

## 📁 Architecture & File Structure

```text
frontend/
├── app/                      # Next.js App Router pages and layout
│   ├── layout.tsx            # Global app layout & provider wrapper
│   ├── page.tsx              # Landing page showcasing the circular economy platform
│   ├── assess-device/        # Step-by-step device assessment workflow
│   ├── engine/               # Decision engine walkthrough & live scoring interface
│   ├── pathways/             # Circular pathways explorer (Repair, Upgrade, Refurbish, etc.)
│   ├── how-it-works/         # Educational walkthrough of the synthesis pipeline
│   └── philosophy/           # Circularity ethos & sustainability standards
├── components/               # Modular UI components
│   ├── assess/               # Workflow steps: Vision inspection, diagnostics, symptoms, results
│   ├── auth/                 # Authentication modal, email OTP, and Google Sign-in
│   ├── engine/               # Interactive pathway scorer visualizer & charts
│   ├── landing/              # Hero, feature highlights, and call-to-actions
│   ├── layout/               # Header, Footer, and Navigation bars
│   ├── providers/            # AuthProvider, AssessmentProvider, and context wrappers
│   └── ui/                   # Reusable UI primitives (buttons, dialogs, badges, inputs)
├── context/                  # React Context definitions (Auth, Assessment state)
├── lib/                      # Utilities, API client bindings, and helpers
├── public/                   # Static assets, branding icons, and favicons
├── types/                    # Shared TypeScript interfaces & API contract models
└── vitest.config.mts         # Unit & component test configuration
```

---

## 🧪 Testing & Linting

Run the test suite using Vitest:
```bash
npm test
```

Run ESLint checks:
```bash
npm run lint
```

Build for production:
```bash
npm run build
```
