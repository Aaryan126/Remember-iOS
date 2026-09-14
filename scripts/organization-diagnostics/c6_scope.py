"""Frozen, corpus-independent controlled-English project-scope feasibility control.

This is a deliberately small rule prototype, not an NLU system or a semantic
reviewer. It performs no I/O and learns nothing. Only complete, unquoted sentences
in the following grammar establish facts (names must themselves be quoted):

* This document concerns [only] project 'Harbor'.
* This note covers [only] projects 'Harbor' and 'Orchard'.
* Projects 'Harbor' and 'Orchard' are separately commissioned undertakings.
* Projects 'Harbor' and 'Orchard' are stages of the same undertaking.

``source``, ``record``, ``is about``, ``undertaking(s)``, and one-to-four names
are accepted in membership statements. Direct relations also accept ``are
separate projects``, ``are independent undertakings``, ``are the same continuing
undertaking``, and ``are phases of the same project``. Straight or curly quotes
are allowed. Name comparisons ignore case and repeated spaces only.

Every endpoint must have exactly one membership sentence. A same-project result
requires a direct explicit same relation connecting memberships of the endpoints.
Shared names, clients, IDs, vocabulary, and low similarity never decide a result.
A separate-project result additionally requires ``only`` at both endpoints and
explicit separate relations for ALL cross-endpoint membership combinations.
No identity or separation is propagated transitively. Shared memberships prevent
separation; direct same and separate claims for the same names cause abstention.

Negation, uncertainty, hypothetical language, and historical corrections trigger
packet-wide abstention. This intentionally overbroad veto is safer than guessing
their scope. Any unsupported sentence or instruction-like language also vetoes
the packet to avoid partially reading a qualification or bridge.
Consequently natural prose, implicit reference, arbitrary quotations, complex
bridges, and context requiring inference will generally abstain. Factual truth
or authenticity cannot be verified; this is not a prompt-injection security
boundary. Recognized source text remains data and is never executed. These
controlled-English requirements may yield zero coverage on naturally worded
text; that is a valid negative diagnostic result, not grounds for corpus tuning.

Citations are exact matched sentence spans from both endpoints and the direct
relation sources. They are stable under source or pair reordering. Malformed
packets raise ValueError; callers still own their full schema/output validation.
No corpus or model outputs were inspected to develop these rules or fixtures.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from itertools import product
from typing import Literal, TypedDict


class Evidence(TypedDict):
    sourceID: str
    quote: str


class Prediction(TypedDict):
    queryID: str
    verdict: Literal["same_project", "separate_projects", "abstain"]
    evidence: list[Evidence]


@dataclass(frozen=True)
class Fact:
    source_id: str
    quote: str
    names: tuple[str, ...]
    kind: str
    exclusive: bool = False


_NAME_BODY = r"[A-Za-z][A-Za-z0-9 _-]{0,79}"
_NAME = rf"(?:'{_NAME_BODY}'|\"{_NAME_BODY}\"|‘{_NAME_BODY}’|“{_NAME_BODY}”)"
_NAME_RE = re.compile(_NAME)
_NAMES = rf"{_NAME}(?:(?:,\s*|\s+and\s+){_NAME}){{0,3}}"
_MEMBERSHIP = re.compile(
    rf"This (?:document|note|record|source) (?:concerns|covers|is about) "
    rf"(?P<only>only )?(?:projects?|undertakings?) (?P<names>{_NAMES})[.!]?",
    re.IGNORECASE,
)
_RELATION = re.compile(
    rf"(?:Projects|Undertakings) (?P<left>{_NAME}) and (?P<right>{_NAME}) "
    r"(?P<relation>are separately commissioned undertakings|"
    r"are separate projects|are independent undertakings|"
    r"are stages of the same undertaking|are the same continuing undertaking|"
    r"are phases of the same project)[.!]?",
    re.IGNORECASE,
)
_SEPARATE = {
    "are separately commissioned undertakings",
    "are separate projects",
    "are independent undertakings",
}
_VETO = re.compile(
    r"\b(?:no|not|never|neither|nor|without|except|unless|"
    r"possibly|perhaps|maybe|might|may|could|would|if|assume|suppose|"
    r"formerly|previously|erroneous|incorrect|retracted|superseded|"
    r"ignore|instructions?|prompt|system|assistant|output|verdict)\b|"
    r"n['’]t\b",
    re.IGNORECASE,
)


def _name(quoted_name: str) -> str:
    return " ".join(quoted_name[1:-1].casefold().split())


def _sentences(text: str) -> list[str]:
    # Names cannot include punctuation, so sentence splitting cannot split a name.
    return [match.group().strip() for match in re.finditer(r"[^.!?\n]+[.!?]?", text)]


def _facts(source_id: str, text: str) -> tuple[list[Fact], bool]:
    if _VETO.search(text):
        return [], False
    facts: list[Fact] = []
    for sentence in _sentences(text):
        membership = _MEMBERSHIP.fullmatch(sentence)
        relation = _RELATION.fullmatch(sentence)
        if membership:
            names = tuple(_name(item.group()) for item in _NAME_RE.finditer(membership["names"]))
            if len(set(names)) != len(names):
                return [], False
            facts.append(Fact(source_id, sentence, names, "membership", bool(membership["only"])))
        elif relation:
            names = (_name(relation["left"]), _name(relation["right"]))
            if names[0] == names[1]:
                return [], False
            kind = "separate" if relation["relation"].casefold() in _SEPARATE else "same"
            facts.append(Fact(source_id, sentence, names, kind))
        else:
            # Do not cherry-pick easy project sentences while ignoring a bridge,
            # negated clause, quotation, or scope qualification we cannot parse.
            return [], False
    return facts, True


def _validate(packet: object) -> tuple[str, tuple[str, str], list[tuple[str, str]]]:
    if not isinstance(packet, dict):
        raise ValueError("packet must be an object")
    query_id = packet.get("queryID")
    pair = packet.get("pair")
    sources = packet.get("sources")
    if not isinstance(query_id, str) or not query_id.strip():
        raise ValueError("queryID must be a nonempty string")
    if packet.get("view") not in ("pair", "context"):
        raise ValueError("view must be pair or context")
    if (not isinstance(pair, list) or len(pair) != 2
            or any(not isinstance(item, str) or not item.strip() for item in pair)
            or pair[0] == pair[1]):
        raise ValueError("pair must contain two distinct nonempty source IDs")
    if not isinstance(sources, list) or not 2 <= len(sources) <= 4:
        raise ValueError("sources must contain two to four sources")
    visible: list[tuple[str, str]] = []
    for source in sources:
        if (not isinstance(source, dict) or not isinstance(source.get("id"), str)
                or not source["id"].strip() or not isinstance(source.get("text"), str)):
            raise ValueError("each source requires a nonempty id and string text")
        visible.append((source["id"], source["text"]))
    ids = [source_id for source_id, _ in visible]
    if len(ids) != len(set(ids)) or not set(pair).issubset(ids):
        raise ValueError("source IDs must be unique and include both endpoints")
    if packet["view"] == "pair" and len(sources) != 2:
        raise ValueError("pair view must contain exactly the two endpoints")
    return query_id, (pair[0], pair[1]), visible


def verify_packet(packet: object) -> Prediction:
    """Return a deterministic cited judgment using only the supplied packet."""
    query_id, pair, sources = _validate(packet)
    abstain: Prediction = {"queryID": query_id, "verdict": "abstain", "evidence": []}
    facts: list[Fact] = []
    for source_id, text in sources:
        source_facts, supported = _facts(source_id, text)
        if not supported:
            return abstain
        facts.extend(source_facts)
    bindings: list[Fact] = []
    for endpoint in pair:
        matches = [fact for fact in facts if fact.source_id == endpoint and fact.kind == "membership"]
        if len(matches) != 1:
            return abstain
        bindings.append(matches[0])
    relations: dict[frozenset[str], dict[str, list[Fact]]] = {}
    for fact in facts:
        if fact.kind != "membership":
            relations.setdefault(frozenset(fact.names), {}).setdefault(fact.kind, []).append(fact)
    if any(len(kinds) != 1 for kinds in relations.values()):
        return abstain
    combinations = list(product(bindings[0].names, bindings[1].names))
    same_facts = [fact for left, right in combinations if left != right
                  for fact in relations.get(frozenset((left, right)), {}).get("same", [])]
    if same_facts:
        verdict: Literal["same_project", "separate_projects"] = "same_project"
        evidence_facts = bindings + same_facts
    else:
        if not all(binding.exclusive for binding in bindings):
            return abstain
        separate_facts: list[Fact] = []
        for left, right in combinations:
            matches = relations.get(frozenset((left, right)), {}).get("separate", [])
            if left == right or not matches:
                return abstain
            separate_facts.extend(matches)
        verdict = "separate_projects"
        evidence_facts = bindings + separate_facts
    evidence: list[Evidence] = [
        {"sourceID": source_id, "quote": quote}
        for source_id, quote in sorted({(fact.source_id, fact.quote) for fact in evidence_facts})
    ]
    return {"queryID": query_id, "verdict": verdict, "evidence": evidence}
