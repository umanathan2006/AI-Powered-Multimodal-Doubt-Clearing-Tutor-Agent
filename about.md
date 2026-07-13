# AI-Powered Multimodal Doubt-Clearing Tutor

An offline, multimodal tutor agent that answers student doubts from uploaded course material — explaining concepts through multiple teaching styles, generating code-driven simulations instead of static images, and narrating everything through synced audio, packaged as a short explainer video.

## Overview

Traditional study material is static — it can't adapt to how a student learns, and it can't demonstrate a *process*. This project builds a tutor that:

- Understands uploaded lecture notes, textbooks, and reference material
- Accepts questions through text or voice
- Explains answers using multiple pedagogical approaches (analogy, story-based, step-by-step, and more)
- Generates **simulations** (code-driven, animated visuals) rather than static infographics — so processes like scheduling, searching, or memory allocation are actually shown running, not just illustrated
- Narrates explanations as audio, synced to the simulation
- Supports follow-up doubts, reusing prior simulations where possible or regenerating new ones when the topic shifts

Runs fully locally — no proprietary APIs, no cloud dependency.

## Features

- **Context-grounded answers** — responses stay faithful to the uploaded material, not generic knowledge
- **Multiple pedagogy modes** — same answer explained differently depending on student preference (analogy-based, problem-based, step-by-step, story-based, and more)
- **Simulation generation** — algorithms and processes rendered as animated, code-driven visuals instead of static diagrams
- **Narrated explainer output** — simulation and narration combined into a single video-like artifact
- **Follow-up doubt handling** — a routing step decides whether a follow-up needs a brand-new simulation or just new narration over the existing one
- **Fully offline** — designed to run on local hardware with no external API dependency

## Architecture

The system is built as a graph-based pipeline rather than a fixed sequence, so it can branch (e.g. choosing a pedagogy style) and loop (handling follow-up doubts) rather than just running start to finish.

**High-level flow:**

1. Student submits a question (text or voice)
2. Voice input is transcribed to text
3. Relevant context is retrieved from the uploaded material
4. A routing step selects the teaching approach
5. Three things are generated in parallel: the explanation text, a code-driven simulation, and narrated audio
6. Simulation and audio are assembled into a single explainer output
7. On a follow-up doubt, a second routing step decides whether to reuse the existing simulation with fresh narration, or regenerate both simulation and narration from scratch
8. The updated output loops back to step 7 for any further doubts

See `docs/architecture.svg` for the full diagram.

## Project structure

```
.
├── backend/          # API server, retrieval pipeline, generation pipeline
├── frontend/          # Desktop client
├── simulations/       # Templated simulation renderers (per topic type)
├── docs/              # Architecture diagrams, sample sessions, reports
└── README.md
```

## Getting started

```bash
# clone the repo
git clone https://github.com/<your-username>/<repo-name>.git
cd <repo-name>

# backend setup
cd backend
pip install -r requirements.txt
uvicorn main:app --reload

# frontend setup
cd ../frontend
flutter pub get
flutter run -d windows
```

Upload your course material, ask a question through text or voice, and the tutor will generate a grounded explanation with a synced simulation and narration.

## Deliverables

- Working prototype
- Source code
- Architecture documentation
- Sample learning sessions
- Generated simulation samples
- Audio demonstrations
- Resource utilization report
- Performance evaluation report
- Demonstration video

## Roadmap / bonus features

- Multilingual support
- Personalized teaching style per student
- Student knowledge-level adaptation
- Interactive whiteboard
- Learning progress tracking
- Follow-up question auto-generation
- Concept dependency visualization

## License

Specify your license here (e.g. MIT).

## Contributing

Issues and pull requests are welcome. Please open an issue first to discuss significant changes.
