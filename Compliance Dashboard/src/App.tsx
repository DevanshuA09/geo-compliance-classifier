import { Header } from "./components/Header";
import { ComplianceForm } from "./components/ComplianceForm";
import { AgentStatusPanel } from "./components/AgentStatusPanel";
import { ResultsSection } from "./components/ResultsSection";
import { MCPChat } from "./components/MCPChat";

export default function App() {
  return (
    <div className="min-h-screen bg-background">
      <Header />
      
      <div className="container mx-auto px-6 py-6">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Panel - Compliance Form */}
          <div className="lg:col-span-1">
            <ComplianceForm />
          </div>
          
          {/* Right Panel - Agent Status */}
          <div className="lg:col-span-2">
            <AgentStatusPanel />
          </div>
        </div>
        
        {/* Results Section */}
        <div className="mt-6">
          <ResultsSection />
        </div>
        
        {/* MCP Chat Section */}
        <div className="mt-6">
          <div className="container mx-auto px-6">
            <h2 className="text-2xl font-bold mb-4">MCP Compliance Analysis</h2>
            <div className="h-96">
              <MCPChat />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}