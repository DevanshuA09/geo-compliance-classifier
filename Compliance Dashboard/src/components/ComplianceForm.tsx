import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { Button } from "./ui/button";
import { Textarea } from "./ui/textarea";
import { Label } from "./ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "./ui/select";
import { Checkbox } from "./ui/checkbox";
import { Send } from "lucide-react";

export function ComplianceForm() {
  const [analysisText, setAnalysisText] = useState("");
  const [analysisType, setAnalysisType] = useState("");
  const [selectedJurisdictions, setSelectedJurisdictions] = useState<string[]>([]);

  const jurisdictions = [
    { id: "us", name: "United States", code: "US" },
    { id: "eu", name: "European Union", code: "EU" },
    { id: "uk", name: "United Kingdom", code: "UK" },
    { id: "ca", name: "Canada", code: "CA" },
    { id: "au", name: "Australia", code: "AU" },
    { id: "jp", name: "Japan", code: "JP" },
    { id: "sg", name: "Singapore", code: "SG" },
    { id: "hk", name: "Hong Kong", code: "HK" },
    { id: "in", name: "India", code: "IN" },
    { id: "br", name: "Brazil", code: "BR" },
    { id: "mx", name: "Mexico", code: "MX" },
    { id: "kr", name: "South Korea", code: "KR" },
  ];

  const handleJurisdictionChange = (jurisdictionId: string, checked: boolean) => {
    if (checked) {
      setSelectedJurisdictions([...selectedJurisdictions, jurisdictionId]);
    } else {
      setSelectedJurisdictions(selectedJurisdictions.filter(id => id !== jurisdictionId));
    }
  };

  const handleSubmit = () => {
    console.log("Analysis submitted:", {
      text: analysisText,
      type: analysisType,
      jurisdictions: selectedJurisdictions
    });
  };

  return (
    <Card className="shadow-sm">
      <CardHeader>
        <CardTitle>Compliance Analysis</CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Analysis Text */}
        <div className="space-y-2">
          <Label htmlFor="analysis-text">Document or Text to Analyze</Label>
          <Textarea
            id="analysis-text"
            placeholder="Paste your document content, contract terms, or policy text here for compliance analysis..."
            className="min-h-[120px] resize-none"
            value={analysisText}
            onChange={(e) => setAnalysisText(e.target.value)}
          />
        </div>

        {/* Analysis Type */}
        <div className="space-y-2">
          <Label>Analysis Type</Label>
          <Select value={analysisType} onValueChange={setAnalysisType}>
            <SelectTrigger>
              <SelectValue placeholder="Select analysis type" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="privacy">Privacy Policy</SelectItem>
              <SelectItem value="contract">Contract Terms</SelectItem>
              <SelectItem value="data-handling">Data Handling Practices</SelectItem>
              <SelectItem value="marketing">Marketing Content</SelectItem>
              <SelectItem value="employment">Employment Terms</SelectItem>
              <SelectItem value="financial">Financial Services</SelectItem>
              <SelectItem value="healthcare">Healthcare Compliance</SelectItem>
              <SelectItem value="general">General Compliance</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {/* Jurisdictions Grid */}
        <div className="space-y-2">
          <Label>Select Jurisdictions</Label>
          <div className="grid grid-cols-2 gap-3">
            {jurisdictions.map((jurisdiction) => (
              <div key={jurisdiction.id} className="flex items-center space-x-2">
                <Checkbox
                  id={jurisdiction.id}
                  checked={selectedJurisdictions.includes(jurisdiction.id)}
                  onCheckedChange={(checked) => 
                    handleJurisdictionChange(jurisdiction.id, checked as boolean)
                  }
                />
                <Label 
                  htmlFor={jurisdiction.id} 
                  className="text-sm cursor-pointer"
                >
                  {jurisdiction.code}
                </Label>
              </div>
            ))}
          </div>
          {selectedJurisdictions.length > 0 && (
            <div className="text-sm text-muted-foreground">
              Selected: {selectedJurisdictions.length} jurisdiction{selectedJurisdictions.length !== 1 ? 's' : ''}
            </div>
          )}
        </div>

        {/* Submit Button */}
        <Button 
          onClick={handleSubmit} 
          disabled={!analysisText.trim() || !analysisType || selectedJurisdictions.length === 0}
          className="w-full"
        >
          <Send className="w-4 h-4 mr-2" />
          Analyze Compliance
        </Button>
      </CardContent>
    </Card>
  );
}