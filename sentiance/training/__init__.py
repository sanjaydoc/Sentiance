"""Training utilities — turn Sentiance's trace exports into a fine-tuning set.

Kept dependency-light on purpose: ``dataset`` is pure Python (importable and
testable without any ML libraries). The actual trainer lives in ``scripts/`` and
pulls the heavy ``[finetune]`` extras only when you run it.
"""
