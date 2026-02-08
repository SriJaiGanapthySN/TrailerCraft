# TrailerCraft: Kollywood AI Trailer Generator

**TrailerCraft** is a generative AI engine that transforms movie synopses into high-impact **Kollywood-style trailer packages**. Built using **Gemini 2.5 Flash** and a custom **Retrieval-Augmented Generation (RAG)** pipeline, the system automates the creation of cinematic trailer assets aligned with the distinctive _Mass_ aesthetic of Tamil cinema.

The platform produces structured, production-ready outputs such as narrative arcs, voice-over scripts, bilingual titles, and cinematic shot lists, making it suitable for direct integration into mobile, web, or backend applications.

---

## Key Capabilities

### 1. Structured Production Output

TrailerCraft generates strongly typed, schema-validated JSON using **Pydantic**, ensuring consistency and reliability across platforms such as Flutter, React, or backend services.

### 2. Kollywood-Specific Narrative Design

The system automatically constructs a **Mass-oriented three-act trailer structure** tailored for Tamil cinema:

- **Act I – The Rise:** Character introduction and emotional grounding
- **Act II – The Conflict:** Escalation, mystery, and threat
- **Act III – The Mass Moment:** Hero elevation, violence, and catharsis

### 3. Bilingual Title Generation

Each trailer package includes multiple impactful title suggestions in both **English** and **Tamil (தமிழ்)**, optimized for theatrical and OTT branding.

### 4. Cinematic Shot Lists

Detailed shot-by-shot breakdowns are generated, including:

- Camera angles and movement
- Visual composition
- Audio cues and background score references

### 5. Style-Aware Knowledge Retrieval

A curated vector database of 1,000+ Tamil films ensures stylistic accuracy by grounding generations in real-world cinema metadata.

### 6. Iterative Director Memory

Conversation history is preserved, allowing creators to refine tone, pacing, and mass moments through natural language feedback.

---

## Technology Stack

- **AI Model:** Google Gemini 2.5 Flash/Groq models
- **Framework:** LangChain (Chains, Prompt Templates, Memory)
- **Data Validation:** Pydantic
- **Vector Database:** ChromaDB
- **Embeddings:** Hugging Face Embeddings

---

## Installation & Setup

### Clone the Repository

```bash
git clone https://github.com/SriJaiGanapthySN/TrailerCraft.git
cd trailercraft
pip install -r requirements.txt
```

## Environment Configuration

Create a `.env` file in the project root and add your Google API key:

```env
GEMINI_API_KEY=your_key_here
```

## Data Initialization

TrailerCraft relies on a Tamil cinema dataset for stylistic grounding.

Ensure the following file is present in the project root:

```text
Tamil_movies_dataset.csv
```

## Usage Example: "Leo" Style Generation

When you provide a synopsis, the AI retrieves similar high-rated action movies from your database to guide the style.

```json
payload = {
    "synopsis": "A mild-mannered cafe owner becomes a local hero, but his past soon catches up with him, forcing him to confront a dangerous drug cartel.",
    "user_instructions": "Make it a Lokesh Kanagaraj style 'Mass' action thriller."
}
```

```json
{
  "titles": [{ "english": "LEO", "tamil": "லியோ" }],
  "music_mood": "Fast-paced percussive beats, heavy synth bass, and a 'Badass' recurring theme.",
  "voice_over": "In a world of silence, his past screams the loudest. When the lion awakens, the forest will tremble...",
  "shot_list": [
    {
      "shot_number": 1,
      "visual": "Low-angle tracking shot of the hero walking through a cafe as the lights flicker.",
      "camera_angle": "Low-angle / Tracking",
      "audio_cue": "Slow, rhythmic heartbeat thumping."
    },
    {
      "shot_number": 2,
      "visual": "Extreme close-up of a bloody chocolate bar on the floor.",
      "camera_angle": "Extreme Close-up",
      "audio_cue": "Sharp, metallic ringing sound."
    },
    {
      "shot_number": 3,
      "visual": "Aerial view of a car chase through the snowy roads of Kashmir.",
      "camera_angle": "Aerial / Drone",
      "audio_cue": "Roaring engine and screeching tires mixed with high-tempo BGM."
    }
  ]
}
```
