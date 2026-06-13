# Regulatory Retrieval Evaluation v2

The fitted TF-IDF index uses nine frozen summaries from official OSHA, FEMA,
EPA, and U.S. Department of Justice accessibility sources. Safe retrieval
checks the top relevance score and vocabulary coverage before exposing any
precedent.

The evaluation has 11 supported questions and four unrelated questions.

| Metric | Score |
| --- | ---: |
| Recall@1 | 1.0000 |
| Recall@3 | 1.0000 |
| Mean reciprocal rank | 1.0000 |
| Accepted-query accuracy | 1.0000 |
| Out-of-domain rejection | 1.0000 |
| False acceptance | 0.0000 |

The corpus is deliberately narrow. Production deployments need source
freshness checks, jurisdiction metadata, authoritative text snapshots, and
human review before acting on retrieved requirements.
