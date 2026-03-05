"""
Real-time Evidence Monitoring with WebSocket Updates

Provides live monitoring of evidence logs with real-time updates,
compliance scoring, and alert notifications.
"""

import asyncio
import json
import logging
import threading
import time
from collections import defaultdict, deque
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set

import websockets
from websockets.server import WebSocketServerProtocol

logger = logging.getLogger(__name__)


class ComplianceScore:
    """Compliance scoring and metrics."""

    def __init__(self):
        self.total_decisions = 0
        self.compliant_decisions = 0
        self.non_compliant_decisions = 0
        self.agent_scores = defaultdict(lambda: {"total": 0, "compliant": 0})
        self.hourly_trends = deque(maxlen=24)  # Last 24 hours
        self.alert_thresholds = {
            "compliance_rate": 0.85,  # Alert if below 85%
            "error_rate": 0.10,  # Alert if above 10%
            "response_time": 1000,  # Alert if above 1000ms
        }

    def update_score(self, evidence_record: Dict[str, Any]):
        """Update compliance score with new evidence."""
        self.total_decisions += 1

        decision_flag = evidence_record.get("decision_flag", False)
        agent_name = evidence_record.get("agent_name", "unknown")

        if decision_flag:
            self.compliant_decisions += 1
            self.agent_scores[agent_name]["compliant"] += 1
        else:
            self.non_compliant_decisions += 1

        self.agent_scores[agent_name]["total"] += 1

        # Update hourly trends
        current_hour = datetime.now().replace(minute=0, second=0, microsecond=0)
        if not self.hourly_trends or self.hourly_trends[-1]["hour"] != current_hour:
            self.hourly_trends.append(
                {"hour": current_hour, "total": 0, "compliant": 0, "non_compliant": 0}
            )

        current_trend = self.hourly_trends[-1]
        current_trend["total"] += 1
        if decision_flag:
            current_trend["compliant"] += 1
        else:
            current_trend["non_compliant"] += 1

    def get_compliance_rate(self) -> float:
        """Get overall compliance rate."""
        if self.total_decisions == 0:
            return 0.0
        return self.compliant_decisions / self.total_decisions

    def get_agent_compliance_rates(self) -> Dict[str, float]:
        """Get compliance rates by agent."""
        rates = {}
        for agent, scores in self.agent_scores.items():
            if scores["total"] > 0:
                rates[agent] = scores["compliant"] / scores["total"]
            else:
                rates[agent] = 0.0
        return rates

    def check_alerts(self) -> List[Dict[str, Any]]:
        """Check for compliance alerts."""
        alerts = []

        # Compliance rate alert
        compliance_rate = self.get_compliance_rate()
        if compliance_rate < self.alert_thresholds["compliance_rate"]:
            alerts.append(
                {
                    "type": "low_compliance",
                    "severity": "warning",
                    "message": f'Compliance rate {compliance_rate:.2%} below threshold {self.alert_thresholds["compliance_rate"]:.2%}',
                    "timestamp": datetime.now().isoformat(),
                    "current_value": compliance_rate,
                    "threshold": self.alert_thresholds["compliance_rate"],
                }
            )

        # Agent-specific alerts
        agent_rates = self.get_agent_compliance_rates()
        for agent, rate in agent_rates.items():
            if rate < self.alert_thresholds["compliance_rate"]:
                alerts.append(
                    {
                        "type": "agent_low_compliance",
                        "severity": "warning",
                        "message": f"Agent {agent} compliance rate {rate:.2%} below threshold",
                        "timestamp": datetime.now().isoformat(),
                        "agent": agent,
                        "current_value": rate,
                        "threshold": self.alert_thresholds["compliance_rate"],
                    }
                )

        return alerts


class EvidenceMonitor:
    """
    Real-time evidence monitoring with WebSocket support.

    Features:
    - Live evidence tracking
    - Compliance scoring
    - Real-time alerts
    - WebSocket updates
    - Performance monitoring
    """

    def __init__(self, evidence_dir: str = "data/evidence", port: int = 8765):
        self.evidence_dir = Path(evidence_dir)
        self.port = port
        self.compliance_score = ComplianceScore()
        self.websocket_clients: Set[WebSocketServerProtocol] = set()
        self.monitoring_active = False
        self.monitor_thread = None

        # Performance tracking
        self.performance_metrics = {
            "total_evidence_processed": 0,
            "websocket_messages_sent": 0,
            "last_processing_time": 0,
            "average_processing_time": 0,
        }

        # Callback for new evidence
        self.evidence_callbacks: List[Callable] = []

    def start_monitoring(self):
        """Start the evidence monitoring system."""
        if self.monitoring_active:
            logger.warning("Monitoring already active")
            return

        self.monitoring_active = True
        self.monitor_thread = threading.Thread(
            target=self._monitor_evidence_files, daemon=True
        )
        self.monitor_thread.start()

        logger.info(f"Evidence monitoring started on port {self.port}")

    def stop_monitoring(self):
        """Stop the evidence monitoring system."""
        self.monitoring_active = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)

        logger.info("Evidence monitoring stopped")

    def _monitor_evidence_files(self):
        """Monitor evidence files for changes."""
        last_processed_files = set()

        while self.monitoring_active:
            try:
                # Check for new evidence files
                current_files = set(self.evidence_dir.glob("*.jsonl"))
                new_files = current_files - last_processed_files

                for file_path in new_files:
                    self._process_evidence_file(file_path)

                # Check for updates to existing files
                for file_path in current_files:
                    if file_path in last_processed_files:
                        # Check if file has been modified
                        current_mtime = file_path.stat().st_mtime
                        if (
                            hasattr(self, "_file_mtimes")
                            and self._file_mtimes.get(file_path, 0) < current_mtime
                        ):
                            self._process_evidence_file(file_path, incremental=True)
                        self._file_mtimes[file_path] = current_mtime

                last_processed_files = current_files

                # Sleep before next check
                time.sleep(1)

            except Exception as e:
                logger.error(f"Error in evidence monitoring: {e}")
                time.sleep(5)

    def _process_evidence_file(self, file_path: Path, incremental: bool = False):
        """Process evidence file and extract new records."""
        try:
            start_time = time.time()

            with open(file_path, "r", encoding="utf-8") as f:
                lines = f.readlines()

                if incremental:
                    # Only process new lines
                    if hasattr(self, "_file_positions"):
                        start_line = self._file_positions.get(file_path, 0)
                    else:
                        start_line = 0
                        self._file_positions = {}
                else:
                    start_line = 0

                new_records = []
                for i, line in enumerate(lines[start_line:], start_line + 1):
                    try:
                        record = json.loads(line.strip())
                        new_records.append(record)

                        # Update compliance score
                        self.compliance_score.update_score(record)

                        # Trigger callbacks
                        for callback in self.evidence_callbacks:
                            try:
                                callback(record)
                            except Exception as e:
                                logger.error(f"Callback error: {e}")

                    except json.JSONDecodeError:
                        logger.warning(f"Invalid JSON in {file_path}:{i}")
                        continue

                # Update file position
                if incremental:
                    self._file_positions[file_path] = len(lines)

                # Send WebSocket updates
                if new_records:
                    self._broadcast_evidence_update(new_records)

                # Update performance metrics
                processing_time = (time.time() - start_time) * 1000
                self.performance_metrics["total_evidence_processed"] += len(new_records)
                self.performance_metrics["last_processing_time"] = processing_time

                # Update average processing time
                total_processed = self.performance_metrics["total_evidence_processed"]
                current_avg = self.performance_metrics["average_processing_time"]
                self.performance_metrics["average_processing_time"] = (
                    current_avg * (total_processed - len(new_records)) + processing_time
                ) / total_processed

                logger.debug(
                    f"Processed {len(new_records)} new evidence records from {file_path}"
                )

        except Exception as e:
            logger.error(f"Error processing evidence file {file_path}: {e}")

    def _broadcast_evidence_update(self, records: List[Dict[str, Any]]):
        """Broadcast evidence updates to all WebSocket clients."""
        if not self.websocket_clients:
            return

        # Prepare update message
        update_message = {
            "type": "evidence_update",
            "timestamp": datetime.now().isoformat(),
            "records_count": len(records),
            "compliance_summary": {
                "overall_rate": self.compliance_score.get_compliance_rate(),
                "agent_rates": self.compliance_score.get_agent_compliance_rates(),
                "total_decisions": self.compliance_score.total_decisions,
            },
            "alerts": self.compliance_score.check_alerts(),
        }

        # Send to all connected clients
        message_json = json.dumps(update_message)
        disconnected_clients = set()

        for client in self.websocket_clients:
            try:
                asyncio.run(client.send(message_json))
                self.performance_metrics["websocket_messages_sent"] += 1
            except websockets.exceptions.ConnectionClosed:
                disconnected_clients.add(client)
            except Exception as e:
                logger.error(f"Error sending WebSocket message: {e}")
                disconnected_clients.add(client)

        # Remove disconnected clients
        self.websocket_clients -= disconnected_clients

    async def websocket_handler(self, websocket: WebSocketServerProtocol, path: str):
        """Handle WebSocket connections."""
        try:
            # Add client to set
            self.websocket_clients.add(websocket)
            logger.info(
                f"WebSocket client connected. Total clients: {len(self.websocket_clients)}"
            )

            # Send initial state
            initial_message = {
                "type": "initial_state",
                "timestamp": datetime.now().isoformat(),
                "compliance_summary": {
                    "overall_rate": self.compliance_score.get_compliance_rate(),
                    "agent_rates": self.compliance_score.get_agent_compliance_rates(),
                    "total_decisions": self.compliance_score.total_decisions,
                },
                "performance_metrics": self.performance_metrics,
            }
            await websocket.send(json.dumps(initial_message))

            # Keep connection alive
            async for message in websocket:
                try:
                    data = json.loads(message)
                    await self._handle_websocket_message(websocket, data)
                except json.JSONDecodeError:
                    logger.warning("Invalid JSON received from WebSocket client")
                except Exception as e:
                    logger.error(f"Error handling WebSocket message: {e}")

        except websockets.exceptions.ConnectionClosed:
            logger.info("WebSocket client disconnected")
        finally:
            # Remove client from set
            self.websocket_clients.discard(websocket)
            logger.info(
                f"WebSocket client removed. Total clients: {len(self.websocket_clients)}"
            )

    async def _handle_websocket_message(
        self, websocket: WebSocketServerProtocol, message: Dict[str, Any]
    ):
        """Handle incoming WebSocket messages."""
        message_type = message.get("type")

        if message_type == "ping":
            await websocket.send(
                json.dumps({"type": "pong", "timestamp": datetime.now().isoformat()})
            )

        elif message_type == "get_summary":
            summary = {
                "type": "summary_response",
                "timestamp": datetime.now().isoformat(),
                "compliance_summary": {
                    "overall_rate": self.compliance_score.get_compliance_rate(),
                    "agent_rates": self.compliance_score.get_agent_compliance_rates(),
                    "total_decisions": self.compliance_score.total_decisions,
                },
                "performance_metrics": self.performance_metrics,
                "alerts": self.compliance_score.check_alerts(),
            }
            await websocket.send(json.dumps(summary))

        elif message_type == "subscribe_alerts":
            # Client wants to receive alerts
            await websocket.send(
                json.dumps(
                    {
                        "type": "subscription_confirmed",
                        "message": "Alert subscription active",
                    }
                )
            )

    def add_evidence_callback(self, callback: Callable[[Dict[str, Any]], None]):
        """Add callback for new evidence records."""
        self.evidence_callbacks.append(callback)

    def get_monitoring_status(self) -> Dict[str, Any]:
        """Get monitoring system status."""
        return {
            "monitoring_active": self.monitoring_active,
            "websocket_clients_count": len(self.websocket_clients),
            "compliance_summary": {
                "overall_rate": self.compliance_score.get_compliance_rate(),
                "agent_rates": self.compliance_score.get_agent_compliance_rates(),
                "total_decisions": self.compliance_score.total_decisions,
            },
            "performance_metrics": self.performance_metrics,
            "alerts": self.compliance_score.check_alerts(),
        }


async def start_websocket_server(
    monitor: EvidenceMonitor, host: str = "localhost", port: int = 8765
):
    """Start WebSocket server for evidence monitoring."""
    async with websockets.serve(monitor.websocket_handler, host, port):
        logger.info(f"WebSocket server started on ws://{host}:{port}")
        await asyncio.Future()  # Run forever


def main():
    """Main function to start evidence monitoring."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Start evidence monitoring with WebSocket support"
    )
    parser.add_argument("--host", default="localhost", help="WebSocket server host")
    parser.add_argument("--port", type=int, default=8765, help="WebSocket server port")
    parser.add_argument(
        "--evidence-dir", default="data/evidence", help="Evidence directory to monitor"
    )

    args = parser.parse_args()

    # Create and start monitor
    monitor = EvidenceMonitor(args.evidence_dir, args.port)
    monitor.start_monitoring()

    try:
        # Start WebSocket server
        asyncio.run(start_websocket_server(monitor, args.host, args.port))
    except KeyboardInterrupt:
        logger.info("Shutting down evidence monitor...")
        monitor.stop_monitoring()
    except Exception as e:
        logger.error(f"Error in WebSocket server: {e}")
        monitor.stop_monitoring()


if __name__ == "__main__":
    main()
