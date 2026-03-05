import { Badge } from "./ui/badge";
import { Card } from "./ui/card";
import { Activity, Shield, AlertTriangle, CheckCircle } from "lucide-react";

export function Header() {
  const statusIndicators = [
    { icon: Shield, label: "System Security", status: "active", color: "bg-green-500" },
    { icon: Activity, label: "Real-time Monitoring", status: "active", color: "bg-green-500" },
    { icon: AlertTriangle, label: "Risk Alerts", status: "warning", color: "bg-yellow-500" },
    { icon: CheckCircle, label: "Compliance Check", status: "active", color: "bg-green-500" },
  ];

  const keyMetrics = [
    { label: "Compliance Score", value: "94.2%", change: "+2.1%" },
    { label: "Active Jurisdictions", value: "12", change: "+1" },
    { label: "Risk Level", value: "Low", change: "↓" },
    { label: "Last Updated", value: "2 min ago", change: "" },
  ];

  return (
    <div className="border-b bg-card">
      <div className="container mx-auto px-6 py-6">
        <div className="flex flex-col lg:flex-row justify-between items-start lg:items-center gap-6">
          {/* Title and Status */}
          <div>
            <h1 className="mb-4">Compliance Dashboard</h1>
            <div className="flex flex-wrap gap-6">
              {statusIndicators.map((indicator) => (
                <div key={indicator.label} className="flex items-center gap-3">
                  <div className="flex items-center gap-2">
                    <div className={`w-6 h-6 rounded-full ${indicator.color} flex items-center justify-center`}>
                      <indicator.icon className="w-3 h-3 text-white" />
                    </div>
                    <div>
                      <p className="text-sm text-muted-foreground">{indicator.label}</p>
                      <Badge variant={indicator.status === "active" ? "default" : "secondary"} className="text-xs">
                        {indicator.status}
                      </Badge>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Key Metrics */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 w-full lg:w-auto">
            {keyMetrics.map((metric) => (
              <Card key={metric.label} className="p-4 shadow-sm">
                <div className="text-center">
                  <div className="font-semibold">{metric.value}</div>
                  <div className="text-sm text-muted-foreground">{metric.label}</div>
                  {metric.change && (
                    <div className="text-xs text-green-600 mt-1">{metric.change}</div>
                  )}
                </div>
              </Card>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}