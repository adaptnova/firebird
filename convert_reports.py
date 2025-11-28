#!/usr/bin/env python3
"""Convert JSON reports to Markdown"""

import json
import os

reports_dir = '/adapt/projects/firebird/reports'
output_dir = '/adapt/projects/firebird/reports/markdown_reports'
os.makedirs(output_dir, exist_ok=True)

# Get all JSON reports
json_files = [f for f in os.listdir(reports_dir) if f.startswith('research_worker') and f.endswith('.json')]

print(f"Converting {len(json_files)} reports to Markdown...")

for json_file in json_files:
    json_path = os.path.join(reports_dir, json_file)
    
    # Read JSON
    with open(json_path, 'r') as f:
        data = json.load(f)
    
    # Create Markdown filename
    topic = data['topic'].replace(' ', '_').replace('/', '_').replace(':', '_')[:50]
    md_filename = f"{topic}.md"
    md_path = os.path.join(output_dir, md_filename)
    
    # Create Markdown
    md_content = f"""# 🔥 {data['topic']}

**Generated**: {data['timestamp']}
**Duration**: {data['duration_seconds']:.1f} seconds
**Sources**: {len(data['sources'])}

---

## Executive Summary

{data['executive_summary']}

---

## Key Findings

"""
    
    for i, finding in enumerate(data['key_findings'], 1):
        md_content += f"{i}. {finding}\n"
    
    md_content += f"""
---

## Sources (Real Content)

"""
    
    for i, source in enumerate(data['sources'][:5], 1):
        md_content += f"""### {i}. {source['title']}

**URL**: {source['url']}
**Query**: {source['query']}

{source['content'][:1000]}...

---

"""
    
    # Add recommendations
    md_content += "## Recommendations\n\n"
    for i, rec in enumerate(data.get('recommendations', []), 1):
        md_content += f"{i}. {rec}\n"
    
    # Write Markdown
    with open(md_path, 'w') as f:
        f.write(md_content)
    
    print(f"✅ Created: {md_filename}")

print(f"\n🎉 All reports converted to Markdown!")
print(f"📁 Location: {output_dir}/")
print(f"📊 Total: {len(json_files)} Markdown reports")
