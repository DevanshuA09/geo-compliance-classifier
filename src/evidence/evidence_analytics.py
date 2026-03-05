"""
Evidence Analytics Dashboard

Provides comprehensive analytics and insights from evidence logs including:
- Compliance trends and patterns
- Agent performance analysis
- Regulatory impact assessment
- Performance metrics and bottlenecks
"""

import json
import logging
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

logger = logging.getLogger(__name__)


class EvidenceAnalytics:
    """
    Comprehensive analytics for evidence logs.

    Features:
    - Compliance trend analysis
    - Agent performance metrics
    - Regulatory impact assessment
    - Performance bottleneck identification
    - Interactive visualizations
    """

    def __init__(self, evidence_dir: str = "data/evidence"):
        self.evidence_dir = Path(evidence_dir)
        self.evidence_data = []
        self.analytics_cache = {}
        self.cache_ttl = 300  # 5 minutes

    def load_evidence_data(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        force_reload: bool = False,
    ) -> pd.DataFrame:
        """
        Load and cache evidence data.

        Args:
            start_date: Filter from this date
            end_date: Filter until this date
            force_reload: Force reload from files

        Returns:
            DataFrame with evidence data
        """
        cache_key = f"evidence_data_{start_date}_{end_date}"

        # Check cache
        if not force_reload and cache_key in self.analytics_cache:
            cache_entry = self.analytics_cache[cache_key]
            if datetime.now().timestamp() - cache_entry["timestamp"] < self.cache_ttl:
                return cache_entry["data"]

        # Load data from files
        records = []
        files = list(self.evidence_dir.glob("*.jsonl"))

        for file_path in files:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    for line in f:
                        try:
                            record = json.loads(line.strip())

                            # Apply date filters
                            if start_date or end_date:
                                record_timestamp = datetime.fromisoformat(
                                    record.get("timestamp_iso", "")
                                )
                                if start_date and record_timestamp < start_date:
                                    continue
                                if end_date and record_timestamp > end_date:
                                    continue

                            records.append(record)
                        except json.JSONDecodeError:
                            continue
            except Exception as e:
                logger.error(f"Error reading {file_path}: {e}")
                continue

        # Convert to DataFrame
        df = pd.DataFrame(records)

        if not df.empty:
            # Convert timestamp to datetime
            df["timestamp"] = pd.to_datetime(df["timestamp_iso"])
            df["date"] = df["timestamp"].dt.date
            df["hour"] = df["timestamp"].dt.hour
            df["day_of_week"] = df["timestamp"].dt.day_name()

            # Extract confidence scores
            df["confidence"] = pd.to_numeric(df["confidence"], errors="coerce").fillna(
                0.0
            )

            # Extract decision flags
            df["decision_flag"] = df["decision_flag"].astype(bool)

        # Cache the result
        self.analytics_cache[cache_key] = {
            "data": df,
            "timestamp": datetime.now().timestamp(),
        }

        return df

    def get_compliance_trends(
        self, df: pd.DataFrame, time_group: str = "date"
    ) -> Dict[str, Any]:
        """
        Analyze compliance trends over time.

        Args:
            df: Evidence DataFrame
            time_group: Time grouping ('date', 'hour', 'day_of_week')

        Returns:
            Compliance trend analysis
        """
        if df.empty:
            return {}

        # Group by time and calculate compliance rates
        grouped = (
            df.groupby(time_group)
            .agg({"decision_flag": ["count", "sum"], "confidence": "mean"})
            .round(4)
        )

        # Flatten column names
        grouped.columns = ["total_decisions", "compliant_decisions", "avg_confidence"]

        # Calculate compliance rate
        grouped["compliance_rate"] = (
            grouped["compliant_decisions"] / grouped["total_decisions"]
        ).round(4)

        # Calculate trend indicators
        grouped["compliance_change"] = grouped["compliance_rate"].diff()
        grouped["decision_volume_change"] = grouped["total_decisions"].diff()

        # Identify trends
        recent_trend = grouped["compliance_rate"].tail(3).mean()
        overall_trend = grouped["compliance_rate"].mean()
        trend_direction = "improving" if recent_trend > overall_trend else "declining"

        return {
            "trend_data": grouped.to_dict("index"),
            "overall_compliance_rate": float(overall_trend),
            "recent_compliance_rate": float(recent_trend),
            "trend_direction": trend_direction,
            "total_periods": len(grouped),
            "best_period": {
                "time": grouped["compliance_rate"].idxmax(),
                "rate": float(grouped["compliance_rate"].max()),
            },
            "worst_period": {
                "time": grouped["compliance_rate"].idxmin(),
                "rate": float(grouped["compliance_rate"].min()),
            },
        }

    def get_agent_performance(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Analyze agent performance metrics.

        Args:
            df: Evidence DataFrame

        Returns:
            Agent performance analysis
        """
        if df.empty:
            return {}

        # Group by agent
        agent_stats = (
            df.groupby("agent_name")
            .agg(
                {
                    "decision_flag": ["count", "sum"],
                    "confidence": ["mean", "std"],
                    "timestamp": ["min", "max"],
                }
            )
            .round(4)
        )

        # Flatten column names
        agent_stats.columns = [
            "total_decisions",
            "compliant_decisions",
            "avg_confidence",
            "confidence_std",
            "first_decision",
            "last_decision",
        ]

        # Calculate compliance rates
        agent_stats["compliance_rate"] = (
            agent_stats["compliant_decisions"] / agent_stats["total_decisions"]
        ).round(4)

        # Calculate decision volume
        agent_stats["decision_volume"] = agent_stats["total_decisions"]

        # Performance ranking
        agent_stats["performance_rank"] = agent_stats["compliance_rate"].rank(
            ascending=False
        )

        # Identify top and bottom performers
        top_performers = agent_stats.nlargest(3, "compliance_rate")
        bottom_performers = agent_stats.nsmallest(3, "compliance_rate")

        return {
            "agent_stats": agent_stats.to_dict("index"),
            "top_performers": top_performers.to_dict("index"),
            "bottom_performers": bottom_performers.to_dict("index"),
            "overall_agent_compliance": float(agent_stats["compliance_rate"].mean()),
            "agent_count": len(agent_stats),
            "performance_gap": float(
                agent_stats["compliance_rate"].max()
                - agent_stats["compliance_rate"].min()
            ),
        }

    def get_regulatory_impact(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Analyze regulatory impact and patterns.

        Args:
            df: Evidence DataFrame

        Returns:
            Regulatory impact analysis
        """
        if df.empty:
            return {}

        # Extract regulations
        regulations = []
        for regs in df["related_regulations"].dropna():
            if isinstance(regs, list):
                regulations.extend(regs)
            elif isinstance(regs, str):
                # Split by semicolon if it's a string
                regulations.extend([r.strip() for r in regs.split(";") if r.strip()])

        if not regulations:
            return {"regulations_analyzed": 0}

        # Count regulation frequency
        reg_counts = Counter(regulations)
        top_regulations = reg_counts.most_common(10)

        # Analyze compliance by regulation
        regulation_compliance = {}
        for reg in reg_counts.keys():
            reg_mask = df["related_regulations"].apply(
                lambda x: reg in (x if isinstance(x, list) else [x]) if x else False
            )
            if reg_mask.any():
                reg_df = df[reg_mask]
                regulation_compliance[reg] = {
                    "total_cases": len(reg_df),
                    "compliance_rate": float(reg_df["decision_flag"].mean()),
                    "avg_confidence": float(reg_df["confidence"].mean()),
                }

        # Identify high-impact regulations
        high_impact = {
            reg: data
            for reg, data in regulation_compliance.items()
            if data["total_cases"] >= 5 and data["compliance_rate"] < 0.8
        }

        return {
            "total_regulations": len(reg_counts),
            "top_regulations": top_regulations,
            "regulation_compliance": regulation_compliance,
            "high_impact_regulations": high_impact,
            "most_cited_regulation": top_regulations[0] if top_regulations else None,
            "compliance_variance": (
                float(
                    pd.Series(
                        [
                            data["compliance_rate"]
                            for data in regulation_compliance.values()
                        ]
                    ).std()
                )
                if regulation_compliance
                else 0.0
            ),
        }

    def get_performance_insights(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Analyze performance metrics and identify bottlenecks.

        Args:
            df: Evidence DataFrame

        Returns:
            Performance insights
        """
        if df.empty:
            return {}

        # Response time analysis (if available)
        timing_columns = [
            col for col in df.columns if "timings_ms" in col or "ms" in col
        ]
        timing_insights = {}

        for col in timing_columns:
            if col in df.columns:
                timing_data = df[col].dropna()
                if not timing_data.empty:
                    # Extract numeric values from timing data
                    numeric_times = []
                    for item in timing_data:
                        if isinstance(item, dict):
                            numeric_times.extend(
                                [
                                    v
                                    for v in item.values()
                                    if isinstance(v, (int, float))
                                ]
                            )
                        elif isinstance(item, (int, float)):
                            numeric_times.append(item)

                    if numeric_times:
                        timing_insights[col] = {
                            "mean": float(np.mean(numeric_times)),
                            "median": float(np.median(numeric_times)),
                            "p95": float(np.percentile(numeric_times, 95)),
                            "max": float(np.max(numeric_times)),
                            "bottleneck_threshold": 1000,  # ms
                        }

        # Decision volume analysis
        volume_analysis = {
            "total_decisions": len(df),
            "decisions_per_day": len(df)
            / max(1, (df["timestamp"].max() - df["timestamp"].min()).days),
            "peak_hour": (
                int(df["hour"].mode().iloc[0]) if not df["hour"].empty else None
            ),
            "busiest_day": (
                df["day_of_week"].mode().iloc[0]
                if not df["day_of_week"].empty
                else None
            ),
        }

        # Confidence distribution
        confidence_analysis = {
            "mean_confidence": float(df["confidence"].mean()),
            "confidence_distribution": {
                "high": float(len(df[df["confidence"] >= 0.8])),
                "medium": float(
                    len(df[(df["confidence"] >= 0.5) & (df["confidence"] < 0.8)])
                ),
                "low": float(len(df[df["confidence"] < 0.5])),
            },
            "confidence_trend": "stable",  # Could be enhanced with trend analysis
        }

        # Identify bottlenecks
        bottlenecks = []
        for col, insights in timing_insights.items():
            if insights["p95"] > insights["bottleneck_threshold"]:
                bottlenecks.append(
                    {
                        "component": col,
                        "p95_time": insights["p95"],
                        "threshold": insights["bottleneck_threshold"],
                        "severity": (
                            "high"
                            if insights["p95"] > insights["bottleneck_threshold"] * 2
                            else "medium"
                        ),
                    }
                )

        return {
            "timing_insights": timing_insights,
            "volume_analysis": volume_analysis,
            "confidence_analysis": confidence_analysis,
            "bottlenecks": bottlenecks,
            "performance_score": self._calculate_performance_score(df),
        }

    def _calculate_performance_score(self, df: pd.DataFrame) -> float:
        """Calculate overall performance score."""
        if df.empty:
            return 0.0

        # Factors: compliance rate, confidence, volume
        compliance_score = df["decision_flag"].mean() * 40  # 40% weight
        confidence_score = df["confidence"].mean() * 30  # 30% weight
        volume_score = min(len(df) / 100, 1.0) * 30  # 30% weight

        return compliance_score + confidence_score + volume_score

    def generate_insights_report(
        self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Generate comprehensive insights report.

        Args:
            start_date: Analysis start date
            end_date: Analysis end date

        Returns:
            Complete insights report
        """
        # Load data
        df = self.load_evidence_data(start_date, end_date)

        if df.empty:
            return {
                "status": "no_data",
                "message": "No evidence data found for the specified period",
                "period": {
                    "start": start_date.isoformat() if start_date else None,
                    "end": end_date.isoformat() if end_date else None,
                },
            }

        # Generate all analyses
        report = {
            "period": {
                "start": start_date.isoformat() if start_date else None,
                "end": end_date.isoformat() if end_date else None,
                "total_days": (
                    (end_date - start_date).days if start_date and end_date else None
                ),
            },
            "summary": {
                "total_decisions": len(df),
                "overall_compliance_rate": float(df["decision_flag"].mean()),
                "unique_agents": df["agent_name"].nunique(),
                "date_range": {
                    "earliest": df["timestamp"].min().isoformat(),
                    "latest": df["timestamp"].max().isoformat(),
                },
            },
            "compliance_trends": self.get_compliance_trends(df),
            "agent_performance": self.get_agent_performance(df),
            "regulatory_impact": self.get_regulatory_impact(df),
            "performance_insights": self.get_performance_insights(df),
            "recommendations": self._generate_recommendations(df),
        }

        return report

    def _generate_recommendations(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Generate actionable recommendations based on analysis."""
        recommendations = []

        # Compliance rate recommendations
        overall_compliance = df["decision_flag"].mean()
        if overall_compliance < 0.8:
            recommendations.append(
                {
                    "category": "compliance",
                    "priority": "high",
                    "title": "Improve Overall Compliance Rate",
                    "description": f"Current compliance rate is {overall_compliance:.1%}, target is 80%",
                    "action": "Review low-compliance cases and identify root causes",
                    "impact": "high",
                }
            )

        # Agent performance recommendations
        agent_stats = df.groupby("agent_name")["decision_flag"].agg(["count", "mean"])
        underperforming_agents = agent_stats[agent_stats["mean"] < 0.7]

        for agent in underperforming_agents.index:
            recommendations.append(
                {
                    "category": "agent_performance",
                    "priority": "medium",
                    "title": f"Improve {agent} Performance",
                    "description": f'{agent} has {underperforming_agents.loc[agent, "count"]} decisions with {underperforming_agents.loc[agent, "mean"]:.1%} compliance rate',
                    "action": f"Review {agent} decision patterns and provide additional training",
                    "impact": "medium",
                }
            )

        # Performance recommendations
        if "timings_ms" in df.columns:
            timing_data = df["timings_ms"].dropna()
            if not timing_data.empty:
                # Check for slow response times
                slow_responses = timing_data.apply(
                    lambda x: any(
                        v > 1000 for v in x.values() if isinstance(v, (int, float))
                    )
                )
                if slow_responses.any():
                    recommendations.append(
                        {
                            "category": "performance",
                            "priority": "medium",
                            "title": "Address Slow Response Times",
                            "description": f"{slow_responses.sum()} decisions had response times > 1 second",
                            "action": "Investigate performance bottlenecks in evidence processing",
                            "impact": "medium",
                        }
                    )

        return recommendations

    def export_analytics_report(
        self,
        output_path: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        format: str = "json",
    ) -> str:
        """
        Export analytics report to file.

        Args:
            output_path: Output file path
            start_date: Analysis start date
            end_date: Analysis end date
            format: Output format ('json', 'csv', 'html')

        Returns:
            Path to exported file
        """
        report = self.generate_insights_report(start_date, end_date)

        if format == "json":
            with open(output_path, "w") as f:
                json.dump(report, f, indent=2, default=str)

        elif format == "csv":
            # Flatten report for CSV
            flat_data = []
            self._flatten_report(report, flat_data)
            df = pd.DataFrame(flat_data)
            df.to_csv(output_path, index=False)

        elif format == "html":
            html_content = self._generate_html_report(report)
            with open(output_path, "w") as f:
                f.write(html_content)

        return output_path

    def _flatten_report(self, data: Any, flat_data: List[Dict], prefix: str = ""):
        """Flatten nested report structure for CSV export."""
        if isinstance(data, dict):
            for key, value in data.items():
                new_prefix = f"{prefix}.{key}" if prefix else key
                self._flatten_report(value, flat_data, new_prefix)
        elif isinstance(data, list):
            for i, item in enumerate(data):
                new_prefix = f"{prefix}[{i}]"
                self._flatten_report(item, flat_data, new_prefix)
        else:
            flat_data.append({"path": prefix, "value": str(data)})

    def _generate_html_report(self, report: Dict[str, Any]) -> str:
        """Generate HTML report."""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Evidence Analytics Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .section {{ margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }}
                .metric {{ display: inline-block; margin: 10px; padding: 10px; background: #f5f5f5; border-radius: 3px; }}
                .recommendation {{ margin: 10px 0; padding: 10px; background: #fff3cd; border-left: 4px solid #ffc107; }}
                .high-priority {{ border-left-color: #dc3545; background: #f8d7da; }}
                .medium-priority {{ border-left-color: #ffc107; background: #fff3cd; }}
            </style>
        </head>
        <body>
            <h1>Evidence Analytics Report</h1>
            <div class="section">
                <h2>Summary</h2>
                <div class="metric">Total Decisions: {report['summary']['total_decisions']}</div>
                <div class="metric">Compliance Rate: {report['summary']['overall_compliance_rate']:.1%}</div>
                <div class="metric">Unique Agents: {report['summary']['unique_agents']}</div>
            </div>
            
            <div class="section">
                <h2>Recommendations</h2>
                {''.join([f'''
                <div class="recommendation {rec['priority']}-priority">
                    <h3>{rec['title']}</h3>
                    <p><strong>Priority:</strong> {rec['priority'].title()}</p>
                    <p><strong>Description:</strong> {rec['description']}</p>
                    <p><strong>Action:</strong> {rec['action']}</p>
                    <p><strong>Impact:</strong> {rec['impact'].title()}</p>
                </div>
                ''' for rec in report['recommendations']])}
            </div>
        </body>
        </html>
        """
        return html


def main():
    """CLI interface for evidence analytics."""
    import argparse

    parser = argparse.ArgumentParser(description="Generate evidence analytics report")
    parser.add_argument("--output", "-o", required=True, help="Output file path")
    parser.add_argument("--start-date", "-s", help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end-date", "-e", help="End date (YYYY-MM-DD)")
    parser.add_argument(
        "--format",
        choices=["json", "csv", "html"],
        default="json",
        help="Output format",
    )

    args = parser.parse_args()

    # Parse dates
    start_date = None
    end_date = None
    if args.start_date:
        start_date = datetime.strptime(args.start_date, "%Y-%m-%d")
    if args.end_date:
        end_date = datetime.strptime(args.end_date, "%Y-%m-%d")

    # Generate report
    analytics = EvidenceAnalytics()
    output_file = analytics.export_analytics_report(
        args.output, start_date, end_date, args.format
    )

    print(f"Analytics report exported to: {output_file}")


if __name__ == "__main__":
    main()
