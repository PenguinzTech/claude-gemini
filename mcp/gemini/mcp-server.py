#!/usr/bin/env python3
"""Gemini MCP Server — wraps the local Gemini CLI and google-genai SDK."""
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

# Ensure venv packages are importable when run directly
_venv = Path(__file__).resolve().parent / ".venv" / "lib"
if _venv.exists():
    for _p in _venv.iterdir():
        _site = _p / "site-packages"
        if _site.exists() and str(_site) not in sys.path:
            sys.path.insert(0, str(_site))

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("gemini")

OUTPUT_DIR = Path(os.environ.get("GEMINI_OUTPUT_DIR", Path.home() / "Downloads" / "gemini-output"))
DEFAULT_MODEL = os.environ.get("GEMINI_CLI_MODEL", "gemini-2.0-flash")
SDK_MODEL_TEXT = os.environ.get("GEMINI_SDK_MODEL", "gemini-2.0-flash")
DEFAULT_GEMINI_IMAGE_MODEL = os.environ.get("GEMINI_IMAGE_MODEL", "gemini-2.5-flash-image")
DEFAULT_IMAGEN_MODEL = os.environ.get("IMAGEN_MODEL", "imagen-4.0-generate-001")
DEFAULT_VEO_MODEL = os.environ.get("VEO_MODEL", "veo-3.0-generate-001")
DEFAULT_MUSIC_MODEL = os.environ.get("MUSIC_MODEL", "lyria-3-pro-preview")


def _gemini_cli(prompt: str, timeout: int = 120) -> str:
    """Run gemini CLI subprocess and return output."""
    gemini_bin = shutil.which("gemini")
    if not gemini_bin:
        return "Error: gemini CLI not found. Install with: npm install -g @google/gemini-cli"
    try:
        result = subprocess.run(
            [gemini_bin, "-p", prompt, "--model", DEFAULT_MODEL],
            capture_output=True,
            text=True,
            timeout=timeout,
            env={**os.environ},
        )
        output = result.stdout.strip()
        if not output and result.stderr.strip():
            output = result.stderr.strip()
        return output or "No response received from Gemini."
    except subprocess.TimeoutExpired:
        return f"Error: Gemini CLI timed out after {timeout}s."
    except Exception as e:
        return f"Error running Gemini CLI: {e}"


def _sdk_client():
    """Return a google-genai Client. Raises RuntimeError if GEMINI_API_KEY missing."""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY environment variable not set. "
            "Get a key at https://aistudio.google.com/apikey and set it in your shell profile."
        )
    try:
        from google import genai
        return genai.Client(api_key=api_key)
    except ImportError:
        raise RuntimeError("google-genai not installed in venv. Run: uv pip install google-genai --python .venv/bin/python")


# ---------------------------------------------------------------------------
# CLI-backed tools (text/reasoning)
# ---------------------------------------------------------------------------

@mcp.tool()
def gemini_research(topic: str, depth: str = "comprehensive") -> str:
    """
    Research a topic using Gemini with Google Search grounding.

    Args:
        topic: The topic or question to research.
        depth: Research depth — "brief", "comprehensive", or "deep". Defaults to "comprehensive".
    """
    depth_instructions = {
        "brief": "Provide a concise 2-3 paragraph summary",
        "comprehensive": "Provide a thorough research summary with key findings, context, and recent developments",
        "deep": "Provide an exhaustive deep-dive analysis with multiple perspectives, historical context, recent developments, key players, and actionable insights",
    }
    instruction = depth_instructions.get(depth, depth_instructions["comprehensive"])
    prompt = (
        f"Using Google Search, research the following topic and {instruction}. "
        f"Cite sources where possible and highlight the most important findings.\n\n"
        f"Topic: {topic}"
    )
    return _gemini_cli(prompt, timeout=180)


@mcp.tool()
def gemini_prompt(prompt: str, system_context: str = "") -> str:
    """
    Send an arbitrary prompt to Gemini.

    Args:
        prompt: The prompt to send to Gemini.
        system_context: Optional context or role instructions prepended to the prompt.
    """
    full_prompt = f"{system_context}\n\n{prompt}".strip() if system_context else prompt
    return _gemini_cli(full_prompt)


@mcp.tool()
def gemini_second_opinion(
    question: str,
    context: str = "",
    perspective: str = "critical",
) -> str:
    """
    Get Gemini's perspective as a second opinion — useful for validating decisions,
    code architecture, debugging approaches, or any problem where an independent view helps.

    Args:
        question: The question, decision, or problem to evaluate.
        context: Optional context (e.g., existing solution, code snippet, constraints).
        perspective: "critical" (find flaws), "balanced" (pros/cons), or "alternative" (suggest different approach).
    """
    perspective_instructions = {
        "critical": "Critically evaluate this from first principles. Identify flaws, risks, edge cases, and what could go wrong. Be direct.",
        "balanced": "Give a balanced assessment with pros, cons, trade-offs, and conditions under which this is or isn't a good idea.",
        "alternative": "Propose alternative approaches that might work better, explaining the reasoning and trade-offs vs the described approach.",
    }
    instruction = perspective_instructions.get(perspective, perspective_instructions["critical"])
    prompt = (
        f"Second opinion request — {instruction}\n\n"
        f"Question/Decision: {question}"
        + (f"\n\nContext/Current approach:\n{context}" if context else "")
    )
    return _gemini_cli(prompt, timeout=90)


@mcp.tool()
def gemini_analyze(content: str, question: str) -> str:
    """
    Analyze text content (code, documents, data, logs) with a specific question.

    Args:
        content: The content to analyze (code, text, data, error logs, etc.).
        question: What to analyze or extract from the content.
    """
    prompt = f"{question}\n\n---\n{content}"
    return _gemini_cli(prompt, timeout=120)


# ---------------------------------------------------------------------------
# SDK-backed tools (media generation)
# ---------------------------------------------------------------------------

@mcp.tool()
def gemini_generate_image(description: str, output_filename: str = "", model: str = "") -> str:
    """
    Generate an image using the Gemini API.
    Tries Gemini native image model first (gemini-2.5-flash-image), falls back to Imagen.
    Requires GEMINI_API_KEY environment variable.

    Args:
        description: Detailed description of the image to generate.
        output_filename: Optional filename (without extension). Defaults to timestamped name.
        model: Model override. Defaults to GEMINI_IMAGE_MODEL env var or 'gemini-2.5-flash-image'.
               To force Imagen, pass e.g. 'imagen-4.0-generate-001'.
               Options: 'gemini-2.5-flash-image', 'gemini-3-pro-image-preview',
                        'imagen-4.0-generate-001', 'imagen-4.0-ultra-generate-001', etc.
    """
    try:
        client = _sdk_client()
        from google.genai import types as genai_types

        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        filename = output_filename or f"image_{int(time.time())}"
        out_path = OUTPUT_DIR / f"{filename}.png"

        # Determine whether caller forced a specific model
        forced_model = model or ""
        use_gemini_native = not forced_model or "gemini" in forced_model.lower()
        use_imagen = not forced_model or "imagen" in forced_model.lower()

        gemini_model = forced_model if forced_model and "gemini" in forced_model.lower() else DEFAULT_GEMINI_IMAGE_MODEL
        imagen_model = forced_model if forced_model and "imagen" in forced_model.lower() else DEFAULT_IMAGEN_MODEL

        # --- Attempt 1: Gemini native image generation (generateContent) ---
        if use_gemini_native:
            try:
                result = client.models.generate_content(
                    model=gemini_model,
                    contents=description,
                    config=genai_types.GenerateContentConfig(
                        response_modalities=["IMAGE", "TEXT"],
                    ),
                )
                for part in (result.candidates[0].content.parts if result.candidates else []):
                    if hasattr(part, "inline_data") and part.inline_data:
                        out_path.write_bytes(part.inline_data.data)
                        return f"Image saved to: {out_path} (model: {gemini_model})"
                # No image part returned — fall through to Imagen if not forced
                if not forced_model:
                    pass  # fall through
                else:
                    return "No image was generated. Try a more detailed description."
            except Exception as gemini_err:
                err_str = str(gemini_err)
                # Only fall back to Imagen on access/not-found errors, not content policy
                access_error = any(x in err_str for x in ["NOT_FOUND", "paid plans", "PERMISSION_DENIED", "not supported", "RESOURCE_EXHAUSTED", "free_tier", "quota"])
                if forced_model or not access_error:
                    return f"Image generation failed (model: {gemini_model}): {gemini_err}"
                # else: fall through to Imagen fallback

        # --- Attempt 2: Imagen via generate_images (predict endpoint) ---
        if use_imagen:
            result = client.models.generate_images(
                model=imagen_model,
                prompt=description,
                config=genai_types.GenerateImagesConfig(number_of_images=1),
            )
            if result.generated_images:
                out_path.write_bytes(result.generated_images[0].image.image_bytes)
                return f"Image saved to: {out_path} (model: {imagen_model})"
            return "No image was generated. Try a more detailed description."

        return "No image was generated. Try a more detailed description."
    except RuntimeError as e:
        return f"Configuration error: {e}"
    except Exception as e:
        return f"Image generation failed: {e}"


@mcp.tool()
def gemini_generate_video(description: str, output_filename: str = "", model: str = "") -> str:
    """
    Generate a short video using Veo via the Gemini API.
    Requires GEMINI_API_KEY environment variable. Note: video generation is async and may take 1-3 minutes.

    Args:
        description: Detailed description of the video to generate.
        output_filename: Optional filename (without extension). Defaults to timestamped name.
        model: Veo model to use. Defaults to VEO_MODEL env var or 'veo-2.0-generate-001'.
               Options: 'veo-2.0-generate-001', 'veo-3.0-generate-preview', etc.
    """
    try:
        client = _sdk_client()

        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        filename = output_filename or f"veo_{int(time.time())}"
        out_path = OUTPUT_DIR / f"{filename}.mp4"
        veo_model = model or DEFAULT_VEO_MODEL

        operation = client.models.generate_videos(
            model=veo_model,
            prompt=description,
        )

        # Poll until complete (max 5 minutes)
        max_wait = 300
        waited = 0
        while not operation.done and waited < max_wait:
            time.sleep(15)
            waited += 15
            operation = client.operations.get(operation)

        if not operation.done:
            return f"Video generation timed out after {max_wait}s. Check back later."

        if operation.response and operation.response.generated_videos:
            video = operation.response.generated_videos[0]
            video_bytes = client.files.download(file=video.video)
            out_path.write_bytes(video_bytes)
            return f"Video saved to: {out_path} (model: {veo_model})"
        return "No video was generated. Try a more detailed description."
    except RuntimeError as e:
        return f"Configuration error: {e}"
    except Exception as e:
        return f"Video generation failed (model: {veo_model}): {e}"


@mcp.tool()
def gemini_generate_music(description: str, duration_seconds: int = 30, output_filename: str = "", model: str = "") -> str:
    """
    Generate music or audio using the Gemini API (Lyria/experimental music generation).
    Requires GEMINI_API_KEY environment variable.

    Args:
        description: Description of the music/audio to generate (genre, mood, instruments, tempo, etc.).
        duration_seconds: Approximate duration in seconds (default 30, max 60).
        output_filename: Optional filename (without extension). Defaults to timestamped name.
        model: Music model to use. Defaults to MUSIC_MODEL env var or 'lyria-realtime-exp'.
    """
    try:
        client = _sdk_client()

        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        filename = output_filename or f"music_{int(time.time())}"
        out_path = OUTPUT_DIR / f"{filename}.wav"
        music_model = model or DEFAULT_MUSIC_MODEL

        duration_seconds = min(duration_seconds, 60)
        prompt = (
            f"Generate {duration_seconds} seconds of music/audio: {description}. "
            f"Return the audio as a WAV file."
        )

        result = client.models.generate_content(
            model=music_model,
            contents=prompt,
        )

        # Extract audio bytes from response parts
        audio_bytes = None
        for part in (result.candidates[0].content.parts if result.candidates else []):
            if hasattr(part, "inline_data") and part.inline_data:
                audio_bytes = part.inline_data.data
                break

        if audio_bytes:
            out_path.write_bytes(audio_bytes)
            return f"Audio saved to: {out_path} (model: {music_model})"

        # Fallback: return text description if audio generation not available
        text_response = result.text if hasattr(result, "text") else str(result)
        return (
            f"Note: {music_model} audio generation may not be available on your API tier. "
            f"Model response: {text_response[:500]}"
        )
    except RuntimeError as e:
        return f"Configuration error: {e}"
    except Exception as e:
        return f"Music generation failed (model: {music_model}): {e}"


if __name__ == "__main__":
    mcp.run()
