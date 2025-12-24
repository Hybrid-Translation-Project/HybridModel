"""
Hybrid Probabilistic Translator - Python Orchestrator

This module ties together Prolog candidate generation with Python-based
ambiguity resolution and AI fallback for context-aware translation.

Architecture:
    1. Turkish input sentence → Prolog engine (que_translator.pl)
    2. Prolog generates ALL candidate translations with scores
    3. Python applies ambiguity detection threshold
    4. If ambiguous → AI/LLM is invoked to choose best translation
    5. Final translation returned to user
"""

import os
import sys
import json
from typing import List, Tuple, Dict, Any, Optional
from dataclasses import dataclass

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from pyswip import Prolog
    PYSWIP_AVAILABLE = True
except ImportError:
    PYSWIP_AVAILABLE = False
    print("[WARNING] pyswip not installed. Running in mock mode.")
    print("Install with: pip install pyswip")

from mongo_api import find_word, find_all_meanings, USE_MOCK_DATA


# ============================================================
# Configuration
# ============================================================

@dataclass
class TranslatorConfig:
    """Configuration for the hybrid translator."""
    ambiguity_threshold: int = 3  # If score difference < this, consider ambiguous
    max_candidates: int = 10       # Maximum candidates to consider
    prolog_file: str = "que_translator.pl"
    debug_mode: bool = True


CONFIG = TranslatorConfig()


# ============================================================
# Data Structures
# ============================================================

@dataclass
class ScoreBreakdown:
    """Breakdown of scoring components."""
    frequency: float = 0.0
    collocation: float = 0.0
    semantic: float = 0.0
    pos_match: float = 0.0
    ngram: float = 0.0
    
    def to_dict(self) -> Dict[str, float]:
        return {
            "frequency": round(self.frequency, 2),
            "collocation": round(self.collocation, 2),
            "semantic": round(self.semantic, 2),
            "pos_match": round(self.pos_match, 2),
            "ngram": round(self.ngram, 2)
        }


@dataclass
class TranslationCandidate:
    """Represents a single translation candidate with score."""
    translation: str
    score: float
    breakdown: ScoreBreakdown = None
    
    def to_dict(self) -> Dict[str, Any]:
        result = {"translation": self.translation, "score": round(self.score, 2)}
        if self.breakdown:
            result["breakdown"] = self.breakdown.to_dict()
        return result


@dataclass 
class TranslationResult:
    """Complete translation result with metadata."""
    input_sentence: List[str]
    candidates: List[TranslationCandidate]
    best_translation: str
    is_ambiguous: bool
    ai_resolved: bool
    confidence: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "input": self.input_sentence,
            "candidates": [c.to_dict() for c in self.candidates],
            "best_translation": self.best_translation,
            "is_ambiguous": self.is_ambiguous,
            "ai_resolved": self.ai_resolved,
            "confidence": round(self.confidence, 3)
        }


# ============================================================
# Prolog Interface
# ============================================================

class PrologTranslator:
    """Interface to the Prolog translation engine."""
    
    def __init__(self, prolog_file: str):
        self.prolog_file = prolog_file
        self.prolog = None
        self._initialized = False
        
    def initialize(self) -> bool:
        """Initialize the Prolog engine and load the translation module."""
        if not PYSWIP_AVAILABLE:
            print("[ERROR] pyswip is required for Prolog integration.")
            return False
            
        try:
            self.prolog = Prolog()
            
            # Get absolute path to prolog file
            script_dir = os.path.dirname(os.path.abspath(__file__))
            prolog_path = os.path.join(script_dir, self.prolog_file)
            
            # Normalize path for Prolog (use forward slashes)
            prolog_path = prolog_path.replace("\\", "/")
            
            # Consult the Prolog file
            self.prolog.consult(prolog_path)
            self._initialized = True
            
            if CONFIG.debug_mode:
                print(f"[DEBUG] Loaded Prolog file: {prolog_path}")
                
            return True
            
        except Exception as e:
            print(f"[ERROR] Failed to initialize Prolog: {e}")
            return False
    
    def generate_candidates(self, word_list: List[str]) -> List[TranslationCandidate]:
        """
        Query Prolog to generate all translation candidates.
        
        Args:
            word_list: List of Turkish words to translate
            
        Returns:
            List of TranslationCandidate objects sorted by score (descending)
        """
        if not self._initialized:
            if not self.initialize():
                return self._mock_candidates(word_list)
        
        try:
            # Build Prolog query
            # Convert Python list to Prolog list format
            prolog_list = "[" + ", ".join(word_list) + "]"
            query = f"translate_with_scores({prolog_list}, Results)"
            
            if CONFIG.debug_mode:
                print(f"[DEBUG] Prolog query: {query}")
            
            # Execute query
            results = list(self.prolog.query(query))
            
            if not results:
                return self._mock_candidates(word_list)
            
            # Parse results - Results is now list of [Translation, Score, Breakdown]
            candidates = []
            for result in results:
                pairs = result.get("Results", [])
                for item in pairs:
                    if len(item) >= 2:
                        translation = str(item[0])
                        score = float(item[1])
                        
                        # Parse breakdown if available
                        breakdown = None
                        if len(item) >= 3 and isinstance(item[2], dict):
                            bd = item[2]
                            breakdown = ScoreBreakdown(
                                frequency=float(bd.get('frequency', 0)),
                                collocation=float(bd.get('collocation', 0)),
                                semantic=float(bd.get('semantic', 0)),
                                pos_match=float(bd.get('pos_match', 0)),
                                ngram=float(bd.get('ngram', 0))
                            )
                        
                        candidates.append(TranslationCandidate(translation, score, breakdown))
            
            # Sort by score descending
            candidates.sort(key=lambda c: c.score, reverse=True)
            
            return candidates[:CONFIG.max_candidates]
            
        except Exception as e:
            print(f"[ERROR] Prolog query failed: {e}")
            import traceback
            traceback.print_exc()
            return self._mock_candidates(word_list)
    
    def _mock_candidates(self, word_list: List[str]) -> List[TranslationCandidate]:
        """Generate mock candidates when Prolog is unavailable."""
        print("[INFO] Using Python mock candidate generation with advanced scoring")
        
        from mongo_api import (
            find_word, find_all_meanings, get_frequency_score,
            get_collocation_score, get_semantic_compatibility_score,
            get_ngram_score, get_semantic_class, SCORE_WEIGHTS
        )
        
        candidates = []
        
        if len(word_list) == 1:
            # Single word translation
            word = word_list[0]
            result = find_word(word)
            if result["found"]:
                for m in result["meanings"]:
                    breakdown = ScoreBreakdown(
                        frequency=m.get("score", 50),
                        collocation=0,
                        semantic=50,
                        pos_match=100 if m.get("type") in ["noun", "pronoun"] else 50,
                        ngram=50
                    )
                    total = (breakdown.frequency * 0.25 + breakdown.collocation * 0.25 +
                            breakdown.semantic * 0.20 + breakdown.pos_match * 0.15 +
                            breakdown.ngram * 0.15)
                    candidates.append(TranslationCandidate(m["meaning"], total, breakdown))
            else:
                candidates.append(TranslationCandidate(word, 10.0, ScoreBreakdown()))
        else:
            # Multi-word: SOV to SVO with advanced scoring
            subject = word_list[0]
            verb = word_list[-1]
            objects = word_list[1:-1] if len(word_list) > 2 else []
            
            # Get meanings
            subj_result = find_word(subject)
            verb_result = find_word(verb)
            
            subj_meanings = subj_result.get("meanings", [{"meaning": subject, "score": 10, "type": "unknown", "semantic_class": "unknown"}])
            verb_meanings = verb_result.get("meanings", [{"meaning": verb, "score": 10, "type": "unknown", "semantic_class": "unknown"}])
            
            # Generate combinations with scoring
            for sm in subj_meanings[:3]:
                for vm in verb_meanings[:3]:
                    # Build translation
                    subj_en = sm["meaning"]
                    verb_en = f"{vm['meaning']}s"  # Simple present tense
                    
                    # Translate objects
                    obj_en_list = []
                    for obj in objects:
                        obj_result = find_word(obj)
                        if obj_result["found"] and obj_result["meanings"]:
                            obj_en_list.append(obj_result["meanings"][0]["meaning"])
                        else:
                            obj_en_list.append(obj)
                    
                    parts = [subj_en, verb_en] + obj_en_list
                    translation = " ".join(parts)
                    
                    # Calculate advanced scores
                    freq_score = (sm.get("score", 50) + vm.get("score", 50)) / 2
                    
                    # Collocation between object and verb
                    coll_score = 20
                    if objects:
                        coll_score = get_collocation_score(objects[0], verb, None)
                    
                    # Semantic compatibility
                    subj_class = sm.get("semantic_class", "unknown")
                    verb_class = vm.get("semantic_class", "unknown")
                    sem_score = get_semantic_compatibility_score(subj_class, verb_class)
                    
                    # POS matching
                    pos_score = 50
                    if sm.get("type") in ["pronoun", "noun"]:
                        pos_score += 25
                    if vm.get("type") == "verb":
                        pos_score += 25
                    
                    # N-gram score
                    ngram_score = get_ngram_score([subj_en, verb_en] + obj_en_list)
                    
                    breakdown = ScoreBreakdown(
                        frequency=freq_score,
                        collocation=coll_score,
                        semantic=sem_score,
                        pos_match=pos_score,
                        ngram=ngram_score
                    )
                    
                    total = (freq_score * 0.25 + coll_score * 0.25 +
                            sem_score * 0.20 + pos_score * 0.15 + ngram_score * 0.15)
                    
                    candidates.append(TranslationCandidate(translation, total, breakdown))
        
        # Add fallback
        if not candidates:
            candidates.append(TranslationCandidate(" ".join(word_list), 5.0, ScoreBreakdown()))
        
        # Sort and return
        candidates.sort(key=lambda c: c.score, reverse=True)
        return candidates[:CONFIG.max_candidates]


# ============================================================
# Ambiguity Detection
# ============================================================

def is_ambiguous(candidates: List[TranslationCandidate]) -> Tuple[bool, float]:
    """
    Determine if the translation is ambiguous based on score difference.
    
    Args:
        candidates: List of candidates sorted by score descending
        
    Returns:
        Tuple of (is_ambiguous, confidence)
        - is_ambiguous: True if top candidates are too close in score
        - confidence: 0.0 to 1.0, higher means more certain
    """
    if not candidates:
        return True, 0.0
        
    if len(candidates) == 1:
        return False, 1.0
    
    score_1 = candidates[0].score
    score_2 = candidates[1].score
    
    score_diff = score_1 - score_2
    
    if score_diff < CONFIG.ambiguity_threshold:
        # Calculate confidence based on how close scores are
        # Closer scores = lower confidence
        confidence = score_diff / CONFIG.ambiguity_threshold
        return True, confidence
    else:
        # Clear winner - confidence based on score difference
        confidence = min(1.0, score_diff / (CONFIG.ambiguity_threshold * 3))
        return False, confidence


# ============================================================
# AI/LLM Integration (Mock Implementation)
# ============================================================

def ai_resolve_ambiguity(
    input_sentence: List[str],
    candidates: List[TranslationCandidate],
    context: Optional[str] = None
) -> TranslationCandidate:
    """
    Use an LLM to resolve ambiguous translations.
    
    This is a mock implementation. In production, replace with actual API calls
    to OpenAI, Azure OpenAI, or other LLM providers.
    
    Args:
        input_sentence: Original Turkish words
        candidates: Top translation candidates
        context: Optional additional context
        
    Returns:
        The best candidate chosen by AI
    """
    # Build the prompt
    prompt = build_ai_prompt(input_sentence, candidates, context)
    
    if CONFIG.debug_mode:
        print("\n[AI HANDOVER] Ambiguous translation detected!")
        print("=" * 50)
        print(prompt)
        print("=" * 50)
    
    # MOCK IMPLEMENTATION
    # In production, replace this with actual LLM API call
    chosen = mock_llm_response(input_sentence, candidates)
    
    print(f"[AI DECISION] Selected: '{chosen.translation}' (score: {chosen.score})")
    
    return chosen


def build_ai_prompt(
    input_sentence: List[str],
    candidates: List[TranslationCandidate],
    context: Optional[str] = None
) -> str:
    """Build a prompt for the LLM to resolve translation ambiguity."""
    
    prompt_parts = [
        "You are a Turkish-to-English translation expert.",
        "",
        f"Input sentence (Turkish): {' '.join(input_sentence)}",
        "",
        "The translation system has generated multiple possible translations:",
        ""
    ]
    
    for i, c in enumerate(candidates[:5], 1):
        prompt_parts.append(f"  {i}. \"{c.translation}\" (confidence score: {c.score})")
    
    prompt_parts.extend([
        "",
        "These translations are very close in confidence scores, indicating ambiguity.",
        ""
    ])
    
    if context:
        prompt_parts.extend([
            f"Additional context: {context}",
            ""
        ])
    
    prompt_parts.extend([
        "Based on the context and your linguistic knowledge, which translation",
        "is most likely correct? Consider:",
        "  - Word order and grammar",
        "  - Common usage patterns",
        "  - Contextual meaning",
        "",
        "Please respond with ONLY the number of your chosen translation (1-5)."
    ])
    
    return "\n".join(prompt_parts)


def mock_llm_response(
    input_sentence: List[str],
    candidates: List[TranslationCandidate]
) -> TranslationCandidate:
    """
    Mock LLM response for testing.
    
    Uses simple heuristics to simulate AI decision:
    - Prefers common word forms
    - Considers context clues
    
    In production, replace with actual API call like:
    
    ```python
    import openai
    
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=10
    )
    choice = int(response.choices[0].message.content.strip())
    return candidates[choice - 1]
    ```
    """
    
    # Simple heuristics for mock selection
    # In practice, this would be the LLM's decision
    
    # Heuristic 1: Prefer translations with common English words
    common_words = {'the', 'a', 'is', 'are', 'I', 'you', 'he', 'she', 'it'}
    
    best_candidate = candidates[0]
    best_score = 0
    
    for c in candidates:
        words = set(c.translation.lower().split())
        common_count = len(words.intersection(common_words))
        adjusted_score = c.score + (common_count * 2)
        
        if adjusted_score > best_score:
            best_score = adjusted_score
            best_candidate = c
    
    return best_candidate


# ============================================================
# Main Translation Pipeline
# ============================================================

class HybridTranslator:
    """Main orchestrator for the hybrid translation system."""
    
    def __init__(self, config: TranslatorConfig = None):
        self.config = config or CONFIG
        self.prolog = PrologTranslator(self.config.prolog_file)
        
    def translate(
        self, 
        input_words: List[str],
        context: Optional[str] = None
    ) -> TranslationResult:
        """
        Translate Turkish words to English using hybrid approach.
        
        Args:
            input_words: List of Turkish words
            context: Optional context for better translation
            
        Returns:
            TranslationResult with best translation and metadata
        """
        print(f"\n{'='*60}")
        print(f"Translating: {input_words}")
        print('='*60)
        
        # Step 1: Get candidates from Prolog
        candidates = self.prolog.generate_candidates(input_words)
        
        if self.config.debug_mode:
            print(f"\n[CANDIDATES] Found {len(candidates)} translations:")
            for i, c in enumerate(candidates[:5], 1):
                print(f"  {i}. '{c.translation}' (score: {c.score})")
        
        if not candidates:
            return TranslationResult(
                input_sentence=input_words,
                candidates=[],
                best_translation=" ".join(input_words),
                is_ambiguous=True,
                ai_resolved=False,
                confidence=0.0
            )
        
        # Step 2: Check for ambiguity
        ambiguous, confidence = is_ambiguous(candidates)
        
        if self.config.debug_mode:
            print(f"\n[AMBIGUITY CHECK] Ambiguous: {ambiguous}, Confidence: {confidence:.2f}")
        
        # Step 3: Resolve if needed
        if ambiguous and len(candidates) > 1:
            # AI handover
            best = ai_resolve_ambiguity(input_words, candidates, context)
            ai_resolved = True
        else:
            # Clear winner
            best = candidates[0]
            ai_resolved = False
            print(f"\n[RESULT] Clear winner: '{best.translation}'")
        
        return TranslationResult(
            input_sentence=input_words,
            candidates=candidates,
            best_translation=best.translation,
            is_ambiguous=ambiguous,
            ai_resolved=ai_resolved,
            confidence=confidence
        )
    
    def translate_sentence(self, sentence: str) -> TranslationResult:
        """
        Translate a Turkish sentence string.
        
        Args:
            sentence: Turkish sentence as string
            
        Returns:
            TranslationResult
        """
        # Tokenize (simple split for now)
        words = sentence.strip().lower().split()
        return self.translate(words)


# ============================================================
# Interactive CLI
# ============================================================

def interactive_mode():
    """Run the translator in interactive mode."""
    print("\n" + "="*60)
    print("  HYBRID PROBABILISTIC TRANSLATOR")
    print("  Turkish → English")
    print("="*60)
    print("\nCommands:")
    print("  Type Turkish words separated by spaces")
    print("  'quit' or 'exit' to exit")
    print("  'debug on/off' to toggle debug mode")
    print()
    
    translator = HybridTranslator()
    
    while True:
        try:
            user_input = input("\nTR > ").strip()
            
            if not user_input:
                continue
                
            if user_input.lower() in ('quit', 'exit', 'son', 'çıkış'):
                print("Goodbye! / Hoşça kal!")
                break
                
            if user_input.lower() == 'debug on':
                CONFIG.debug_mode = True
                print("[DEBUG MODE ON]")
                continue
                
            if user_input.lower() == 'debug off':
                CONFIG.debug_mode = False
                print("[DEBUG MODE OFF]")
                continue
            
            # Translate
            result = translator.translate_sentence(user_input)
            
            print(f"\n>>> EN: {result.best_translation}")
            
            if result.ai_resolved:
                print("    (AI-assisted disambiguation)")
            
        except KeyboardInterrupt:
            print("\n\nInterrupted. Goodbye!")
            break
        except Exception as e:
            print(f"[ERROR] {e}")


# ============================================================
# API Functions (for external use)
# ============================================================

def translate(words: List[str], context: str = None) -> Dict[str, Any]:
    """
    Public API function for translation.
    
    Args:
        words: List of Turkish words
        context: Optional context string
        
    Returns:
        Dictionary with translation result
    """
    translator = HybridTranslator()
    result = translator.translate(words, context)
    return result.to_dict()


def translate_text(text: str) -> Dict[str, Any]:
    """
    Public API function for text translation.
    
    Args:
        text: Turkish text as string
        
    Returns:
        Dictionary with translation result
    """
    translator = HybridTranslator()
    result = translator.translate_sentence(text)
    return result.to_dict()


# ============================================================
# Main Entry Point
# ============================================================

if __name__ == "__main__":
    # Check for command line arguments
    if len(sys.argv) > 1:
        # Command line mode
        input_words = sys.argv[1:]
        result = translate(input_words)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        # Interactive mode
        interactive_mode()
