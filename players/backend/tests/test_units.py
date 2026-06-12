"""Unit tests (no database): encoder, mental extraction, similarity math, routing."""

from __future__ import annotations

import numpy as np
import pytest

from backend.app.services import similarity as sim
from backend.app.services.assistant import _route
from backend.app.services.encoder import DIM, ReportEncoder, cosine
from ml.mental_traits import extract_traits


class TestEncoder:
    def setup_method(self):
        self.enc = ReportEncoder(mode="lite")

    def test_deterministic_and_normalized(self):
        a = self.enc.encode_passage("explosive edge rusher with bend")
        b = self.enc.encode_passage("explosive edge rusher with bend")
        assert a.shape == (DIM,)
        assert np.allclose(a, b)
        assert abs(np.linalg.norm(a) - 1.0) < 1e-5

    def test_blank_is_zero(self):
        assert np.linalg.norm(self.enc.encode_passage("   ")) == 0.0

    def test_shared_vocabulary_scores_higher(self):
        anchor = self.enc.encode_passage("sudden slot receiver wins deep with speed")
        close = self.enc.encode_passage("slot receiver with deep speed who is sudden")
        far = self.enc.encode_passage("two-gap nose tackle anchors against doubles")
        assert cosine(anchor, close) > cosine(anchor, far)

    def test_section_weights(self):
        # sources_tell_us has weight 0 -> must not affect the player embedding
        a = self.enc.encode_player("overview text", "strengths", "weaknesses", "AAA")
        b = self.enc.encode_player("overview text", "strengths", "weaknesses", "BBB")
        assert np.allclose(a, b)


class TestMentalExtraction:
    def test_positive_and_negative_context(self):
        sections = {
            "overview": "",
            "strengths": "Relentless motor; plays to the whistle on every snap.",
            "weaknesses": "Slow to read pattern distribution and late to react.",
            "sources_tell_us": "",
        }
        out = {t["trait"]: t for t in extract_traits(sections, "LB")}
        assert out["motor"]["score"] > 0.6
        assert out["processing_speed"]["score"] < 0.4
        assert "Relentless" in out["motor"]["evidence"]

    def test_qb_subtraits_only_for_qbs(self):
        sections = {
            "overview": "Sets protections himself and handles mike points.",
            "strengths": "", "weaknesses": "", "sources_tell_us": "",
        }
        assert any(t["qb"] for t in extract_traits(sections, "QB"))
        assert not any(t["qb"] for t in extract_traits(sections, "WR"))


class TestSimilarityMath:
    def test_blend_renormalizes_missing_axis(self):
        weights = {"scouting": 0.5, "scheme": 0.25, "mental": 0.25}
        full = sim.blend({"scouting": 0.8, "scheme": 0.4, "mental": 0.6}, weights)
        assert full == pytest.approx(0.5 * 0.8 + 0.25 * 0.4 + 0.25 * 0.6)
        dropped = sim.blend({"scouting": 0.8, "scheme": 0.4, "mental": None}, weights)
        assert dropped == pytest.approx((0.5 * 0.8 + 0.25 * 0.4) / 0.75)

    def test_normalize_weights(self):
        w = sim.normalize_weights({"scouting": 2.0, "scheme": 1.0, "mental": 1.0})
        assert w == {"scouting": 0.5, "scheme": 0.25, "mental": 0.25}
        assert sim.normalize_weights(None) == sim.DEFAULT_WEIGHTS
        assert sim.normalize_weights({"scouting": 0, "scheme": 0, "mental": 0}) == sim.DEFAULT_WEIGHTS

    def test_scheme_family_scoring(self):
        assert sim.archetype_score("Air Raid", "Air Raid") == 1.0
        assert sim.archetype_score("Air Raid", "Spread/RPO") == 0.5
        assert sim.archetype_score("Air Raid", "Power Run") == 0.0
        assert sim.archetype_score(None, "Air Raid") == 0.0

    def test_role_jaccard(self):
        assert sim.role_jaccard(["slot", "deep threat"], ["slot"]) == pytest.approx(0.5)
        assert sim.role_jaccard([], []) == 0.0

    def test_mental_axis_none_when_missing(self):
        v = sim.mental_vector([("motor", 0.8)])
        assert sim.mental_axis(v, None) is None
        assert sim.mental_axis(v, v) == pytest.approx(1.0)


class TestOfflineRouter:
    @pytest.mark.parametrize("message,tool", [
        ("5 fastest 40 times among receivers", "filtered_list"),
        ("compare Ace Alpha and Bo Bravo", "player_compare"),
        ("similar to Ace Alpha", "similarity_comparison"),
        ("tell me about Gus Golf", "player_profile"),
        ("Air Raid receivers", "scheme_fit"),
        ("press-man corner prospects", "role_search"),
        ("best leadership among QBs", "mental_profile_query"),
        ("production for Ace Alpha", "production_lookup"),
        ("team fits for Ace Alpha", "team_fit"),
        ("note on Ace Alpha: great kid", "scout_comment"),
    ])
    def test_intent_routing(self, message, tool):
        routed = _route(message, None)
        assert routed is not None and routed[0] == tool

    def test_fastest_args(self):
        name, args = _route("5 fastest 40 times among receivers", None)
        assert args["sort"] == "forty" and args["limit"] == 5
        assert args["position"] == ["WR"]

    def test_unmatched_returns_none(self):
        assert _route("what's the meaning of life", None) is None
