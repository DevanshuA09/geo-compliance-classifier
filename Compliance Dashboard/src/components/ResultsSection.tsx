import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { Badge } from "./ui/badge";
import { Progress } from "./ui/progress";
import { Alert, AlertDescription } from "./ui/alert";
import { 
  Target, 
  AlertTriangle, 
  CheckCircle, 
  XCircle, 
  Info,
  Flag
} from "lucide-react";

export function ResultsSection() {
  const overallConfidence = 87.3;
  
  const jurisdictionResults = [
    {
      code: "EU",
      name: "European Union (GDPR)",
      score: 92.1,
      status: "compliant",
      issues: 2,
      recommendations: ["Update cookie consent mechanism", "Clarify data retention periods"]
    },
    {
      code: "US",
      name: "United States (CCPA)",
      score: 88.7,
      status: "mostly-compliant",
      issues: 4,
      recommendations: ["Add 'Do Not Sell' link", "Update privacy notice language", "Implement opt-out process"]
    },
    {
      code: "UK",
      name: "United Kingdom (UK GDPR)",
      score: 91.3,
      status: "compliant",
      issues: 1,
      recommendations: ["Minor formatting adjustments needed"]
    },
    {
      code: "CA",
      name: "Canada (PIPEDA)",
      score: 85.2,
      status: "mostly-compliant",
      issues: 3,
      recommendations: ["Strengthen consent mechanisms", "Add breach notification procedures"]
    },
    {
      code: "AU",
      name: "Australia (Privacy Act)",
      score: 76.4,
      status: "needs-attention",
      issues: 6,
      recommendations: ["Significant updates required", "Review collection practices", "Update notification procedures"]
    },
    {
      code: "JP",
      name: "Japan (APPI)",
      score: 68.9,
      status: "non-compliant",
      issues: 8,
      recommendations: ["Major revisions needed", "Implement consent mechanisms", "Add required disclosures"]
    }
  ];

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "compliant": return <CheckCircle className="w-4 h-4 text-green-600" />;
      case "mostly-compliant": return <Info className="w-4 h-4 text-blue-600" />;
      case "needs-attention": return <AlertTriangle className="w-4 h-4 text-yellow-600" />;
      case "non-compliant": return <XCircle className="w-4 h-4 text-red-600" />;
      default: return <Info className="w-4 h-4 text-gray-600" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "compliant": return "text-green-600 bg-green-50 border-green-200";
      case "mostly-compliant": return "text-blue-600 bg-blue-50 border-blue-200";
      case "needs-attention": return "text-yellow-600 bg-yellow-50 border-yellow-200";
      case "non-compliant": return "text-red-600 bg-red-50 border-red-200";
      default: return "text-gray-600 bg-gray-50 border-gray-200";
    }
  };

  const getProgressColor = (score: number) => {
    if (score >= 90) return "bg-green-500";
    if (score >= 80) return "bg-blue-500";
    if (score >= 70) return "bg-yellow-500";
    return "bg-red-500";
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 85) return "text-green-600";
    if (confidence >= 70) return "text-blue-600";
    if (confidence >= 60) return "text-yellow-600";
    return "text-red-600";
  };

  return (
    <div className="space-y-6">
      <Card className="shadow-sm">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Target className="w-5 h-5" />
            Compliance Analysis Results
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Overall Confidence Meter */}
          <div className="bg-muted/50 rounded-lg p-6">
            <div className="text-center space-y-4">
              <div>
                <div className="text-sm text-muted-foreground mb-2">Overall Confidence Score</div>
                <div className={`text-3xl font-semibold ${getConfidenceColor(overallConfidence)}`}>
                  {overallConfidence}%
                </div>
              </div>
              <div className="max-w-md mx-auto">
                <Progress 
                  value={overallConfidence} 
                  className="h-3"
                />
                <div className="flex justify-between text-xs text-muted-foreground mt-2">
                  <span>0%</span>
                  <span>50%</span>
                  <span>100%</span>
                </div>
              </div>
              <Alert>
                <Info className="h-4 w-4" />
                <AlertDescription>
                  Analysis based on current regulatory requirements and best practices. 
                  Review individual jurisdiction results for specific recommendations.
                </AlertDescription>
              </Alert>
            </div>
          </div>

          {/* Jurisdiction-Specific Results */}
          <div>
            <div className="flex items-center gap-2 mb-4">
              <Flag className="w-5 h-5" />
              <h3>Jurisdiction-Specific Results</h3>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {jurisdictionResults.map((result) => (
                <Card key={result.code} className={`border-2 ${getStatusColor(result.status)} shadow-sm`}>
                  <CardContent className="p-4">
                    <div className="space-y-3">
                      {/* Header */}
                      <div className="flex items-center justify-between">
                        <div>
                          <div className="font-medium">{result.code}</div>
                          <div className="text-sm text-muted-foreground">{result.name}</div>
                        </div>
                        <div className="flex items-center gap-2">
                          {getStatusIcon(result.status)}
                          <div className="text-right">
                            <div className="font-medium">{result.score}%</div>
                            <div className="text-xs text-muted-foreground">{result.issues} issues</div>
                          </div>
                        </div>
                      </div>

                      {/* Progress Bar */}
                      <div>
                        <Progress value={result.score} className="h-2" />
                      </div>

                      {/* Status Badge */}
                      <div className="flex justify-between items-center">
                        <Badge 
                          variant="outline" 
                          className={getStatusColor(result.status)}
                        >
                          {result.status.replace('-', ' ')}
                        </Badge>
                        <span className="text-xs text-muted-foreground">
                          {result.recommendations.length} recommendations
                        </span>
                      </div>

                      {/* Recommendations Preview */}
                      <div className="space-y-1">
                        <div className="text-xs font-medium text-muted-foreground">
                          KEY RECOMMENDATIONS:
                        </div>
                        <ul className="space-y-1">
                          {result.recommendations.slice(0, 2).map((rec, index) => (
                            <li key={index} className="text-xs text-muted-foreground flex items-start gap-1">
                              <span className="text-xs">•</span>
                              <span>{rec}</span>
                            </li>
                          ))}
                          {result.recommendations.length > 2 && (
                            <li className="text-xs text-blue-600">
                              +{result.recommendations.length - 2} more recommendations
                            </li>
                          )}
                        </ul>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}