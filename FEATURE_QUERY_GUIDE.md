# 🎯 Feature Artifact Query Guide

## 🚀 **Quick Start**

Your system is now working! You can query feature artifacts using the simple Python script I created.

### **Method 1: Use the Query Script (Recommended)**

```bash
# Query with specific number of results
python query_features.py "Does this feature require dedicated logic to comply with region-specific legal obligations?" 5

# Query with default results (5)
python query_features.py "How many features have we rolled out to ensure compliance with this regulation?"

# Interactive mode
python query_features.py
```

### **Method 2: Direct Python Code**

```python
from retriever.faiss_retriever import FaissRetriever

# Create config
config = {
    'embedding': {
        'model_name': 'sentence-transformers/all-MiniLM-L6-v2',
        'dimension': 384
    },
    'rag': {
        'vectorstore': {
            'index_path': 'index/faiss/index.faiss',
            'id_map_path': 'index/faiss/id_map.jsonl',
            'metric': 'ip',
            'normalize': True
        }
    }
}

# Initialize and query
retriever = FaissRetriever(config)
results = retriever.retrieve('Your query here', top_k=5)

# Process results
for result in results:
    print(f"{result.law_name} ({result.jurisdiction})")
    print(f"Section: {result.section_label}")
    print(f"Score: {result.score:.3f}")
    print(f"Text: {result.snippet[:200]}...")
```

## 🔍 **Example Queries**

### **Query 1: Region-Specific Legal Obligations**
```bash
python query_features.py "Does this feature require dedicated logic to comply with region-specific legal obligations?" 8
```

**Expected Results:**
- EU Digital Services Act (DSA) compliance requirements
- US federal reporting requirements
- Jurisdiction-specific legal representative obligations

### **Query 2: Feature Compliance Count**
```bash
python query_features.py "How many features have we rolled out to ensure compliance with this regulation?" 10
```

**Expected Results:**
- NCMEC reporting requirements
- EU DSA compliance functions
- Regulatory enforcement measures

### **Query 3: Specific Regulation Focus**
```bash
python query_features.py "What are the age verification requirements for minors in Florida?" 5
```

### **Query 4: Cross-Jurisdictional Analysis**
```bash
python query_features.py "Compare algorithmic transparency requirements between EU and US jurisdictions" 8
```

## 📊 **Understanding Results**

Each query returns structured results with:

- **Law Name**: e.g., "EU Digital Services Act (DSA)"
- **Jurisdiction**: e.g., "EU", "US", "US-FL"
- **Section Reference**: e.g., "Document.77", "(A)"
- **Relevance Score**: 0.0-1.0 (higher = more relevant)
- **Legal Snippet**: Relevant text excerpt from regulations

## 🛠️ **Troubleshooting**

### **If the script doesn't work:**

1. **Check dependencies:**
   ```bash
   pip install sentence-transformers faiss-cpu numpy
   ```

2. **Verify index files exist:**
   ```bash
   ls -la index/faiss/
   # Should show: index.faiss and id_map.jsonl
   ```

3. **Check Python path:**
   ```bash
   python -c "import sys; print('\\n'.join(sys.path))"
   ```

### **Common Issues:**

- **Import errors**: Make sure you're in the project root directory
- **Index not found**: The FAISS index needs to be built first
- **Memory issues**: The embedding model requires ~2GB RAM

## 🔧 **Advanced Usage**

### **Custom Configuration**

You can modify the configuration in `query_features.py`:

```python
config = {
    'embedding': {
        'model_name': 'sentence-transformers/all-MiniLM-L6-v2',  # Change model
        'dimension': 384  # Adjust dimension
    },
    'rag': {
        'vectorstore': {
            'index_path': 'your/custom/path/index.faiss',
            'id_map_path': 'your/custom/path/id_map.jsonl',
            'metric': 'ip',  # or 'l2', 'cos'
            'normalize': True
        }
    }
}
```

### **Batch Queries**

```python
queries = [
    "Does this feature require dedicated logic to comply with region-specific legal obligations?",
    "How many features have we rolled out to ensure compliance with this regulation?",
    "What are the parental consent requirements for algorithmic features?"
]

for query in queries:
    print(f"\n{'='*60}")
    results = retriever.retrieve(query, top_k=3)
    print(f"Query: {query}")
    print(f"Results: {len(results)}")
```

## 📈 **Performance Tips**

- **Top-k**: Start with 5-10 results, increase if needed
- **Query specificity**: More specific queries yield better results
- **Batch processing**: Process multiple queries together for efficiency
- **Caching**: The embedding model is cached after first use

## 🎯 **What You Can Query**

Your system indexes and can query:

- **EU Regulations**: DSA, GDPR compliance requirements
- **US State Laws**: Florida HB3, California SB976
- **Federal Laws**: COPPA, NCMEC reporting requirements
- **Feature Templates**: TikTok-style feature descriptions
- **Compliance Patterns**: Historical compliance decisions
- **Legal Text**: Full regulatory documents

## 🚀 **Next Steps**

1. **Try the example queries** above
2. **Experiment with your own questions** about feature compliance
3. **Use interactive mode** for exploration: `python query_features.py`
4. **Integrate the code** into your applications

## 📞 **Need Help?**

If you encounter issues:

1. Check this guide first
2. Verify your index files exist
3. Ensure all dependencies are installed
4. Check the Python path and working directory

Your system is now fully functional for querying feature artifacts! 🎉
