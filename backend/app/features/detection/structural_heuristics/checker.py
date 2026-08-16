"""Layer 4 — structural heuristics (pure Python, no external calls)."""

import base64
import re
import unicodedata

from app.features.detection.schemas import HeuristicResult

_BASE64_PATTERN = re.compile(r"[A-Za-z0-9+/]{40,}={0,2}")
_HEX_PATTERN = re.compile(r"(?:0x)?[0-9a-fA-F]{64,}")
_ROLE_SWITCH_PATTERN = re.compile(r"(?i)\b(system|assistant|user)\s*:")
_INVISIBLE_CHARS = {
  "\u200b",  # zero-width space
  "\u200c",  # zero-width non-joiner
  "\u200d",  # zero-width joiner
  "\u2060",  # word joiner
  "\ufeff",  # zero-width no-break space / BOM
  "\u202e",  # RTL override
  "\u202d",  # LTR override
  "\u202c",  # pop directional formatting
}

_DEFAULT_BASELINE_LENGTH = 2000
_LENGTH_MULTIPLIER_THRESHOLD = 5


def check_heuristics(prompt: str, baseline_length: int = _DEFAULT_BASELINE_LENGTH) -> HeuristicResult:
  findings: list[str] = []
  score = 0

  base64_matches = _BASE64_PATTERN.findall(prompt)
  if base64_matches:
    longest = max(base64_matches, key=len)
    if len(longest) >= 40:
      try:
        decoded = base64.b64decode(longest, validate=True)
        if len(decoded) > 20:
          findings.append(f"Base64-encoded blob detected ({len(longest)} chars)")
          score = max(score, 70)
      except Exception:
        findings.append(f"Suspicious base64-like string ({len(longest)} chars)")
        score = max(score, 50)

  hex_matches = _HEX_PATTERN.findall(prompt)
  if hex_matches:
    longest_hex = max(hex_matches, key=len)
    if len(longest_hex) >= 64:
      findings.append(f"Hex-encoded blob detected ({len(longest_hex)} chars)")
      score = max(score, 65)

  invisible_count = sum(1 for ch in prompt if ch in _INVISIBLE_CHARS)
  if invisible_count > 0:
    findings.append(f"Invisible/zero-width characters detected ({invisible_count})")
    score = max(score, min(40 + invisible_count * 10, 90))

  non_ascii_ratio = sum(1 for ch in prompt if ord(ch) > 127) / max(len(prompt), 1)
  if non_ascii_ratio > 0.3 and len(prompt) > 100:
    findings.append(f"High non-ASCII character ratio ({non_ascii_ratio:.0%})")
    score = max(score, 40)

  control_chars = sum(
    1 for ch in prompt
    if unicodedata.category(ch).startswith("C") and ch not in ("\n", "\r", "\t")
  )
  if control_chars > 5:
    findings.append(f"Excessive control characters ({control_chars})")
    score = max(score, 55)

  role_matches = _ROLE_SWITCH_PATTERN.findall(prompt)
  if role_matches:
    findings.append(f"Role-switch tokens in user content: {', '.join(set(role_matches))}")
    score = max(score, min(60 + len(role_matches) * 10, 90))

  if len(prompt) > baseline_length * _LENGTH_MULTIPLIER_THRESHOLD:
    findings.append(f"Abnormal prompt length ({len(prompt)} chars vs baseline {baseline_length})")
    score = max(score, 50)

  repeated_phrases = _detect_repetition(prompt)
  if repeated_phrases:
    findings.append(f"Repeated phrase patterns detected ({len(repeated_phrases)})")
    score = max(score, 45)

  return HeuristicResult(score=min(score, 100), findings=findings)


def _detect_repetition(prompt: str) -> list[str]:
  words = prompt.lower().split()
  if len(words) < 10:
    return []

  repeated: list[str] = []
  for window_size in (3, 4, 5):
    seen: dict[str, int] = {}
    for i in range(len(words) - window_size + 1):
      phrase = " ".join(words[i : i + window_size])
      seen[phrase] = seen.get(phrase, 0) + 1
      if seen[phrase] >= 3:
        repeated.append(phrase)
  return repeated
