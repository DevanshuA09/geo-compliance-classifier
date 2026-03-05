import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { Badge } from "./ui/badge";
import { Progress } from "./ui/progress";
import { ScrollArea } from "./ui/scroll-area";
import { Avatar, AvatarFallback } from "./ui/avatar";
import { Bot, Clock, Activity, TrendingUp, Server, Zap } from "lucide-react";

export function AgentStatusPanel() {
  const agents = [
    { 
      id: "agent-1", 
      name: "GDPR Analyzer", 
      status: "active", 
      accuracy: 96.8, 
      tasksCompleted: 147,
      avatar: "GA"
    },
    { 
      id: "agent-2", 
      name: "CCPA Validator", 
      status: "active", 
      accuracy: 94.2, 
      tasksCompleted: 93,
      avatar: "CV"
    },
    { 
      id: "agent-3", 
      name: "HIPAA Checker", 
      status: "idle", 
      accuracy: 98.1, 
      tasksCompleted: 67,
      avatar: "HC"
    },
    { 
      id: "agent-4", 
      name: "SOX Auditor", 
      status: "processing", 
      accuracy: 91.7, 
      tasksCompleted: 28,
      avatar: "SA"
    },
  ];

  const recentActivity = [
    { 
      id: 1, 
      action: "GDPR analysis completed", 
      agent: "GDPR Analyzer", 
      time: "2 min ago",
      status: "success"
    },
    { 
      id: 2, 
      action: "Privacy policy review started", 
      agent: "CCPA Validator", 
      time: "5 min ago",
      status: "processing"
    },
    { 
      id: 3, 
      action: "Risk assessment flagged", 
      agent: "HIPAA Checker", 
      time: "8 min ago",
      status: "warning"
    },
    { 
      id: 4, 
      action: "Compliance report generated", 
      agent: "SOX Auditor", 
      time: "12 min ago",
      status: "success"
    },
    { 
      id: 5, 
      action: "Document processing queued", 
      agent: "GDPR Analyzer", 
      time: "15 min ago",
      status: "pending"
    },
  ];

  const systemMetrics = [
    { label: "CPU Usage", value: 68, icon: Server, color: "text-blue-600" },
    { label: "Memory", value: 42, icon: Activity, color: "text-green-600" },
    { label: "Processing Speed", value: 89, icon: Zap, color: "text-purple-600" },
    { label: "Uptime", value: 99.8, icon: TrendingUp, color: "text-emerald-600", isPercentage: true },
  ];

  const getStatusColor = (status: string) => {
    switch (status) {
      case "active": return "bg-green-500";
      case "processing": return "bg-blue-500";
      case "idle": return "bg-gray-400";
      default: return "bg-gray-400";
    }
  };

  const getActivityStatusColor = (status: string) => {
    switch (status) {
      case "success": return "text-green-600";
      case "processing": return "text-blue-600";
      case "warning": return "text-yellow-600";
      case "pending": return "text-gray-600";
      default: return "text-gray-600";
    }
  };

  return (
    <div className="space-y-6">
      {/* Agent Status Cards */}
      <Card className="shadow-sm">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Bot className="w-5 h-5" />
            Agent Status
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {agents.map((agent) => (
              <div key={agent.id} className="border rounded-lg p-4 space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <Avatar className="h-8 w-8">
                      <AvatarFallback className="text-xs">{agent.avatar}</AvatarFallback>
                    </Avatar>
                    <div>
                      <div className="font-medium text-sm">{agent.name}</div>
                      <div className="flex items-center gap-2 mt-1">
                        <div className={`w-2 h-2 rounded-full ${getStatusColor(agent.status)}`} />
                        <Badge variant="outline" className="text-xs">
                          {agent.status}
                        </Badge>
                      </div>
                    </div>
                  </div>
                </div>
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="text-muted-foreground">Accuracy</span>
                    <span>{agent.accuracy}%</span>
                  </div>
                  <Progress value={agent.accuracy} className="h-2" />
                  <div className="text-xs text-muted-foreground">
                    {agent.tasksCompleted} tasks completed
                  </div>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Recent Activity Feed */}
      <Card className="shadow-sm">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Clock className="w-5 h-5" />
            Recent Activity
          </CardTitle>
        </CardHeader>
        <CardContent>
          <ScrollArea className="h-[300px]">
            <div className="space-y-4">
              {recentActivity.map((activity) => (
                <div key={activity.id} className="flex items-start gap-3 pb-4 border-b last:border-0">
                  <div className={`w-6 h-6 rounded-full flex items-center justify-center ${
                    activity.status === 'success' ? 'bg-green-100' :
                    activity.status === 'processing' ? 'bg-blue-100' :
                    activity.status === 'warning' ? 'bg-yellow-100' : 'bg-gray-100'
                  }`}>
                    <div className={`w-2 h-2 rounded-full ${
                      activity.status === 'success' ? 'bg-green-500' :
                      activity.status === 'processing' ? 'bg-blue-500' :
                      activity.status === 'warning' ? 'bg-yellow-500' : 'bg-gray-500'
                    }`} />
                  </div>
                  <div className="flex-1 space-y-1">
                    <div className="text-sm">{activity.action}</div>
                    <div className="flex items-center justify-between">
                      <span className="text-xs text-muted-foreground">{activity.agent}</span>
                      <span className="text-xs text-muted-foreground">{activity.time}</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </ScrollArea>
        </CardContent>
      </Card>

      {/* System Metrics */}
      <Card className="shadow-sm">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Activity className="w-5 h-5" />
            System Metrics
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {systemMetrics.map((metric) => (
              <div key={metric.label} className="space-y-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <metric.icon className={`w-4 h-4 ${metric.color}`} />
                    <span className="text-sm">{metric.label}</span>
                  </div>
                  <span className="text-sm font-medium">
                    {metric.value}{metric.isPercentage ? '%' : '%'}
                  </span>
                </div>
                <Progress value={metric.value} className="h-2" />
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}