"""
Command-line interface for the Regulation Retriever Agent.
"""
import argparse
import json
import logging
import sys
from typing import List, Optional

from sdk.client import RegulationClient
from retriever.models import SearchResult


def setup_logging(verbose: bool = False):
    """Setup logging configuration."""
    level = logging.INFO if verbose else logging.WARNING
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )


def format_result(result: SearchResult, include_score: bool = True) -> str:
    """Format a search result for display."""
    header = f"📄 {result.law_name} ({result.jurisdiction})"
    section = f"📍 {result.section_label}"
    
    if include_score:
        score = f"⭐ Score: {result.score:.3f}"
        lines = f"📝 Lines {result.start_line}-{result.end_line}"
        metadata = f"{score} | {lines} | {result.latency_ms}ms"
    else:
        metadata = f"📝 Lines {result.start_line}-{result.end_line}"
    
    # Format snippet with proper wrapping
    snippet_lines = []
    words = result.snippet.split()
    current_line = ""
    
    for word in words:
        if len(current_line + " " + word) > 80:
            if current_line:
                snippet_lines.append(current_line)
                current_line = word
            else:
                snippet_lines.append(word)
        else:
            current_line = current_line + " " + word if current_line else word
    
    if current_line:
        snippet_lines.append(current_line)
    
    snippet = "\\n".join(f"  {line}" for line in snippet_lines)
    
    return f"{header}\\n{section}\\n{metadata}\\n{snippet}"


def print_results(results: List[SearchResult], include_score: bool = True):
    """Print search results to console."""
    if not results:
        print("❌ No results found")
        return
    
    print(f"\\n🔍 Found {len(results)} result(s):\\n")
    
    for i, result in enumerate(results, 1):
        print(f"[{i}] {format_result(result, include_score)}")
        if i < len(results):
            print("─" * 80)
    
    print()


def retrieve_command(args):
    """Handle retrieve command."""
    try:
        client = RegulationClient(base_url=args.url, timeout=args.timeout)
        
        response = client.retrieve(
            query=args.query,
            laws=args.laws,
            top_k=args.k,
            max_chars=args.max_chars,
            include_citation=True
        )
        
        print_results(response.results, include_score=not args.no_score)
        
        if args.json:
            print("\\n📋 JSON Response:")
            print(json.dumps(response.to_dict(), indent=2))
        
        if args.stats:
            print(f"\\n📊 Query Stats:")
            print(f"  Total latency: {response.total_latency_ms}ms")
            print(f"  Laws searched: {', '.join(response.laws_searched)}")
            print(f"  Chunks searched: {response.total_chunks_searched}")
        
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        return 1
    
    return 0


def health_command(args):
    """Handle health command."""
    try:
        client = RegulationClient(base_url=args.url, timeout=args.timeout)
        health = client.health()
        
        status = health.get('status', 'unknown')
        if status == 'ready':
            print("✅ Service is ready")
        else:
            print(f"⚠️  Service status: {status}")
        
        print(f"📊 Performance metrics:")
        print(f"  Query count: {health.get('query_count', 0)}")
        print(f"  Avg latency: {health.get('avg_latency_ms', 0):.1f}ms")
        print(f"  P95 latency: {health.get('p95_latency_ms', 0):.1f}ms")
        print(f"  Total chunks: {health.get('total_chunks', 0)}")
        
        cache_info = health.get('cache_info', {})
        if cache_info:
            print(f"💾 Cache info:")
            print(f"  Hits: {cache_info.get('hits', 0)}")
            print(f"  Misses: {cache_info.get('misses', 0)}")
            print(f"  Size: {cache_info.get('currsize', 0)}")
        
        if args.json:
            print("\\n📋 Full response:")
            print(json.dumps(health, indent=2))
        
    except Exception as e:
        print(f"❌ Health check failed: {e}", file=sys.stderr)
        return 1
    
    return 0


def search_by_law_command(args):
    """Handle search by specific law."""
    try:
        client = RegulationClient(base_url=args.url, timeout=args.timeout)
        results = client.search_by_law(args.query, args.law, args.k)
        
        print(f"🔍 Searching in {args.law}:")
        print_results(results, include_score=not args.no_score)
        
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        return 1
    
    return 0


def search_by_jurisdiction_command(args):
    """Handle search by jurisdiction."""
    try:
        client = RegulationClient(base_url=args.url, timeout=args.timeout)
        results = client.search_jurisdiction(args.query, args.jurisdiction, args.k)
        
        print(f"🔍 Searching in {args.jurisdiction}:")
        print_results(results, include_score=not args.no_score)
        
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        return 1
    
    return 0


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Regulation Retriever CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic search
  python -m retriever.cli "parental consent for 14-15 year olds in CA" --laws CA_SB976 --k 3
  
  # Search specific law
  python -m retriever.cli search-law "age verification" FL_HB3
  
  # Search by jurisdiction
  python -m retriever.cli search-jurisdiction "systemic risk" EU
  
  # Check service health
  python -m retriever.cli health
        """
    )
    
    # Global options
    parser.add_argument("--url", default="http://localhost:8000", 
                       help="API base URL (default: http://localhost:8000)")
    parser.add_argument("--timeout", type=int, default=30,
                       help="Request timeout in seconds (default: 30)")
    parser.add_argument("--verbose", action="store_true",
                       help="Enable verbose logging")
    parser.add_argument("--json", action="store_true",
                       help="Output JSON response")
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Retrieve command (default)
    retrieve_parser = subparsers.add_parser('retrieve', help='Search legal documents (default)')
    retrieve_parser.add_argument('query', help='Search query')
    retrieve_parser.add_argument('--laws', nargs='+', 
                               help='Filter by specific laws (e.g., EUDSA FL_HB3)')
    retrieve_parser.add_argument('--k', type=int, default=5,
                               help='Number of results (default: 5)')
    retrieve_parser.add_argument('--max-chars', type=int, default=1200,
                               help='Maximum snippet length (default: 1200)')
    retrieve_parser.add_argument('--no-score', action='store_true',
                               help='Hide relevance scores')
    retrieve_parser.add_argument('--stats', action='store_true',
                               help='Show query statistics')
    
    # Health command
    health_parser = subparsers.add_parser('health', help='Check service health')
    
    # Search by law command
    law_parser = subparsers.add_parser('search-law', help='Search within specific law')
    law_parser.add_argument('query', help='Search query')
    law_parser.add_argument('law', choices=['EUDSA', 'CA_SB976', 'FL_HB3', 'US_2258A'],
                           help='Law to search')
    law_parser.add_argument('--k', type=int, default=3,
                           help='Number of results (default: 3)')
    law_parser.add_argument('--no-score', action='store_true',
                           help='Hide relevance scores')
    
    # Search by jurisdiction command
    jurisdiction_parser = subparsers.add_parser('search-jurisdiction', 
                                              help='Search within jurisdiction')
    jurisdiction_parser.add_argument('query', help='Search query')
    jurisdiction_parser.add_argument('jurisdiction', choices=['EU', 'US-CA', 'US-FL', 'US'],
                                    help='Jurisdiction to search')
    jurisdiction_parser.add_argument('--k', type=int, default=5,
                                    help='Number of results (default: 5)')
    jurisdiction_parser.add_argument('--no-score', action='store_true',
                                    help='Hide relevance scores')
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.verbose)
    
    # Handle default command (retrieve)
    if args.command is None:
        if len(sys.argv) > 1 and not sys.argv[1].startswith('-'):
            # Treat first non-flag argument as query for default retrieve command
            args.command = 'retrieve'
            args.query = sys.argv[1]
            args.laws = None
            args.k = 5
            args.max_chars = 1200
            args.no_score = False
            args.stats = False
        else:
            parser.print_help()
            return 0
    
    # Route to appropriate command handler
    if args.command == 'retrieve':
        return retrieve_command(args)
    elif args.command == 'health':
        return health_command(args)
    elif args.command == 'search-law':
        return search_by_law_command(args)
    elif args.command == 'search-jurisdiction':
        return search_by_jurisdiction_command(args)
    else:
        parser.print_help()
        return 0


if __name__ == "__main__":
    sys.exit(main())
