import json
import re
import uuid
from dataclasses import dataclass
from datetime import datetime
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Lazy imports to avoid circular dependencies
RAGAdapter = None
log_compliance_decision = None


@dataclass
class EvidenceSpan:
    """Individual evidence span with metadata"""

    text: str
    start_pos: int
    end_pos: int
    source: str
    regulation_reference: Optional[str] = None
    confidence: float = 1.0
    regulatory_context: Optional[str] = None


@dataclass
class RegulationMapping:
    """Regulation mapping with validation details"""

    regulation_name: str
    text_excerpt: str
    is_valid: bool
    validation_notes: str
    section_reference: Optional[str] = None
    source_file: Optional[str] = None


@dataclass
class ReasoningValidation:
    """Validation result for reasoning-evidence alignment"""

    reasoning_text: str
    evidence_spans: List[EvidenceSpan]
    regulation_mappings: List[RegulationMapping]
    alignment_score: float
    alignment_issues: List[str]
    is_aligned: bool


@dataclass
class EvidenceQuality:
    """Assessment of evidence quality"""

    span: EvidenceSpan
    quality_score: float
    quality_level: str  # "Strong", "Moderate", "Weak", "Generic"
    specific_language: bool
    regulation_linked: bool
    compliance_terms: List[str]
    quality_notes: str


@dataclass
class VerificationResult:
    """Complete verification result for a case"""

    case_id: str
    reasoning_validation: ReasoningValidation
    evidence_quality: List[EvidenceQuality]
    regulation_mapping_valid: bool
    final_decision: str
    auto_approved: bool
    flags: List[str]
    notes: str
    overall_score: float


class EvidenceVerificationAgent:
    """
    Evidence Verification Agent for Compliance Decisions

    Validates reasoning against evidence spans and regulation texts to ensure
    defensible compliance decisions with automatic approval of strong cases
    and flagging of problematic ones for manual review.
    """

    def __init__(self, legal_texts_dir: str = "legal_texts", rag_adapter=None):
        self.legal_texts_dir = Path(legal_texts_dir)
        self.regulation_database = self._load_regulation_database()
        self.compliance_keywords = self._initialize_compliance_keywords()
        self.verification_history = []

        # RAG integration - handle None case
        self.rag_adapter = rag_adapter

        # Quality thresholds
        self.alignment_threshold = 0.75
        self.quality_threshold = 0.70
        self.auto_approval_threshold = 0.85

    def _load_regulation_database(self) -> Dict[str, Dict[str, Any]]:
        """Load available regulation texts and metadata"""
        database = {}

        if self.legal_texts_dir.exists():
            for file_path in self.legal_texts_dir.glob("*.txt"):
                regulation_name = file_path.stem
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()

                    database[regulation_name] = {
                        "content": content,
                        "file_path": str(file_path),
                        "sections": self._extract_sections(content),
                        "compliance_terms": self._extract_compliance_terms(content),
                    }
                except Exception as e:
                    print(f"Warning: Could not load {file_path}: {e}")

        return database

    def _extract_sections(self, content: str) -> Dict[str, str]:
        """Extract sections from regulation text"""
        sections = {}

        # Look for common section patterns
        section_patterns = [
            r"Section\s+(\d+[A-Za-z]?)[:\s]+([^\n]+)",
            r"§\s*(\d+[A-Za-z]?)[:\s]+([^\n]+)",
            r"(\d+[A-Za-z]?)[.\s]+([^\n]+)",
        ]

        for pattern in section_patterns:
            matches = re.finditer(pattern, content, re.MULTILINE)
            for match in matches:
                section_num = match.group(1)
                section_title = match.group(2).strip()
                # Get content up to next section or end
                start_pos = match.end()
                next_match = re.search(pattern, content[start_pos:])
                if next_match:
                    end_pos = start_pos + next_match.start()
                else:
                    end_pos = len(content)

                sections[section_num] = content[start_pos:end_pos].strip()

        return sections

    def _extract_compliance_terms(self, content: str) -> List[str]:
        """Extract compliance-related terms from regulation text"""
        compliance_patterns = [
            r"\b(shall|must|required|mandatory|obligatory)\b",
            r"\b(prohibited|forbidden|illegal|unlawful)\b",
            r"\b(compliance|comply|conform|adhere)\b",
            r"\b(regulation|statute|law|act|code)\b",
            r"\b(penalty|fine|sanction|enforcement)\b",
        ]

        terms = []
        for pattern in compliance_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            terms.extend(matches)

        return list(set(terms))

    def verify_evidence_with_rag(
        self, text: str, regulation_refs: List[str]
    ) -> List[RegulationMapping]:
        """Verify evidence using centralized RAG system."""
        if not self.rag_adapter:
            # Fallback when RAG is not available
            return self._verify_evidence_fallback(text, regulation_refs)

        try:
            # Get regulatory context via RAG
            rag_results = self.rag_adapter.retrieve_regulatory_context(
                text, max_results=5
            )

            # Process RAG results
            mappings = []
            for result in rag_results:
                mapping = RegulationMapping(
                    regulation_name=result["source"],
                    text_excerpt=result["text"],
                    is_valid=True,  # RAG results are pre-validated
                    validation_notes=f"Retrieved via centralized RAG system",
                    section_reference=result["section"],
                    source_file=result["metadata"].get("source_path"),
                )
                mappings.append(mapping)

            return mappings

        except Exception as e:
            print(f"RAG-based verification failed: {e}")
            # Fallback to existing method
            return self._verify_evidence_fallback(text, regulation_refs)

    def _verify_evidence_fallback(
        self, text: str, regulation_refs: List[str]
    ) -> List[RegulationMapping]:
        """Fallback verification method."""
        # Existing verification logic
        return []

    def get_rag_system_status(self) -> Dict[str, Any]:
        """Get RAG system status."""
        return self.rag_adapter.get_system_status()

    def _initialize_compliance_keywords(self) -> Dict[str, List[str]]:
        """Initialize compliance keywords for evidence quality assessment"""
        return {
            "strong_compliance": [
                "shall",
                "must",
                "required",
                "mandatory",
                "obligatory",
                "compliance",
                "comply",
                "conform",
                "adhere",
                "enforce",
            ],
            "prohibited": [
                "prohibited",
                "forbidden",
                "illegal",
                "unlawful",
                "banned",
                "restricted",
                "not permitted",
                "not allowed",
            ],
            "regulatory_framework": [
                "regulation",
                "statute",
                "law",
                "act",
                "code",
                "standard",
                "guideline",
                "policy",
                "requirement",
            ],
            "enforcement": [
                "penalty",
                "fine",
                "sanction",
                "enforcement",
                "violation",
                "breach",
                "non-compliance",
                "audit",
                "review",
            ],
        }

    def verify_case(
        self,
        case_id: str,
        reasoning_text: str,
        evidence_spans: List[Dict[str, Any]],
        regulation_references: List[str],
    ) -> VerificationResult:
        """
        Verify a compliance case by validating reasoning against evidence

        Args:
            case_id: Unique identifier for the case
            reasoning_text: Classifier reasoning text
            evidence_spans: List of evidence spans with text and metadata
            regulation_references: List of referenced regulations

        Returns:
            VerificationResult with validation details
        """
        # Parse evidence spans
        parsed_spans = []
        for span_data in evidence_spans:
            span = EvidenceSpan(
                text=span_data.get("text", ""),
                start_pos=span_data.get("start_pos", 0),
                end_pos=span_data.get("end_pos", 0),
                source=span_data.get("source", "unknown"),
                regulation_reference=span_data.get("regulation_reference"),
                confidence=span_data.get("confidence", 1.0),
            )
            parsed_spans.append(span)

        # Validate reasoning-evidence alignment
        reasoning_validation = self._validate_reasoning_alignment(
            reasoning_text, parsed_spans
        )

        # Validate regulation mappings
        regulation_mappings = self._validate_regulation_mappings(
            regulation_references, parsed_spans
        )

        # Assess evidence quality
        evidence_quality = self._assess_evidence_quality(parsed_spans)

        # Determine final decision
        final_decision, auto_approved, flags, notes, overall_score = (
            self._make_verification_decision(
                reasoning_validation, regulation_mappings, evidence_quality
            )
        )

        # Create verification result
        result = VerificationResult(
            case_id=case_id,
            reasoning_validation=reasoning_validation,
            evidence_quality=evidence_quality,
            regulation_mapping_valid=all(m.is_valid for m in regulation_mappings),
            final_decision=final_decision,
            auto_approved=auto_approved,
            flags=flags,
            notes=notes,
            overall_score=overall_score,
        )

        # Store in history
        self.verification_history.append(result)

        # Log evidence for verification decision
        if log_compliance_decision:
            evidence_data = {
                "request_id": str(uuid.uuid4()),
                "timestamp_iso": datetime.now().isoformat(),
                "agent_name": "evidence_verifier",
                "decision_flag": final_decision == "APPROVED",
                "reasoning_text": f"Verification completed: {final_decision} - {notes}",
                "feature_id": case_id,
                "feature_title": f"Evidence Verification {case_id}",
                "related_regulations": regulation_references,
                "confidence": overall_score,
                "retrieval_metadata": {
                    "agent_specific": "evidence_verification",
                    "evidence_spans_count": len(evidence_spans),
                    "regulation_references_count": len(regulation_references),
                    "alignment_score": reasoning_validation.alignment_score,
                    "quality_score": sum(q.quality_score for q in evidence_quality)
                    / max(len(evidence_quality), 1),
                },
                "timings_ms": {
                    "verification_ms": 0  # Will be populated if timing is tracked
                },
            }
            log_compliance_decision(evidence_data)

        return result

    def _validate_reasoning_alignment(
        self, reasoning_text: str, evidence_spans: List[EvidenceSpan]
    ) -> ReasoningValidation:
        """Validate that reasoning aligns with evidence spans"""
        alignment_scores = []
        alignment_issues = []

        if not evidence_spans:
            return ReasoningValidation(
                reasoning_text=reasoning_text,
                evidence_spans=evidence_spans,
                regulation_mappings=[],
                alignment_score=0.0,
                alignment_issues=["No evidence spans provided"],
                is_aligned=False,
            )

        # Check semantic alignment between reasoning and each evidence span
        for span in evidence_spans:
            if not span.text.strip():
                alignment_issues.append(f"Empty evidence span from {span.source}")
                alignment_scores.append(0.0)
                continue

            # Calculate semantic similarity
            similarity = self._calculate_semantic_similarity(reasoning_text, span.text)
            alignment_scores.append(similarity)

            if similarity < self.alignment_threshold:
                alignment_issues.append(
                    f"Low alignment ({similarity:.2f}) between reasoning and evidence from {span.source}"
                )

        # Calculate overall alignment score
        overall_alignment = (
            sum(alignment_scores) / len(alignment_scores) if alignment_scores else 0.0
        )
        is_aligned = overall_alignment >= self.alignment_threshold

        return ReasoningValidation(
            reasoning_text=reasoning_text,
            evidence_spans=evidence_spans,
            regulation_mappings=[],
            alignment_score=overall_alignment,
            alignment_issues=alignment_issues,
            is_aligned=is_aligned,
        )

    def _calculate_semantic_similarity(self, text1: str, text2: str) -> float:
        """Calculate semantic similarity between two texts"""
        # Simple sequence matcher for now - could be enhanced with more sophisticated NLP
        text1_clean = re.sub(r"\s+", " ", text1.lower().strip())
        text2_clean = re.sub(r"\s+", " ", text2.lower().strip())

        if not text1_clean or not text2_clean:
            return 0.0

        # Use sequence matcher for similarity
        similarity = SequenceMatcher(None, text1_clean, text2_clean).ratio()

        # Boost similarity if key terms are shared
        words1 = set(text1_clean.split())
        words2 = set(text2_clean.split())
        if words1 and words2:
            word_overlap = len(words1.intersection(words2)) / len(words1.union(words2))
            # Combine sequence similarity with word overlap
            final_similarity = (similarity + word_overlap) / 2
            return min(1.0, final_similarity)

        return similarity

    def _validate_regulation_mappings(
        self, regulation_references: List[str], evidence_spans: List[EvidenceSpan]
    ) -> List[RegulationMapping]:
        """Validate that cited regulations exist and apply to the evidence"""
        mappings = []

        for regulation_ref in regulation_references:
            # Check if regulation exists in database
            regulation_name = self._normalize_regulation_name(regulation_ref)

            if regulation_name in self.regulation_database:
                regulation_data = self.regulation_database[regulation_name]

                # Check if evidence spans contain content from this regulation
                regulation_content = regulation_data["content"]
                is_referenced = self._check_regulation_reference(
                    regulation_content, evidence_spans
                )

                if is_referenced:
                    mapping = RegulationMapping(
                        regulation_name=regulation_name,
                        text_excerpt=regulation_content[:200] + "...",
                        is_valid=True,
                        validation_notes=f"Regulation {regulation_name} found and referenced in evidence",
                        source_file=regulation_data["file_path"],
                    )
                else:
                    mapping = RegulationMapping(
                        regulation_name=regulation_name,
                        text_excerpt="",
                        is_valid=False,
                        validation_notes=f"Regulation {regulation_name} found but not referenced in evidence",
                        source_file=regulation_data["file_path"],
                    )
            else:
                mapping = RegulationMapping(
                    regulation_name=regulation_name,
                    text_excerpt="",
                    is_valid=False,
                    validation_notes=f"Regulation {regulation_name} not found in database",
                    source_file=None,
                )

            mappings.append(mapping)

        return mappings

    def _normalize_regulation_name(self, regulation_ref: str) -> str:
        """Normalize regulation reference to match database keys"""
        # Remove common prefixes and normalize
        normalized = regulation_ref.strip()

        # Remove common prefixes
        prefixes_to_remove = ["the ", "act", "regulation", "statute", "law", "code"]

        for prefix in prefixes_to_remove:
            if normalized.lower().startswith(prefix.lower()):
                normalized = normalized[len(prefix) :].strip()

        # Try to find best match in database
        for key in self.regulation_database.keys():
            if (
                regulation_ref.lower() in key.lower()
                or key.lower() in regulation_ref.lower()
            ):
                return key

        return normalized

    def _check_regulation_reference(
        self, regulation_content: str, evidence_spans: List[EvidenceSpan]
    ) -> bool:
        """Check if any evidence spans reference the regulation content"""
        if not regulation_content:
            return False

        # Extract key terms from regulation
        regulation_terms = set(re.findall(r"\b\w{4,}\b", regulation_content.lower()))

        # Check if evidence spans contain regulation terms
        for span in evidence_spans:
            if not span.text:
                continue

            span_terms = set(re.findall(r"\b\w{4,}\b", span.text.lower()))

            # Check for significant overlap
            overlap = len(regulation_terms.intersection(span_terms))
            if overlap > 3:  # At least 3 significant terms overlap
                return True

        return False

    def _assess_evidence_quality(
        self, evidence_spans: List[EvidenceSpan]
    ) -> List[EvidenceQuality]:
        """Assess the quality of evidence spans"""
        quality_assessments = []

        for span in evidence_spans:
            if not span.text.strip():
                quality_assessments.append(
                    EvidenceQuality(
                        span=span,
                        quality_score=0.0,
                        quality_level="Weak",
                        specific_language=False,
                        regulation_linked=False,
                        compliance_terms=[],
                        quality_notes="Empty evidence span",
                    )
                )
                continue

            # Analyze evidence quality
            compliance_terms = self._extract_compliance_terms_from_span(span.text)
            specific_language = self._assess_specificity(span.text)
            regulation_linked = bool(span.regulation_reference)

            # Calculate quality score
            quality_score = self._calculate_quality_score(
                compliance_terms, specific_language, regulation_linked, span.confidence
            )

            # Determine quality level
            if quality_score >= 0.8:
                quality_level = "Strong"
            elif quality_score >= 0.6:
                quality_level = "Moderate"
            elif quality_score >= 0.4:
                quality_level = "Weak"
            else:
                quality_level = "Generic"

            quality_assessments.append(
                EvidenceQuality(
                    span=span,
                    quality_score=quality_score,
                    quality_level=quality_level,
                    specific_language=specific_language,
                    regulation_linked=regulation_linked,
                    compliance_terms=compliance_terms,
                    quality_notes=self._generate_quality_notes(
                        span.text, compliance_terms, specific_language
                    ),
                )
            )

        return quality_assessments

    def _extract_compliance_terms_from_span(self, text: str) -> List[str]:
        """Extract compliance-related terms from evidence span"""
        found_terms = []
        text_lower = text.lower()

        for category, terms in self.compliance_keywords.items():
            for term in terms:
                if term.lower() in text_lower:
                    found_terms.append(term)

        return found_terms

    def _assess_specificity(self, text: str) -> bool:
        """Assess whether text contains specific rather than generic language"""
        # Check for specific indicators
        specific_indicators = [
            r"\b\d{4}\b",  # Years
            r"\b\d+[A-Za-z]?\b",  # Section numbers
            r"\b[A-Z][a-z]+\s+[A-Z][a-z]+\b",  # Proper nouns
            r"\b(shall|must|required|prohibited)\b",  # Specific legal terms
        ]

        for pattern in specific_indicators:
            if re.search(pattern, text):
                return True

        # Check for generic language
        generic_indicators = [
            r"\b(general|usually|typically|generally)\b",
            r"\b(may|might|could|should)\b",
            r"\b(appropriate|reasonable|adequate)\b",
        ]

        generic_count = 0
        for pattern in generic_indicators:
            generic_count += len(re.findall(pattern, text, re.IGNORECASE))

        # Text is specific if it has specific indicators and few generic ones
        return generic_count < 2

    def _calculate_quality_score(
        self,
        compliance_terms: List[str],
        specific_language: bool,
        regulation_linked: bool,
        confidence: float,
    ) -> float:
        """Calculate evidence quality score"""
        score = 0.0

        # Base score from compliance terms
        if compliance_terms:
            score += min(0.4, len(compliance_terms) * 0.1)

        # Specificity bonus
        if specific_language:
            score += 0.3

        # Regulation linkage bonus
        if regulation_linked:
            score += 0.2

        # Confidence adjustment
        score *= confidence

        return min(1.0, score)

    def _generate_quality_notes(
        self, text: str, compliance_terms: List[str], specific_language: bool
    ) -> str:
        """Generate notes about evidence quality"""
        notes = []

        if compliance_terms:
            notes.append(
                f"Contains {len(compliance_terms)} compliance terms: {', '.join(compliance_terms[:3])}"
            )

        if specific_language:
            notes.append("Contains specific legal language")
        else:
            notes.append("Contains generic language")

        if len(text.split()) < 10:
            notes.append("Short evidence span")
        elif len(text.split()) > 100:
            notes.append("Long evidence span")

        return "; ".join(notes)

    def _make_verification_decision(
        self,
        reasoning_validation: ReasoningValidation,
        regulation_mappings: List[RegulationMapping],
        evidence_quality: List[EvidenceQuality],
    ) -> Tuple[str, bool, List[str], str, float]:
        """Make final verification decision"""
        flags = []
        notes_parts = []

        # Check reasoning alignment
        if not reasoning_validation.is_aligned:
            flags.append("Reasoning-evidence misalignment")
            notes_parts.append("Low alignment between reasoning and evidence")

        # Check regulation mappings
        invalid_mappings = [m for m in regulation_mappings if not m.is_valid]
        if invalid_mappings:
            flags.append("Invalid regulation mappings")
            notes_parts.append(f"{len(invalid_mappings)} invalid regulation references")

        # Check evidence quality
        weak_evidence = [
            eq for eq in evidence_quality if eq.quality_level in ["Weak", "Generic"]
        ]
        if weak_evidence:
            flags.append("Weak evidence quality")
            notes_parts.append(f"{len(weak_evidence)} low-quality evidence spans")

        # Calculate overall score
        alignment_score = reasoning_validation.alignment_score
        regulation_score = sum(1 for m in regulation_mappings if m.is_valid) / max(
            1, len(regulation_mappings)
        )
        quality_score = sum(eq.quality_score for eq in evidence_quality) / max(
            1, len(evidence_quality)
        )

        overall_score = (alignment_score + regulation_score + quality_score) / 3

        # Determine decision
        if overall_score >= self.auto_approval_threshold and not flags:
            final_decision = "Auto-Approved"
            auto_approved = True
            notes_parts.append("Strong evidence and alignment - auto-approved")
        elif overall_score >= self.quality_threshold:
            final_decision = "Approved with Notes"
            auto_approved = False
            notes_parts.append("Moderate quality - approved with review notes")
        else:
            final_decision = "Manual Review Required"
            auto_approved = False
            notes_parts.append("Low quality or misalignment - manual review required")

        notes = "; ".join(notes_parts)

        return final_decision, auto_approved, flags, notes, overall_score

    def get_verification_summary(self) -> str:
        """Get summary of all verifications in markdown format"""
        if not self.verification_history:
            return "No verification results available."

        # Create summary table
        table_rows = []
        for result in self.verification_history:
            row = {
                "Case ID": result.case_id,
                "Reasoning–Evidence Alignment": f"{result.reasoning_validation.alignment_score:.2f}",
                "Regulation Mapping Valid": (
                    "Yes" if result.regulation_mapping_valid else "No"
                ),
                "Evidence Quality": f"{sum(eq.quality_score for eq in result.evidence_quality) / max(1, len(result.evidence_quality)):.2f}",
                "Final Decision": result.final_decision,
                "Notes/Flags": "; ".join(result.flags) if result.flags else "None",
            }
            table_rows.append(row)

        # Generate markdown table
        markdown = "## Evidence Verification Summary\n\n"
        markdown += "| Case ID | Reasoning–Evidence Alignment | Regulation Mapping Valid | Evidence Quality | Final Decision | Notes/Flags |\n"
        markdown += "|----------|------------------------------|--------------------------|------------------|-----------------|-------------|\n"

        for row in table_rows:
            markdown += f"| {row['Case ID']} | {row['Reasoning–Evidence Alignment']} | {row['Regulation Mapping Valid']} | {row['Evidence Quality']} | {row['Final Decision']} | {row['Notes/Flags']} |\n"

        return markdown

    def export_verification_results(self, filename: str = None) -> str:
        """Export verification results to markdown file"""
        if filename is None:
            from datetime import datetime

            filename = (
                f"evidence_verification_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
            )

        markdown_content = "# Evidence Verification Results\n\n"
        markdown_content += (
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        )
        markdown_content += f"Total Cases: {len(self.verification_history)}\n\n"

        # Summary table
        markdown_content += self.get_verification_summary()
        markdown_content += "\n\n"

        # Detailed results
        markdown_content += "## Detailed Results\n\n"
        for result in self.verification_history:
            markdown_content += f"### Case {result.case_id}\n\n"
            markdown_content += f"**Overall Score:** {result.overall_score:.2f}\n\n"
            markdown_content += f"**Final Decision:** {result.final_decision}\n\n"
            markdown_content += (
                f"**Auto-Approved:** {'Yes' if result.auto_approved else 'No'}\n\n"
            )

            # Reasoning validation
            markdown_content += "**Reasoning-Evidence Alignment:**\n"
            markdown_content += f"- Alignment Score: {result.reasoning_validation.alignment_score:.2f}\n"
            markdown_content += f"- Is Aligned: {'Yes' if result.reasoning_validation.is_aligned else 'No'}\n"
            if result.reasoning_validation.alignment_issues:
                markdown_content += "- Issues:\n"
                for issue in result.reasoning_validation.alignment_issues:
                    markdown_content += f"  - {issue}\n"
            markdown_content += "\n"

            # Evidence quality
            markdown_content += "**Evidence Quality:**\n"
            for eq in result.evidence_quality:
                markdown_content += (
                    f"- {eq.span.source}: {eq.quality_level} ({eq.quality_score:.2f})\n"
                )
                markdown_content += f"  - {eq.quality_notes}\n"
            markdown_content += "\n"

            # Flags and notes
            if result.flags:
                markdown_content += "**Flags:**\n"
                for flag in result.flags:
                    markdown_content += f"- {flag}\n"
                markdown_content += "\n"

            markdown_content += f"**Notes:** {result.notes}\n\n"
            markdown_content += "---\n\n"

        # Save to file
        with open(filename, "w") as f:
            f.write(markdown_content)

        return filename

    def _verify_evidence_fallback(
        self, text: str, regulation_refs: List[str]
    ) -> List[RegulationMapping]:
        """Fallback verification when RAG is not available"""
        mappings = []
        for ref in regulation_refs:
            # Simple text-based verification
            mapping = RegulationMapping(
                regulation_name=ref,
                text_excerpt=text[:200] + "..." if len(text) > 200 else text,
                is_valid=True,
                validation_notes="Fallback verification - RAG not available",
                section_reference=None,
                source_file=None,
            )
            mappings.append(mapping)
        return mappings
