#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# =============================================================================
# core/trading_agents/llm_router.py — Multi-Model LLM Provider Router
# Connects TradingAgents to Claude, DeepSeek, GPT-4o, and Gemini with zero-lag fallback.
# =============================================================================

import os
import sys
import json
import logging
import urllib.request
import urllib.error
from typing import Dict, List, Any, Optional

logger = logging.getLogger("GEN26.TradingAgents.LLMRouter")


class LLMRouter:
    """
    Multi-Model LLM Provider Router supporting:
    - Google Gemini (Gemini 1.5 Pro / Flash)
    - DeepSeek AI (DeepSeek-V3 / DeepSeek-R1)
    - OpenAI (GPT-4o / GPT-4o-mini)
    - Anthropic (Claude 3.5 Sonnet)
    - Offline Hybrid Deterministic Quant Engine (Instant 0ms Fallback)
    """

    SUPPORTED_PROVIDERS = ["auto", "gemini", "deepseek", "openai", "anthropic", "offline"]

    @classmethod
    def get_provider_status(cls) -> Dict[str, Any]:
        """Detects available API keys in environment."""
        has_gemini = bool(os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY"))
        has_deepseek = bool(os.environ.get("DEEPSEEK_API_KEY"))
        has_openai = bool(os.environ.get("OPENAI_API_KEY"))
        has_anthropic = bool(os.environ.get("ANTHROPIC_API_KEY"))

        active_provider = "offline"
        pref = os.environ.get("TRADING_AGENTS_LLM_PROVIDER", "auto").lower()

        if pref == "gemini" and has_gemini:
            active_provider = "gemini"
        elif pref == "deepseek" and has_deepseek:
            active_provider = "deepseek"
        elif pref == "openai" and has_openai:
            active_provider = "openai"
        elif pref == "anthropic" and has_anthropic:
            active_provider = "anthropic"
        elif pref == "auto":
            if has_deepseek:
                active_provider = "deepseek"
            elif has_gemini:
                active_provider = "gemini"
            elif has_anthropic:
                active_provider = "anthropic"
            elif has_openai:
                active_provider = "openai"

        return {
            "active_provider": active_provider,
            "configured_preference": pref,
            "available_keys": {
                "gemini": has_gemini,
                "deepseek": has_deepseek,
                "openai": has_openai,
                "anthropic": has_anthropic
            },
            "offline_fallback_ready": True
        }

    @classmethod
    def query_llm(
        cls,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.3,
        max_tokens: int = 1200,
        timeout_sec: float = 4.0
    ) -> Optional[str]:
        """
        Sends structured query to active LLM provider.
        Returns text response or None on failure/offline.
        """
        status = cls.get_provider_status()
        provider = status["active_provider"]

        if provider == "offline":
            return None

        try:
            if provider == "deepseek":
                return cls._call_deepseek(system_prompt, user_prompt, temperature, max_tokens, timeout_sec)
            elif provider == "gemini":
                return cls._call_gemini(system_prompt, user_prompt, temperature, max_tokens, timeout_sec)
            elif provider == "openai":
                return cls._call_openai(system_prompt, user_prompt, temperature, max_tokens, timeout_sec)
            elif provider == "anthropic":
                return cls._call_anthropic(system_prompt, user_prompt, temperature, max_tokens, timeout_sec)
        except Exception as e:
            logger.warning(f"LLM Provider {provider} failed ({e}). Reverting to instant deterministic fallback.")
            return None
        return None

    @classmethod
    def _call_deepseek(cls, sys_p: str, usr_p: str, temp: float, max_t: int, timeout: float) -> Optional[str]:
        api_key = os.environ.get("DEEPSEEK_API_KEY", "")
        if not api_key:
            return None
        url = "https://api.deepseek.com/chat/completions"
        payload = {
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": sys_p},
                {"role": "user", "content": usr_p}
            ],
            "temperature": temp,
            "max_tokens": max_t
        }
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data["choices"][0]["message"]["content"]

    @classmethod
    def _call_openai(cls, sys_p: str, usr_p: str, temp: float, max_t: int, timeout: float) -> Optional[str]:
        api_key = os.environ.get("OPENAI_API_KEY", "")
        if not api_key:
            return None
        url = "https://api.openai.com/v1/chat/completions"
        payload = {
            "model": "gpt-4o-mini",
            "messages": [
                {"role": "system", "content": sys_p},
                {"role": "user", "content": usr_p}
            ],
            "temperature": temp,
            "max_tokens": max_t
        }
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data["choices"][0]["message"]["content"]

    @classmethod
    def _call_gemini(cls, sys_p: str, usr_p: str, temp: float, max_t: int, timeout: float) -> Optional[str]:
        api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY", "")
        if not api_key:
            return None
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
        payload = {
            "system_instruction": {"parts": [{"text": sys_p}]},
            "contents": [{"parts": [{"text": usr_p}]}],
            "generationConfig": {"temperature": temp, "maxOutputTokens": max_t}
        }
        headers = {"Content-Type": "application/json"}
        req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data["candidates"][0]["content"]["parts"][0]["text"]

    @classmethod
    def _call_anthropic(cls, sys_p: str, usr_p: str, temp: float, max_t: int, timeout: float) -> Optional[str]:
        api_key = os.environ.get("ANTHROPIC_API_KEY", "")
        if not api_key:
            return None
        url = "https://api.anthropic.com/v1/messages"
        payload = {
            "model": "claude-3-5-sonnet-20241022",
            "system": sys_p,
            "messages": [{"role": "user", "content": usr_p}],
            "max_tokens": max_t,
            "temperature": temp
        }
        headers = {
            "Content-Type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01"
        }
        req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data["content"][0]["text"]
