"""
Evaluation harness for the Regulation Retriever Agent.
"""

import json
import logging
import statistics
import time
from pathlib import Path
from typing import Any, Dict, List, Tuple

from retriever.models import SearchResult
from sdk.client import RegulationClient

logger = logging.getLogger(__name__)


class EvaluationMetrics:
    """Container for evaluation metrics."""

    def __init__(self):
        self.hit_at_1 = 0.0
        self.hit_at_3 = 0.0
        self.hit_at_5 = 0.0
        self.avg_latency_ms = 0.0
        self.p50_latency_ms = 0.0
        self.p95_latency_ms = 0.0
        self.avg_score = 0.0
        self.section_accuracy = 0.0
        self.total_queries = 0
        self.successful_queries = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "hit_at_1": self.hit_at_1,
            "hit_at_3": self.hit_at_3,
            "hit_at_5": self.hit_at_5,
            "avg_latency_ms": self.avg_latency_ms,
            "p50_latency_ms": self.p50_latency_ms,
            "p95_latency_ms": self.p95_latency_ms,
            "avg_score": self.avg_score,
            "section_accuracy": self.section_accuracy,
            "total_queries": self.total_queries,
            "successful_queries": self.successful_queries,
            "success_rate": self.successful_queries / max(1, self.total_queries),
        }


class EvaluationHarness:
    """Evaluation harness for testing retrieval quality and performance."""

    def __init__(
        self, client: RegulationClient, queries_file: str = "eval/queries.json"
    ):
        """
        Initialize evaluation harness.

        Args:
            client: Regulation retriever client
            queries_file: Path to evaluation queries JSON
        """
        self.client = client
        self.queries = self._load_queries(queries_file)

    def _load_queries(self, queries_file: str) -> List[Dict[str, Any]]:
        """Load evaluation queries from JSON file."""
        queries_path = Path(queries_file)
        if not queries_path.exists():
            raise FileNotFoundError(f"Queries file not found: {queries_file}")

        with open(queries_path, "r", encoding="utf-8") as f:
            queries = json.load(f)

        logger.info(f"Loaded {len(queries)} evaluation queries")
        return queries

    def run_evaluation(self, top_k: int = 5) -> EvaluationMetrics:
        """
        Run complete evaluation suite.

        Args:
            top_k: Number of results to retrieve per query

        Returns:
            Evaluation metrics
        """
        logger.info(f"Starting evaluation with {len(self.queries)} queries")

        metrics = EvaluationMetrics()
        metrics.total_queries = len(self.queries)

        latencies = []
        scores = []
        hit_1_count = 0
        hit_3_count = 0
        hit_5_count = 0
        section_correct_count = 0

        results_details = []

        for i, query_info in enumerate(self.queries):
            logger.info(
                f"Evaluating query {i+1}/{len(self.queries)}: {query_info['id']}"
            )

            try:
                # Execute query
                start_time = time.time()
                response = self.client.retrieve(
                    query=query_info["query"],
                    laws=query_info.get("expected_laws"),
                    top_k=top_k,
                )
                query_latency = int((time.time() - start_time) * 1000)

                latencies.append(query_latency)
                metrics.successful_queries += 1

                # Evaluate results
                hit_1, hit_3, hit_5, section_correct = self._evaluate_query_results(
                    query_info, response.results
                )

                hit_1_count += hit_1
                hit_3_count += hit_3
                hit_5_count += hit_5
                section_correct_count += section_correct

                # Collect scores
                if response.results:
                    scores.extend([r.score for r in response.results])

                # Store detailed results
                results_details.append(
                    {
                        "query_id": query_info["id"],
                        "query": query_info["query"],
                        "latency_ms": query_latency,
                        "hit_at_1": hit_1,
                        "hit_at_3": hit_3,
                        "hit_at_5": hit_5,
                        "section_correct": section_correct,
                        "results_count": len(response.results),
                        "top_score": (
                            response.results[0].score if response.results else 0.0
                        ),
                    }
                )

            except Exception as e:
                logger.error(f"Query {query_info['id']} failed: {e}")
                results_details.append(
                    {
                        "query_id": query_info["id"],
                        "query": query_info["query"],
                        "error": str(e),
                    }
                )

        # Calculate metrics
        if metrics.successful_queries > 0:
            metrics.hit_at_1 = hit_1_count / metrics.successful_queries
            metrics.hit_at_3 = hit_3_count / metrics.successful_queries
            metrics.hit_at_5 = hit_5_count / metrics.successful_queries
            metrics.section_accuracy = (
                section_correct_count / metrics.successful_queries
            )

        if latencies:
            metrics.avg_latency_ms = statistics.mean(latencies)
            metrics.p50_latency_ms = statistics.median(latencies)
            metrics.p95_latency_ms = statistics.quantiles(latencies, n=20)[
                18
            ]  # 95th percentile

        if scores:
            metrics.avg_score = statistics.mean(scores)

        # Save detailed results
        self._save_results(results_details, metrics)

        logger.info("Evaluation completed")
        return metrics

    def _evaluate_query_results(
        self, query_info: Dict[str, Any], results: List[SearchResult]
    ) -> Tuple[bool, bool, bool, bool]:
        """
        Evaluate results for a single query.

        Returns:
            (hit_at_1, hit_at_3, hit_at_5, section_correct)
        """
        expected_laws = set(query_info.get("expected_laws", []))
        expected_sections = query_info.get("expected_sections", [])

        if not results:
            return False, False, False, False

        # Check hits at different k values
        hit_at_1 = self._check_hit(results[:1], expected_laws)
        hit_at_3 = self._check_hit(results[:3], expected_laws)
        hit_at_5 = self._check_hit(results[:5], expected_laws)

        # Check section accuracy (more specific)
        section_correct = self._check_section_match(results[:3], expected_sections)

        return hit_at_1, hit_at_3, hit_at_5, section_correct

    def _check_hit(self, results: List[SearchResult], expected_laws: set) -> bool:
        """Check if any result matches expected laws."""
        if not expected_laws:
            return True  # No specific law expectation

        result_laws = {r.law_id for r in results}
        return bool(result_laws.intersection(expected_laws))

    def _check_section_match(
        self, results: List[SearchResult], expected_sections: List[str]
    ) -> bool:
        """Check if any result matches expected sections."""
        if not expected_sections:
            return True  # No specific section expectation

        for result in results:
            for expected_section in expected_sections:
                if expected_section.lower() in result.section_label.lower():
                    return True

        return False

    def _save_results(
        self, results_details: List[Dict[str, Any]], metrics: EvaluationMetrics
    ):
        """Save evaluation results to file."""
        output_file = f"eval/results_{int(time.time())}.json"

        output_data = {
            "timestamp": time.time(),
            "metrics": metrics.to_dict(),
            "query_results": results_details,
        }

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(output_data, f, indent=2)

        logger.info(f"Detailed results saved to {output_file}")

    def benchmark_latency(
        self, sample_queries: List[str] = None, iterations: int = 10
    ) -> Dict[str, float]:
        """
        Benchmark latency with repeated queries.

        Args:
            sample_queries: Specific queries to test (uses first 3 eval queries if None)
            iterations: Number of iterations per query

        Returns:
            Latency statistics
        """
        if sample_queries is None:
            sample_queries = [q["query"] for q in self.queries[:3]]

        logger.info(
            f"Benchmarking latency with {len(sample_queries)} queries x {iterations} iterations"
        )

        all_latencies = []

        for query in sample_queries:
            query_latencies = []

            for i in range(iterations):
                try:
                    start_time = time.time()
                    self.client.retrieve(query=query, top_k=5)
                    latency = (time.time() - start_time) * 1000
                    query_latencies.append(latency)
                    all_latencies.append(latency)
                except Exception as e:
                    logger.error(
                        f"Latency test failed for '{query}' iteration {i}: {e}"
                    )

        if not all_latencies:
            return {"error": "No successful latency measurements"}

        return {
            "avg_latency_ms": statistics.mean(all_latencies),
            "min_latency_ms": min(all_latencies),
            "max_latency_ms": max(all_latencies),
            "p50_latency_ms": statistics.median(all_latencies),
            "p95_latency_ms": statistics.quantiles(all_latencies, n=20)[18],
            "p99_latency_ms": statistics.quantiles(all_latencies, n=100)[98],
            "total_measurements": len(all_latencies),
        }


def main():
    """Run evaluation suite."""
    import argparse

    parser = argparse.ArgumentParser(description="Run regulation retriever evaluation")
    parser.add_argument("--url", default="http://localhost:8000", help="API base URL")
    parser.add_argument("--queries", default="eval/queries.json", help="Queries file")
    parser.add_argument(
        "--top-k", type=int, default=5, help="Number of results per query"
    )
    parser.add_argument(
        "--benchmark", action="store_true", help="Run latency benchmark"
    )
    parser.add_argument("--verbose", action="store_true", help="Verbose logging")

    args = parser.parse_args()

    # Setup logging
    logging.basicConfig(
        level=logging.INFO if args.verbose else logging.WARNING,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )

    try:
        # Initialize client
        client = RegulationClient(base_url=args.url)

        # Check service health
        health = client.health()
        logger.info(f"Service status: {health.get('status')}")

        # Initialize evaluator
        evaluator = EvaluationHarness(client, args.queries)

        if args.benchmark:
            # Run latency benchmark
            latency_stats = evaluator.benchmark_latency()
            print("\\n=== Latency Benchmark ===")
            for metric, value in latency_stats.items():
                print(f"{metric}: {value:.2f}")

        # Run evaluation
        metrics = evaluator.run_evaluation(top_k=args.top_k)

        # Print results
        print("\\n=== Evaluation Results ===")
        print(f"Total Queries: {metrics.total_queries}")
        print(f"Successful Queries: {metrics.successful_queries}")
        print(
            f"Success Rate: {metrics.successful_queries/max(1,metrics.total_queries):.2%}"
        )
        print(f"Hit@1: {metrics.hit_at_1:.2%}")
        print(f"Hit@3: {metrics.hit_at_3:.2%}")
        print(f"Hit@5: {metrics.hit_at_5:.2%}")
        print(f"Section Accuracy: {metrics.section_accuracy:.2%}")
        print(f"Avg Latency: {metrics.avg_latency_ms:.0f}ms")
        print(f"P95 Latency: {metrics.p95_latency_ms:.0f}ms")
        print(f"Avg Score: {metrics.avg_score:.3f}")

        # Check performance targets
        print("\\n=== Performance Targets ===")
        p95_target = 1000  # 1000ms target
        hit3_target = 0.9  # 90% target

        print(
            f"P95 < 1000ms: {'✅ PASS' if metrics.p95_latency_ms < p95_target else '❌ FAIL'} ({metrics.p95_latency_ms:.0f}ms)"
        )
        print(
            f"Hit@3 ≥ 90%: {'✅ PASS' if metrics.hit_at_3 >= hit3_target else '❌ FAIL'} ({metrics.hit_at_3:.1%})"
        )

    except Exception as e:
        logger.error(f"Evaluation failed: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
