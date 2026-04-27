---
name: literature-review
description: Structured paper search and synthesis — search papers, extract key claims, build annotated bibliography, identify gaps. Use when asked to find papers, review literature, or understand a research area.
---

# Literature Review

You have been asked to review literature on a topic. Follow this protocol. It uses available MCP servers for search, the research state for tracking, and display addons for output.

## The Workflow

### 1. Accept topic and initialize

Get a clear research question or topic from the user. Initialize the research state:

```python
python -c "
import sys; sys.path.insert(0, '.')
from core.research import init_research
init_research('Literature review: TOPIC HERE')
"
```

If the question is vague, ask the user to sharpen it before proceeding. "Machine learning" is too broad. "Recent approaches to physics-informed neural networks for fluid dynamics" is workable.

### 2. Search broadly

Cast a wide net using all available search tools. Run multiple searches in parallel.

**arXiv MCP** — for ML, CS, physics, math preprints:
```
mcp__arxiv-latex-mcp__get_paper_abstract  — get abstract by arXiv ID
mcp__arxiv-latex-mcp__list_paper_sections — browse paper structure
mcp__arxiv-latex-mcp__get_paper_section   — read specific sections in LaTeX
```
arXiv MCP reads raw LaTeX, so equations come through clean. Use it when you have specific paper IDs or need to read a paper's actual content.

**Hugging Face** — for ML papers, models, datasets:
```
mcp__claude_ai_Hugging_Face__paper_search — search papers by keyword
mcp__claude_ai_Hugging_Face__hub_repo_search — find models/datasets related to the topic
```
Good for finding the ML papers that have associated code, models, or datasets.

**Bio-research MCP** — for biomedical and life sciences:
```
mcp__bio-research: pubmed — search PubMed, get article metadata and full text
mcp__bio-research: biorxiv — search bioRxiv/medRxiv preprints
mcp__bio-research: chembl — compound/target search (chemistry-specific)
mcp__bio-research: c-trials — clinical trial data
mcp__bio-research: open targets — target-disease associations
```
Use PubMed for established biomedical literature. Use bioRxiv for recent preprints. Use the specialized tools (ChEMBL, clinical trials, Open Targets) only when the topic demands them.

**Firecrawl** — for web search, surveys, blog posts:
```
mcp__firecrawl-mcp__firecrawl_search — web search
mcp__firecrawl-mcp__firecrawl_scrape — scrape a specific URL
```
Use firecrawl to find survey articles, blog posts, course notes, or popular explanations that point to key papers. Also useful for finding papers not indexed in arXiv (e.g., Nature, Science, PNAS).

**PapersFlow** — for broad academic search (474M papers via OpenAlex):
If installed (`papersflow` MCP server), use it for cross-disciplinary search, citation counts, and finding papers outside arXiv's scope. Check available tools with ToolSearch first.

### Which tool when

| Domain | Primary search | Secondary |
|--------|---------------|-----------|
| ML / CS / AI | Hugging Face paper_search | arXiv MCP for reading, firecrawl for surveys |
| Physics / Math | arXiv MCP | firecrawl for textbooks and lecture notes |
| Biomedical | PubMed (bio-research) | bioRxiv for preprints, firecrawl for reviews |
| Chemistry / Pharma | ChEMBL + PubMed | clinical trials for translational work |
| Cross-disciplinary | Firecrawl search | all of the above as relevant |

### 3. Filter and prioritize

From the initial search, select 5-10 papers based on:

- **Relevance** — Does the paper directly address the research question?
- **Impact** — Citation count, venue quality, author reputation
- **Recency** — Prefer recent work, but include foundational papers
- **Methodological diversity** — Don't just grab 10 papers that all do the same thing
- **Coverage** — Include at least one survey/review if available

Log your selection rationale:
```python
python -c "
import sys; sys.path.insert(0, '.')
from core.research import update_state
update_state('assumptions', '- Selected papers based on: relevance to [topic], citation count, methodological diversity\n- Prioritized surveys and foundational papers alongside recent work')
"
```

### 4. Extract per paper

For each selected paper, extract a structured record:

- **Title, authors, year, venue**
- **Main claims** — What does this paper argue or demonstrate?
- **Methodology** — What approach/method/framework do they use?
- **Key results** — Quantitative results, theorems proved, phenomena observed
- **Limitations** — What do the authors acknowledge? What do you notice?
- **Relation to question** — How does this connect to the research question?

Use arXiv MCP to read paper sections directly when you need detail:
```
mcp__arxiv-latex-mcp__get_paper_section(paper_id="2301.12345", section="introduction")
mcp__arxiv-latex-mcp__get_paper_section(paper_id="2301.12345", section="results")
```

For non-arXiv papers, use firecrawl to scrape the paper page or abstract.

### 5. Synthesize

Build a structured synthesis. This is the core deliverable — not just a list of papers, but an analysis of the field.

**What's known** — Points of consensus across papers. Results that multiple groups have reproduced or that are well-established.

**What's debated** — Conflicting results or claims. Papers that disagree on methodology, interpretation, or conclusions. When papers conflict:
- Note the specific disagreement
- Identify possible reasons (different datasets, assumptions, metrics)
- Don't pick a winner unless the evidence is overwhelming
- Flag this as an open question

**What's unknown** — Gaps in the literature. Questions that no paper addresses. Methodological blind spots. These are often the most valuable findings.

**Methodological trends** — Common approaches, emerging techniques, tools being adopted or abandoned.

**Timeline** — How has the field evolved? Key inflection points, paradigm shifts.

### 6. Update research state

Write findings to the research state so they persist and connect to other work:

```python
python -c "
import sys; sys.path.insert(0, '.')
from core.research import update_state, add_observed

# Update the narrative
update_state('established', '''## Literature Review: [TOPIC]

### What's Known
- [consensus point 1] (Smith 2023, Jones 2024)
- [consensus point 2] (multiple sources)

### What's Debated
- [point of disagreement] — Smith claims X, Jones claims Y

### What's Unknown
- [gap 1]
- [gap 2]

### Key Papers
1. Smith et al. (2023) — \"Title\" — [one-line summary]
2. Jones et al. (2024) — \"Title\" — [one-line summary]
...
''')

# Add key findings as nodes in the dependency graph.
# Use add_observed — literature consensus is empirical (what the field
# says), not a verifier-checked claim. add_established is reserved for
# results with a verification.log entry.
add_observed('LR1', 'Consensus: [finding]', depends_on=[])
add_observed('LR2', 'Gap identified: [gap]', depends_on=['LR1'])
"
```

### 7. Display results

Show the annotated bibliography and synthesis in the display panel:

```python
python -c "
import sys; sys.path.insert(0, '.')
from displays import show_html

html = '''
<h1>Literature Review: [TOPIC]</h1>
<p class=\"subtitle\">[N] papers reviewed | [date]</p>

<h2>Synthesis</h2>
<h3>What's Known</h3>
<ul>
  <li>[finding] <span class=\"cite\">(Smith 2023)</span></li>
</ul>

<h3>What's Debated</h3>
<ul>
  <li>[disagreement]</li>
</ul>

<h3>Gaps</h3>
<ul>
  <li>[gap]</li>
</ul>

<h2>Annotated Bibliography</h2>
<div class=\"paper\">
  <h3>Smith et al. (2023)</h3>
  <p class=\"meta\">arXiv:2301.12345 | 150 citations</p>
  <p><strong>Claims:</strong> [main claims]</p>
  <p><strong>Method:</strong> [methodology]</p>
  <p><strong>Results:</strong> [key results]</p>
  <p><strong>Limitations:</strong> [limitations]</p>
</div>

<style>
  body { background: #151210; color: #d8d0c8; font-family: 'Archivo', system-ui, sans-serif; padding: 2rem; max-width: 800px; margin: 0 auto; }
  h1 { color: #cc7a58; margin-bottom: 0.25rem; }
  h2 { color: #d8d0c8; border-bottom: 1px solid #3a332b; padding-bottom: 0.5rem; margin-top: 2rem; }
  h3 { color: #3cc497; }
  .subtitle { color: #968e84; margin-top: 0; }
  .cite { color: #968e84; font-size: 0.9em; }
  .meta { color: #685f56; font-size: 0.85em; }
  .paper { border-left: 2px solid #3a332b; padding-left: 1rem; margin-bottom: 1.5rem; }
  .paper h3 { color: #d8d0c8; margin-bottom: 0.25rem; }
  ul { padding-left: 1.5rem; }
  li { margin-bottom: 0.5rem; }
  strong { color: #968e84; }
</style>
'''

show_html(html)
"
```

Alternatively, for simpler output use `show_markdown`:
```python
python -c "
import sys; sys.path.insert(0, '.')
from displays import show_markdown
show_markdown('''
# Literature Review: [TOPIC]

## Synthesis
...

## Annotated Bibliography
...
''', title='Literature Review')
"
```

## Identifying gaps

Gaps are the most valuable output of a literature review. Look for:

- **Missing combinations** — Method A has been applied to Problem X, and Method B to Problem Y, but nobody has tried Method A on Problem Y
- **Scale gaps** — Results exist for toy problems but not realistic ones (or vice versa)
- **Domain gaps** — Well-studied in one field, unknown in another where it's relevant
- **Assumption gaps** — Every paper assumes X, but nobody has tested what happens without X
- **Reproducibility gaps** — Claims made but no code/data released, no independent replication
- **Recency gaps** — The last work on this is from 5+ years ago, and the field has moved on

When you find a gap, state it as a potential research question. This makes the review actionable.

## Handling conflicts between papers

When Paper A says X and Paper B says not-X:

1. **State both positions clearly.** Don't average them or pick one.
2. **Check methodology.** Different datasets? Different metrics? Different definitions?
3. **Check timing.** Does the later paper address the earlier one? Is this a resolved debate?
4. **Check scope.** Maybe both are right in different regimes/domains.
5. **Log as an open thread** in the research state if unresolved.

## Output format

The final output should contain:

1. **One-paragraph summary** — What did we learn? Suitable for someone who won't read the details.
2. **Synthesis** — What's known, debated, unknown, trending (as above).
3. **Annotated bibliography** — Each paper with structured extraction (as above).
4. **Suggested next steps** — Based on gaps, what should be investigated next?

## Key principles

- **Breadth first, depth second.** Start with many papers, then deep-dive on the important ones.
- **Don't just summarize, synthesize.** The value is in connections and gaps, not summaries.
- **Cite everything.** Every claim in the synthesis should trace to specific papers.
- **Be honest about coverage.** State what you searched, what you might have missed, and what databases weren't available.
- **Update research state throughout.** The human can check progress anytime.
- **If a search returns nothing useful, say so.** Don't pad with irrelevant results.
