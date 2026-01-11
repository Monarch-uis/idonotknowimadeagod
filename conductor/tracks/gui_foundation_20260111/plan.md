# Track Plan: Implement a Web-Based GUI with Brutalist Aesthetics

## Phase 1: Backend Foundation (FastAPI)

- [~] Task: Initialize FastAPI project structure and core dependencies.
- [ ] Task: Implement `GET /api/health` endpoint with unit tests.
- [ ] Task: Create project management API endpoints (`POST`, `GET` /api/projects).
    - [ ] Write tests for project creation and retrieval.
    - [ ] Implement endpoint logic using existing `ProjectManager` components.
- [ ] Task: Implement TTS preview endpoint (`POST /api/tts/preview`).
    - [ ] Write tests for voice synthesis requests.
    - [ ] Integrate with `core/tts.py`.
- [ ] Task: Conductor - User Manual Verification 'Backend Foundation' (Protocol in workflow.md)

## Phase 2: Frontend Foundation (React + Tailwind)

- [ ] Task: Scaffold React application with Vite and Tailwind CSS.
- [ ] Task: Configure Tailwind with Brutalist theme (B&W palette, custom fonts).
- [ ] Task: Create the Immersive Hero component with video background capability.
    - [ ] Write component unit tests (e.g., Vitest/React Testing Library).
    - [ ] Implement the component with oversized typography.
- [ ] Task: Implement the Project Dashboard grid.
    - [ ] Write tests for project list rendering.
    - [ ] Implement asymmetrical layout and interactive hover effects.
- [ ] Task: Connect Frontend to Backend API.
    - [ ] Write integration tests for API calls.
    - [ ] Implement data fetching and state management.
- [ ] Task: Conductor - User Manual Verification 'Frontend Foundation' (Protocol in workflow.md)

## Phase 3: Polish & Integration

- [ ] Task: Implement technical error logging display in the UI.
- [ ] Task: Optimize for mobile responsiveness and touch interactions.
- [ ] Task: Final end-to-end verification of the conversion trigger flow.
- [ ] Task: Conductor - User Manual Verification 'Polish & Integration' (Protocol in workflow.md)
