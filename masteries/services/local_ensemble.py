"""Lazy local actor/critic inference for the original PACE model classes.

Actual actor and critic are separate models in Review mode, never simulated.
These models are not shipped in the hosted Render API and require substantial
CPU/GPU memory. The model code in the original repository is preserved.
"""
from __future__ import annotations

from functools import lru_cache
from typing import Iterator

from masteries.services.ai_gateway import AIUnavailable


@lru_cache(maxsize=3)
def _actor(mode: str):
    if mode == "coding":
        from masteries.coding.training.actor.alt_actor_model import ActorModel
        return ActorModel()
    if mode == "literacy":
        from masteries.literacy.training.actor.alt_actor_model import LiteracyActorModel
        return LiteracyActorModel()
    if mode == "research":
        from masteries.research.training.actor.alt_actor_model import ResearchActorModel
        return ResearchActorModel()
    raise AIUnavailable("Invalid workspace")


@lru_cache(maxsize=3)
def _critic(mode: str):
    if mode == "coding":
        from masteries.coding.training.critic.alt_critic_model import QwenCritic
        return QwenCritic()
    if mode == "literacy":
        from masteries.literacy.training.critic.alt_critic_model import LiteracyCriticModel
        return LiteracyCriticModel()
    if mode == "research":
        from masteries.research.training.critic.alt_critic_model import ResearchCriticModel
        return ResearchCriticModel()
    raise AIUnavailable("Invalid workspace")


def _generate(actor, mode: str, prompt: str):
    if mode == "coding":
        return actor.generate_code(prompt)
    if mode == "literacy":
        return actor.generate_text(prompt)
    return actor.generate_research(prompt)


def _revise(actor, mode: str, prompt: str, output: str, critique: str):
    if mode == "coding":
        return actor.revise_code(prompt, output, critique)
    if mode == "literacy":
        return actor.revise_text(prompt, output, critique)
    return actor.revise_research(prompt, output, critique)


def stream_local_ensemble(prompt: str, mode: str, speed: str) -> Iterator[str]:
    if mode not in ("coding", "literacy", "research") or speed not in ("fast", "pro"):
        raise AIUnavailable("Unsupported workspace or model mode")
    actor = _actor(mode)
    initial = "".join(_generate(actor, mode, prompt))
    if not initial.strip():
        raise AIUnavailable("Actor produced no response")
    if speed == "fast":
        yield initial
        return
    # Pro mode *requires* a separate critic. Critic failure is not approval.
    critic = _critic(mode)
    critique = "".join(critic.critique(initial, context=prompt))
    if not critique.strip():
        raise AIUnavailable("Critic produced no feedback")
    revised = "".join(_revise(actor, mode, prompt, initial, critique))
    if not revised.strip():
        raise AIUnavailable("Actor revision produced no response")
    yield revised
