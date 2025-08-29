#!/usr/bin/env python3
"""
Comprehensive test script for the Regulation Retriever Agent.
Tests index building, retrieval performance, and evaluation metrics.
"""

import json
import time
import logging
import statistics
from pathlib import Path
from typing import List, Dict, Any, Tuple
import sys

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_index_building():
    """Test the vector index building process."""
    print("=" * 60)
    print("🏗️  TESTING INDEX BUILDING")
    print("=" * 60)
    
    try:
        from index.build_index import VectorIndexBuilder
        
        # Build the index
        builder = VectorIndexBuilder()
        start_time = time.time()
        stats = builder.build_index()
        build_time = time.time() - start_time
        
        print(f"✅ Index built successfully!")
        print(f"   📊 Total chunks: {stats.total_chunks}")
        print(f"   📚 Total laws: {stats.total_laws}")
        print(f"   ⏱️  Build time: {build_time:.2f}s")
        print(f"   💾 Index path: {stats.index_path}")
        
        # Verify index files exist
        index_dir = Path(stats.index_path).parent
        if (index_dir / "vector.faiss").exists() and (index_dir / "metadata.pkl").exists():
            print("   ✅ Index files created successfully")
        else:
            print("   ❌ Index files not found")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ Index building failed: {e}")
        return False

def test_retrieval_service():
    """Test the retrieval service functionality."""
    print("\n" + "=" * 60)
    print("🔍 TESTING RETRIEVAL SERVICE")
    print("=" * 60)
    
    try:
        from retriever.service import RetrievalService
        
        # Initialize service
        service = RetrievalService()
        
        # Test basic retrieval
        query = "parental consent requirements"
        start_time = time.time()
        results = service.retrieve(query, top_k=3)
        latency = (time.time() - start_time) * 1000
        
        print(f"✅ Basic retrieval working")
        print(f"   🔍 Query: '{query}'")
        print(f"   📊 Results: {len(results)}")
        print(f"   ⏱️  Latency: {latency:.1f}ms")
        
        if results:
            print(f"   🏆 Top result: {results[0].law_id} (score: {results[0].score:.3f})")
            print(f"   📝 Snippet: {results[0].snippet[:100]}...")
        
        return True, latency
        
    except Exception as e:
        print(f"❌ Retrieval service failed: {e}")
        return False, 0

def create_evaluation_queries():
    """Create comprehensive evaluation queries for testing."""
    return [
        {
            "id": "age_verification_1",
            "query": "age verification requirements for social media platforms",
            "expected_laws": ["CA_SB976", "FL_HB3"],
            "description": "Testing age verification compliance"
        },
        {
            "id": "parental_consent_1", 
            "query": "parental consent for minors under 14",
            "expected_laws": ["FL_HB3", "CA_SB976"],
            "description": "Testing parental consent requirements"
        },
        {
            "id": "ncmec_reporting_1",
            "query": "reporting child sexual abuse material to NCMEC",
            "expected_laws": ["US_2258A"],
            "description": "Testing NCMEC reporting obligations"
        },
        {
            "id": "dsa_minors_1",
            "query": "EU Digital Services Act obligations for protecting minors",
            "expected_laws": ["EUDSA"],
            "description": "Testing DSA minor protection requirements"
        },
        {
            "id": "california_addiction_1",
            "query": "California social media addiction prevention measures",
            "expected_laws": ["CA_SB976"],
            "description": "Testing CA addiction prevention law"
        },
        {
            "id": "florida_curfew_1",
            "query": "Florida restrictions on social media access hours",
            "expected_laws": ["FL_HB3"], 
            "description": "Testing FL curfew restrictions"
        },
        {
            "id": "dsa_risk_assessment_1",
            "query": "systemic risk assessment requirements for large platforms",
            "expected_laws": ["EUDSA"],
            "description": "Testing DSA risk assessment obligations"
        },
        {
            "id": "reporting_timeline_1",
            "query": "timeline requirements for reporting illegal content",
            "expected_laws": ["US_2258A", "EUDSA"],
            "description": "Testing reporting timeline compliance"
        },
        {
            "id": "age_assurance_1",
            "query": "age assurance and verification methods",
            "expected_laws": ["FL_HB3", "CA_SB976"],
            "description": "Testing age assurance requirements"
        },
        {
            "id": "penalties_violations_1",
            "query": "penalties for violations and non-compliance",
            "expected_laws": ["CA_SB976", "FL_HB3", "EUDSA"],
            "description": "Testing penalty provisions"
        },
        {
            "id": "data_protection_minors_1",
            "query": "data protection requirements for minors",
            "expected_laws": ["EUDSA", "CA_SB976"],
            "description": "Testing minor data protection"
        },
        {
            "id": "algorithmic_transparency_1",
            "query": "algorithmic transparency and recommendation systems",
            "expected_laws": ["EUDSA", "CA_SB976"],
            "description": "Testing algorithmic requirements"
        },
        {
            "id": "notification_requirements_1",
            "query": "notification requirements to users and authorities",
            "expected_laws": ["EUDSA", "US_2258A"],
            "description": "Testing notification obligations"
        },
        {
            "id": "platform_liability_1",
            "query": "platform liability for harmful content",
            "expected_laws": ["EUDSA", "FL_HB3"],
            "description": "Testing platform liability provisions"
        },
        {
            "id": "implementation_timeline_1",
            "query": "implementation timeline and effective dates",
            "expected_laws": ["CA_SB976", "FL_HB3", "EUDSA"],
            "description": "Testing implementation requirements"
        }
    ]

def run_evaluation():
    """Run comprehensive evaluation of the retrieval system."""
    print("\n" + "=" * 60)
    print("📊 RUNNING COMPREHENSIVE EVALUATION")
    print("=" * 60)
    
    try:
        from retriever.service import RetrievalService
        
        service = RetrievalService()
        queries = create_evaluation_queries()
        
        results = {
            "total_queries": len(queries),
            "latencies": [],
            "hit_at_1": 0,
            "hit_at_3": 0,
            "hit_at_5": 0,
            "query_results": []
        }
        
        print(f"🧪 Testing {len(queries)} evaluation queries...")
        
        for i, test_query in enumerate(queries, 1):
            print(f"\n[{i:2d}/{len(queries)}] {test_query['description']}")
            print(f"   Query: '{test_query['query']}'")
            
            # Measure retrieval latency
            start_time = time.time()
            retrieval_results = service.retrieve(
                query=test_query['query'],
                top_k=5,
                max_chars=800
            )
            latency = (time.time() - start_time) * 1000
            results["latencies"].append(latency)
            
            # Check hits at different k values
            retrieved_laws = [r.law_id for r in retrieval_results]
            expected_laws = set(test_query['expected_laws'])
            
            hit_1 = bool(set(retrieved_laws[:1]) & expected_laws)
            hit_3 = bool(set(retrieved_laws[:3]) & expected_laws)
            hit_5 = bool(set(retrieved_laws[:5]) & expected_laws)
            
            results["hit_at_1"] += hit_1
            results["hit_at_3"] += hit_3  
            results["hit_at_5"] += hit_5
            
            # Store detailed results
            query_result = {
                "query_id": test_query['id'],
                "query": test_query['query'],
                "expected_laws": test_query['expected_laws'],
                "retrieved_laws": retrieved_laws[:3],
                "latency_ms": latency,
                "hit_at_1": hit_1,
                "hit_at_3": hit_3,
                "hit_at_5": hit_5,
                "top_result": {
                    "law_id": retrieval_results[0].law_id if retrieval_results else None,
                    "score": retrieval_results[0].score if retrieval_results else 0,
                    "section": retrieval_results[0].section_label if retrieval_results else None
                } if retrieval_results else None
            }
            results["query_results"].append(query_result)
            
            # Print immediate results
            print(f"   ⏱️  Latency: {latency:.1f}ms")
            print(f"   🎯 Hit@1: {'✅' if hit_1 else '❌'} | Hit@3: {'✅' if hit_3 else '❌'}")
            if retrieval_results:
                print(f"   🏆 Top: {retrieval_results[0].law_id} ({retrieval_results[0].score:.3f})")
        
        # Calculate final metrics
        total_queries = len(queries)
        hit_at_1_rate = results["hit_at_1"] / total_queries
        hit_at_3_rate = results["hit_at_3"] / total_queries
        hit_at_5_rate = results["hit_at_5"] / total_queries
        
        latencies = results["latencies"]
        p50_latency = statistics.median(latencies)
        p95_latency = statistics.quantiles(latencies, n=20)[18] if len(latencies) >= 20 else max(latencies)
        avg_latency = statistics.mean(latencies)
        
        # Print final results
        print("\n" + "=" * 60)
        print("📈 EVALUATION RESULTS")
        print("=" * 60)
        print(f"📊 Query Performance:")
        print(f"   • Total queries: {total_queries}")
        print(f"   • Hit@1: {results['hit_at_1']}/{total_queries} ({hit_at_1_rate:.1%})")
        print(f"   • Hit@3: {results['hit_at_3']}/{total_queries} ({hit_at_3_rate:.1%})")
        print(f"   • Hit@5: {results['hit_at_5']}/{total_queries} ({hit_at_5_rate:.1%})")
        
        print(f"\n⏱️  Latency Performance:")
        print(f"   • P50: {p50_latency:.1f}ms")
        print(f"   • P95: {p95_latency:.1f}ms")
        print(f"   • Average: {avg_latency:.1f}ms")
        print(f"   • Max: {max(latencies):.1f}ms")
        
        # Performance assessment
        performance_target_met = p95_latency < 1000
        accuracy_target_met = hit_at_3_rate >= 0.8
        
        print(f"\n🎯 Target Assessment:")
        print(f"   • P95 < 1000ms: {'✅' if performance_target_met else '❌'} ({p95_latency:.1f}ms)")
        print(f"   • Hit@3 ≥ 80%: {'✅' if accuracy_target_met else '❌'} ({hit_at_3_rate:.1%})")
        
        # Save detailed results
        results_file = "evaluation_results.json"
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\n💾 Detailed results saved to: {results_file}")
        
        return results
        
    except Exception as e:
        print(f"❌ Evaluation failed: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_sdk_client():
    """Test the SDK client functionality."""
    print("\n" + "=" * 60)
    print("🐍 TESTING SDK CLIENT")
    print("=" * 60)
    
    try:
        from sdk.client import RetrievalClient
        
        # Test client initialization
        client = RetrievalClient()
        
        # Test retrieval
        query = "age verification requirements"
        start_time = time.time()
        results = client.retrieve(query, top_k=3)
        latency = (time.time() - start_time) * 1000
        
        print(f"✅ SDK client working")
        print(f"   🔍 Query: '{query}'")
        print(f"   📊 Results: {len(results)}")
        print(f"   ⏱️  Latency: {latency:.1f}ms")
        
        if results:
            result = results[0]
            print(f"   🏆 Top result:")
            print(f"      • Law: {result['law_id']} ({result['jurisdiction']})")
            print(f"      • Score: {result['score']:.3f}")
            print(f"      • Section: {result['section_label']}")
        
        return True
        
    except Exception as e:
        print(f"❌ SDK client failed: {e}")
        return False

def main():
    """Run all tests and evaluations."""
    print("🚀 REGULATION RETRIEVER AGENT - COMPREHENSIVE TEST")
    print("=" * 60)
    
    # Test 1: Index Building
    index_success = test_index_building()
    if not index_success:
        print("❌ Cannot proceed without a valid index. Exiting.")
        return
    
    # Test 2: Retrieval Service
    retrieval_success, _ = test_retrieval_service()
    if not retrieval_success:
        print("❌ Cannot proceed without working retrieval. Exiting.")
        return
    
    # Test 3: SDK Client
    sdk_success = test_sdk_client()
    
    # Test 4: Comprehensive Evaluation
    eval_results = run_evaluation()
    
    # Final Summary
    print("\n" + "=" * 60)
    print("🏁 FINAL TEST SUMMARY")
    print("=" * 60)
    
    print(f"✅ Index Building: {'PASS' if index_success else 'FAIL'}")
    print(f"✅ Retrieval Service: {'PASS' if retrieval_success else 'FAIL'}")
    print(f"✅ SDK Client: {'PASS' if sdk_success else 'FAIL'}")
    print(f"✅ Evaluation: {'PASS' if eval_results else 'FAIL'}")
    
    if eval_results:
        hit_rate = eval_results["hit_at_3"] / eval_results["total_queries"]
        p95_latency = statistics.quantiles(eval_results["latencies"], n=20)[18] if len(eval_results["latencies"]) >= 20 else max(eval_results["latencies"])
        
        print(f"\n🎯 Key Metrics:")
        print(f"   • Hit@3 Rate: {hit_rate:.1%}")
        print(f"   • P95 Latency: {p95_latency:.1f}ms")
        
        overall_success = index_success and retrieval_success and hit_rate >= 0.8 and p95_latency < 1000
        print(f"\n🏆 Overall Status: {'SUCCESS' if overall_success else 'NEEDS IMPROVEMENT'}")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    main()
