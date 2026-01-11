# Track Spec: Implement a Web-Based GUI with Brutalist Aesthetics

## Overview
This track focuses on building the foundational web interface for the EPUB to Audiobook/Video converter. It will serve as the primary control center for users to upload EPUBs, configure conversion settings, preview voices, and monitor project status.

## Architectural Design

### Backend (FastAPI)
- **Framework:** FastAPI for high-performance, asynchronous API endpoints.
- **Endpoints:**
    - `POST /api/projects`: Initialize a new conversion project from an EPUB.
    - `GET /api/projects`: List all active and archived projects.
    - `GET /api/projects/{id}`: Detailed status and metadata for a specific project.
    - `POST /api/tts/preview`: Generate and return a short audio preview for a selected voice/text.
- **Integration:** Bridges the GUI with the existing `core/` and `features/` logic.

### Frontend (React + Tailwind CSS)
- **Framework:** React.js (Vite-based) for a fast, modern development experience.
- **Styling:** Tailwind CSS implementing the **Brutalist Precision** theme.
    - Monochromatic palette (B&W) with Blue accents.
    - Asymmetrical grid layouts.
    - Bold, oversized typography.
    - Interactive hover effects and micro-interactions.

## Design Goals
- **Immersive Hero Section:** Full-screen landing area with video background support.
- **Efficiency:** Technical, data-dense project dashboards.
- **Artstation Polish:** Clean but structurally daring visual style.

## Acceptance Criteria
- [ ] Users can see a list of existing projects in the Brutalist UI.
- [ ] Users can trigger a voice preview and hear the audio.
- [ ] Technical error logs are visible in the UI for failed tasks.
- [ ] Responsive design that works on desktop and mobile.
