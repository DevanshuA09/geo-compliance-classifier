# Active Learning Data

This folder contains training data, feedback, and learning patterns for the Active Learning Agent.

## 📁 Contents

### `patterns.json`
Contains identified learning patterns from human corrections:
- **pattern_id**: Unique identifier for each pattern
- **text_pattern**: Description of the pattern (e.g., "Compliant->Non-Compliant")
- **original_prediction**: What the model originally predicted
- **corrected_prediction**: What the human reviewer corrected it to
- **confidence_delta**: Change in confidence score
- **frequency**: How often this pattern occurs
- **examples**: Sample cases demonstrating the pattern
- **regulatory_context**: Regulatory context from RAG analysis
- **geographic_factors**: Geographic considerations
- **demographic_factors**: Demographic considerations

### `corrections.json`
Contains individual human corrections:
- **case_id**: Unique identifier for each correction
- **timestamp**: When the correction was made
- **original_prediction**: Model's original prediction
- **corrected_label**: Human reviewer's corrected label
- **reviewer_reasoning**: Explanation for the correction
- **feature_characteristics**: Geographic, demographic, and regulatory details
- **confidence_score**: Confidence level of the correction
- **model_used**: Which model made the original prediction
- **correction_type**: Type of correction (label, confidence, etc.)
- **impact_score**: Impact assessment of the correction

### `feedback.json`
Contains general feedback and learning insights:
- **feedback_id**: Unique identifier for each feedback item
- **timestamp**: When feedback was provided
- **feedback_type**: Type of feedback (improvement, bug report, etc.)
- **description**: Detailed feedback description
- **priority**: Priority level of the feedback
- **status**: Current status (open, in progress, resolved)

## 🔄 Usage

The Active Learning Agent uses this data to:
1. **Identify Patterns**: Analyze common correction patterns
2. **Improve Models**: Use corrections to retrain and improve accuracy
3. **Track Progress**: Monitor learning and improvement over time
4. **Generate Insights**: Provide feedback on system performance

## 📊 Data Quality

**Note**: The current data contains test examples and may include:
- Placeholder content for demonstration
- Connection error messages from testing
- Sample data for development purposes

For production use, ensure:
- Real human corrections and feedback
- Proper data validation and sanitization
- Regular data quality reviews
- Privacy and compliance considerations

## 🛠️ Management

### Adding New Data
```python
from core.agents import ActiveLearningAgent

agent = ActiveLearningAgent(rag_base_url="http://localhost:8000")

# Record a new correction
agent.record_correction(
    original_prediction="Compliant",
    corrected_label="Non-Compliant",
    reasoning="Missing required consent mechanisms"
)

# Record feedback
agent.record_feedback(
    feedback_type="improvement",
    description="Need better handling of edge cases"
)
```

### Data Backup
- Regular backups of all JSON files
- Version control for data changes
- Export capabilities for analysis

## 📈 Analytics

The data can be analyzed to:
- Track model improvement over time
- Identify common failure patterns
- Measure correction impact
- Optimize learning strategies

---

**For more information, see the [Active Learning Agent documentation](../docs/ACTIVE_LEARNING_SUMMARY.md)**
