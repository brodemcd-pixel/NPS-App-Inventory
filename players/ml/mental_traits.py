"""Mental & intangible trait extraction from scouting report text (PDR M1, M3).

Lexicon-driven: each trait maps to keyword/phrase patterns. Every hit is scored by the
sentiment of its surrounding window (positive/negative scouting vocabulary), with a prior
from which report section it appears in (strengths skews positive, weaknesses negative).
Per-trait scores aggregate hits into a 0..1 value; 0.5 is neutral.

spaCy (sentence segmentation) is used when importable; a regex sentence splitter is the
fallback so the pipeline runs without optional deps. Extraction is intentionally
*directional*, not ground truth — callers must keep evidence text alongside scores
(PDR risk #3).
"""

from __future__ import annotations

import re

# Core traits apply to every position (PDR M1).
CORE_TRAITS: dict[str, list[str]] = {
    "football_iq": [
        "football iq", "football intelligence", "high iq", "smart player", "cerebral",
        "understands leverage", "understands the game", "savvy", "film junkie", "film study",
    ],
    "processing_speed": [
        "processing", "processes", "quick trigger", "plays fast mentally", "diagnose",
        "diagnoses", "reaction time", "sees it quickly", "slow to read", "late to react",
    ],
    "leadership": [
        "leader", "leadership", "captain", "commands the huddle", "vocal presence",
        "sets the tone", "teammates follow", "locker room presence",
    ],
    "coachability": [
        "coachable", "coachability", "takes coaching", "sponge for", "applies corrections",
        "responds to coaching", "stubborn", "resists coaching",
    ],
    "poise": [
        "poise", "poised", "composure", "composed", "calm under pressure", "unflappable",
        "rattled", "panics", "flustered",
    ],
    "decision_making": [
        "decision-making", "decision making", "decisions", "judgment", "ball security",
        "takes care of the football", "forces throws", "careless with the ball",
        "questionable choices",
    ],
    "instincts": [
        "instincts", "instinctive", "feel for the game", "natural feel", "nose for the ball",
        "sniffs out", "anticipates routes", "robotic", "mechanical mover",
    ],
    "anticipation": [
        "anticipation", "anticipates", "anticipatory", "throws receivers open",
        "beats the snap", "jumps routes", "late ball placement", "waits to see it",
    ],
    "motor": [
        "motor", "relentless", "nonstop effort", "plays to the whistle", "high effort",
        "takes plays off", "effort wanes", "hot and cold effort",
    ],
}

# QB pre-snap processing sub-profile (PDR M3).
QB_TRAITS: dict[str, list[str]] = {
    "audibles": ["audible", "audibles", "checks at the line", "kills the play", "changes the play"],
    "protection_calls": ["protection call", "protection calls", "sets protections", "slides protection", "mike points"],
    "defense_reading": ["reads defenses", "reads the defense", "pre-snap read", "identifies coverage", "deciphers coverage", "coverage recognition"],
    "safety_manipulation": ["manipulates safeties", "moves the safety", "looks off", "looks defenders off", "eye discipline", "holds the safety"],
    "progression_discipline": ["progression", "progressions", "full-field read", "works through reads", "checks down", "check-down", "locks onto", "stares down"],
}

POSITIVE_WORDS = {
    "elite", "outstanding", "excellent", "exceptional", "impressive", "plus", "strong",
    "advanced", "rare", "high-level", "consistently", "best", "smooth", "natural",
    "reliable", "sharp", "crisp", "efficient", "polished", "high", "great", "good",
    "quick", "fast", "commands", "wins", "thrives",
}

NEGATIVE_WORDS = {
    "poor", "lacks", "lacking", "slow", "limited", "concern", "concerns", "concerning",
    "inconsistent", "struggles", "struggled", "below", "questionable", "erratic",
    "sloppy", "late", "rarely", "never", "fails", "marginal", "stiff", "underdeveloped",
    "worrisome", "liability", "red", "stubborn", "careless",
}

# Phrases that are inherently negative regardless of surrounding sentiment words.
_NEGATIVE_PATTERNS = {
    "slow to read", "late to react", "rattled", "panics", "flustered", "stubborn",
    "resists coaching", "forces throws", "careless with the ball", "questionable choices",
    "robotic", "mechanical mover", "late ball placement", "waits to see it",
    "takes plays off", "effort wanes", "hot and cold effort", "locks onto", "stares down",
}

_SECTION_PRIOR = {"overview": 0.0, "strengths": 0.15, "weaknesses": -0.25, "sources_tell_us": 0.0}

_SENT_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")
_WORD_RE = re.compile(r"[a-z']+")

_nlp = None
_spacy_checked = False


def _sentences(text: str) -> list[str]:
    global _nlp, _spacy_checked
    if not _spacy_checked:
        _spacy_checked = True
        try:  # pragma: no cover - depends on optional install
            import spacy

            try:
                _nlp = spacy.load("en_core_web_sm", disable=["ner", "lemmatizer", "tagger"])
            except OSError:
                _nlp = spacy.blank("en")
                _nlp.add_pipe("sentencizer")
        except ImportError:
            _nlp = None
    if _nlp is not None:  # pragma: no cover
        return [s.text for s in _nlp(text).sents]
    return [s for s in _SENT_SPLIT_RE.split(text) if s.strip()]


def _sentence_sentiment(sentence: str) -> float:
    words = set(_WORD_RE.findall(sentence.lower()))
    pos = len(words & POSITIVE_WORDS)
    neg = len(words & NEGATIVE_WORDS)
    if pos == neg == 0:
        return 0.0
    return (pos - neg) / (pos + neg)


def _score_hit(sentence: str, pattern: str, section: str) -> float:
    """Score one keyword hit to 0..1 (0.5 neutral)."""
    sentiment = _sentence_sentiment(sentence)
    if pattern in _NEGATIVE_PATTERNS:
        sentiment = min(sentiment, -0.5)
    sentiment += _SECTION_PRIOR.get(section, 0.0)
    return max(0.0, min(1.0, 0.5 + 0.5 * max(-1.0, min(1.0, sentiment))))


def _extract_lexicon(
    lexicon: dict[str, list[str]], sections: dict[str, str], qb: bool
) -> list[dict]:
    hits: dict[str, list[tuple[float, str]]] = {}
    for section, text in sections.items():
        if not text:
            continue
        for sentence in _sentences(text):
            low = sentence.lower()
            for trait, patterns in lexicon.items():
                for pattern in patterns:
                    if pattern in low:
                        score = _score_hit(sentence, pattern, section)
                        hits.setdefault(trait, []).append((score, sentence.strip()))
                        break  # one hit per trait per sentence
    results = []
    for trait, scored in hits.items():
        scores = [s for s, _ in scored]
        # Mean hit score, nudged toward its extreme by repetition (more mentions = more signal).
        mean = sum(scores) / len(scores)
        confidence = min(1.0, 0.6 + 0.2 * (len(scores) - 1))
        score = 0.5 + (mean - 0.5) * confidence
        evidence = max(scored, key=lambda t: abs(t[0] - 0.5))[1]
        results.append(
            {"trait": trait, "score": round(score, 3), "evidence": evidence[:300], "qb": qb}
        )
    return results


def extract_traits(sections: dict[str, str], position: str) -> list[dict]:
    """Extract mental trait scores from a player's report sections.

    sections keys: overview, strengths, weaknesses, sources_tell_us.
    Returns [{"trait", "score" (0..1), "evidence", "qb"}].
    """
    results = _extract_lexicon(CORE_TRAITS, sections, qb=False)
    if position.upper() == "QB":
        results.extend(_extract_lexicon(QB_TRAITS, sections, qb=True))
    return sorted(results, key=lambda r: (-r["score"], r["trait"]))
