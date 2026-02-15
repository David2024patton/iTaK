"""
iTaK Multi-Model Router - 4-model architecture with fallback chains.
Chat (frontier), Utility (cheap), Browser (vision), Embeddings (local).
Supports dynamic model switching and provider-aware API key injection.
"""

import asyncio
import json
from typing import Any, Callable, Optional

import litellm


class ModelRouter:
    """Routes LLM calls to the appropriate model based on purpose.

    4-model architecture (stolen from Agent Zero):
    - chat: Main reasoning (expensive, powerful)
    - utility: Background tasks (cheap, fast) - summarization, keyword extraction
    - browser: Vision-capable model for browser automation
    - embeddings: Local model for vector search (zero API cost)

    Phase 5 additions:
    - Fallback chains: auto-retry with secondary model on failure
    - Dynamic model switching: change models at runtime
    - Provider API key injection from environment
    """

    def __init__(self, config: dict):
        self.config = config
        self._chat_fallback_models: list[str] = []

        if "chat" in config or "utility" in config or "browser" in config:
            self._chat_config = config.get("chat", {})
            self._utility_config = config.get("utility", {})
            self._browser_config = config.get("browser", {})
            self._embeddings_config = config.get("embeddings", {})
            self.default_model = self._chat_config.get("model", "gemini/gemini-2.0-flash")
        else:
            router_cfg = config.get("router", {})
            model_map = config.get("models", {})
            default_model_name = router_cfg.get("default", "gemini/gemini-2.0-flash")
            self.default_model = default_model_name
            default_entry = model_map.get(default_model_name, {})
            self._chat_config = {
                **default_entry,
                "model": default_entry.get("model", default_model_name),
            }
            self._utility_config = self._chat_config.copy()
            self._browser_config = self._chat_config.copy()
            self._embeddings_config = config.get("embeddings", {})
            self._chat_fallback_models = [
                model_map.get(name, {}).get("model", name)
                for name in router_cfg.get("fallback", [])
            ]

        # Fallback models (tried if primary fails)
        self._fallbacks = config.get("fallbacks", {})

        # Cache for FastEmbed model instance to avoid repeated loading
        self._fastembed_cache: dict[str, Any] = {}

        # Disable litellm logging noise
        litellm.suppress_debug_info = True

        # Inject API keys from env
        self._inject_api_keys()

    async def chat(
        self,
        messages: list[dict],
        stream_callback: Optional[Callable] = None,
        **kwargs,
    ) -> str:
        """Call the main chat model for reasoning."""
        return await self._call_model(self._chat_config, messages, stream_callback, **kwargs)

    async def utility(
        self,
        messages: list[dict],
        **kwargs,
    ) -> str:
        """Call the utility model for cheap background tasks."""
        return await self._call_model(self._utility_config, messages, **kwargs)

    async def browser(
        self,
        messages: list[dict],
        **kwargs,
    ) -> str:
        """Call the browser model (vision-capable) for web automation."""
        return await self._call_model(self._browser_config, messages, **kwargs)

    async def embed(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings using the configured embedding model.

        Uses FastEmbed for local inference (zero API cost).
        Falls back to LiteLLM embedding API if configured.
        """
        provider = self._embeddings_config.get("provider", "fastembed")
        model = self._embeddings_config.get("model", "BAAI/bge-small-en-v1.5")

        if provider == "fastembed":
            return await self._fastembed(texts, model)
        else:
            # Use LiteLLM for API-based embeddings
            response = await litellm.aembedding(
                model=model,
                input=texts,
            )
            return [item["embedding"] for item in response.data]

    async def _fastembed(self, texts: list[str], model: str) -> list[list[float]]:
        """Run FastEmbed locally for zero-cost embeddings."""
        from fastembed import TextEmbedding

        # Check cache for existing model instance
        if model not in self._fastembed_cache:
            self._fastembed_cache[model] = TextEmbedding(model_name=model)
        
        embedding_model = self._fastembed_cache[model]
        embeddings = list(embedding_model.embed(texts))
        return [emb.tolist() for emb in embeddings]

    async def _call_model(
        self,
        model_config: dict,
        messages: list[dict],
        stream_callback: Optional[Callable] = None,
        **kwargs,
    ) -> str:
        """Generic model call with optional streaming and fallback."""
        model = model_config.get("model", "gemini/gemini-2.0-flash")
        temperature = model_config.get("temperature", 0.7)
        max_tokens = model_config.get("max_tokens", 4096)

        # Build the list of models to try (primary + fallbacks)
        models_to_try = [model]
        if model == self._chat_config.get("model") and self._chat_fallback_models:
            models_to_try.extend(self._chat_fallback_models)
        fallback_key = model_config.get("fallback_key", "")
        if fallback_key and fallback_key in self._fallbacks:
            models_to_try.extend(self._fallbacks[fallback_key])

        last_error = None
        for try_model in models_to_try:
            call_kwargs = {
                "model": try_model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "stream": stream_callback is not None,
                **kwargs,
            }

            try:
                if stream_callback:
                    response_text = ""
                    response = await litellm.acompletion(**call_kwargs)
                    async for chunk in response:
                        delta = chunk.choices[0].delta.content or ""
                        response_text += delta
                        await stream_callback(delta)
                    return response_text
                else:
                    response = await litellm.acompletion(**call_kwargs)
                    return response.choices[0].message.content or ""
            except Exception as e:
                last_error = e
                # If we have more models to try, continue
                if try_model != models_to_try[-1]:
                    continue

        # All models failed
        raise last_error or Exception("All models failed")

    def count_tokens(self, text: str, model: Optional[str] = None) -> int:
        """Count tokens for a given text."""
        model = model or self._chat_config.get("model", "gpt-4")
        try:
            import tiktoken
            enc = tiktoken.encoding_for_model(model.split("/")[-1])
            return len(enc.encode(text))
        except Exception:
            # Rough estimate: 1 token ≈ 4 chars
            return len(text) // 4

    def set_model(self, role: str, model_name: str):
        """Dynamically switch a model at runtime.

        Args:
            role: 'chat', 'utility', or 'browser'
            model_name: LiteLLM model identifier
        """
        config_map = {
            "chat": self._chat_config,
            "utility": self._utility_config,
            "browser": self._browser_config,
        }
        if role in config_map:
            config_map[role]["model"] = model_name

    def get_models(self) -> dict:
        """Get current model configuration for dashboard."""
        return {
            "chat": self._chat_config.get("model", "N/A"),
            "utility": self._utility_config.get("model", "N/A"),
            "browser": self._browser_config.get("model", "N/A"),
            "embeddings": self._embeddings_config.get("model", "N/A"),
        }

    def calculate_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        """Backward-compatible cost calculator used by legacy tests/integrations."""
        model_cfg = self.config.get("models", {}).get(model, {})
        if not model_cfg and model == self.default_model:
            model_cfg = self._chat_config

        in_rate = float(model_cfg.get("cost_per_1k_input", 0.0) or 0.0)
        out_rate = float(model_cfg.get("cost_per_1k_output", 0.0) or 0.0)
        cost = (max(0, input_tokens) / 1000.0) * in_rate + (max(0, output_tokens) / 1000.0) * out_rate
        return float(cost)

    def _inject_api_keys(self):
        """Inject API keys from environment into litellm."""
        import os
        key_map = {
            "OPENAI_API_KEY": "openai",
            "ANTHROPIC_API_KEY": "anthropic",
            "OPENROUTER_API_KEY": "openrouter",
            "GEMINI_API_KEY": "gemini",
        }
        for env_key, _ in key_map.items():
            val = os.environ.get(env_key)
            if val:
                setattr(litellm, env_key.lower(), val)
