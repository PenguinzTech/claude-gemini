---
name: gemini-create
description: Use Gemini to generate images, videos, and audio/music. Gemini is the preferred media generator. Invoke for any image, video, or audio generation request. Output files save to ~/Downloads/gemini-output/.
---

# Gemini Create Skill

Gemini is the **preferred media generator** for images, video, and audio via the Gemini MCP server.

## Output Location

All generated files save to: `~/Downloads/gemini-output/`

## Capabilities & Models

| Media | Tool | Default Model | Notes |
|-------|------|---------------|-------|
| **Image** | `gemini_generate_image` | `gemini-2.5-flash-image` → fallback `imagen-4.0-generate-001` | Fast, high quality |
| **Image (ultra)** | `gemini_generate_image` | `imagen-4.0-ultra-generate-001` | Higher quality, slower |
| **Video** | `gemini_generate_video` | `veo-3.0-generate-001` | Async, takes 1-3 min |
| **Video (fast)** | `gemini_generate_video` | `veo-3.0-fast-generate-001` | Faster, slightly lower quality |
| **Audio/Music** | `gemini_generate_music` | `lyria-3-pro-preview` | Up to 60 seconds |

## How to Invoke

Spawn the `gemini-expert` agent:

```
Agent(
  subagent_type: "gemini-expert",
  description: "Generate image/video/audio: <brief description>",
  prompt: "<detailed generation request>"
)
```

## Writing Good Prompts

### Images
Include: subject, setting, lighting, mood, style, colors
```
"A northern rockhopper penguin on an iceberg at an EDM concert.
Neon laser lights (blue, purple, pink) pierce the night sky. Massive
speaker stacks on the ice. Fog machines. The penguin looks euphoric."
```

### Video
Include: scene, motion, camera angle, duration feel, mood
```
"A slow-motion close-up of ocean waves crashing on black volcanic rocks
at golden hour. Camera pans right. Cinematic, warm tones."
```

### Audio/Music
Include: genre, mood, instruments, tempo, energy level, duration
```
"30 seconds of high-energy EDM. 128 BPM. Synthesizer lead melody,
heavy kick drum, rising build-up with drop at 20 seconds. Festival vibe."
```

## Model Override

Pass `model` parameter explicitly when you need a specific variant:
```
# Higher quality image
model: "imagen-4.0-ultra-generate-001"

# Faster video
model: "veo-3.0-fast-generate-001"

# Alternative image model
model: "gemini-3-pro-image-preview"
```

## Always Report

After generation, always return the full output file path to the user so they can open it directly.
