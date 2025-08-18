# FILE: src/openai_rooms_pkg/actions/__init__.py
"""
Actions subpackage initializer.

- Exporte proprement les callables d'actions et leurs modèles d'input.
- Utilise __all__ (et non 'all') pour que les loaders puissent compter les actions.
- Protège les imports pour éviter de casser l'addon si une action est temporairement absente.
"""

__all__ = []

def _register(name: str, input_alias: str):
    __all__.extend([name, input_alias])

# --- chat_completion (⚠️ nom attendu par le workflow) ---
try:
    from .chat_complete import chat_completion, ActionInput as ChatCompletionInput
    _register("chat_completion", "ChatCompletionInput")
except Exception:  # pragma: no cover
    pass

# --- vision_complete ---
try:
    from .vision_complete import vision_complete, ActionInput as VisionCompleteInput
    _register("vision_complete", "VisionCompleteInput")
except Exception:  # pragma: no cover
    pass

# --- image_generate ---
try:
    from .image_generate import image_generate, ActionInput as ImageGenerateInput
    _register("image_generate", "ImageGenerateInput")
except Exception:  # pragma: no cover
    pass

# --- embedding_create ---
try:
    from .embedding_create import embedding_create, ActionInput as EmbeddingCreateInput
    _register("embedding_create", "EmbeddingCreateInput")
except Exception:  # pragma: no cover
    pass

# --- audio_transcribe ---
try:
    from .audio_transcribe import audio_transcribe, ActionInput as AudioTranscribeInput
    _register("audio_transcribe", "AudioTranscribeInput")
except Exception:  # pragma: no cover
    pass

# --- audio_tts ---
try:
    from .audio_tts import audio_tts, ActionInput as AudioTTSInput
    _register("audio_tts", "AudioTTSInput")
except Exception:  # pragma: no cover
    pass
