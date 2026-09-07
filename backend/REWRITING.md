# Rewriting pipeline

Ghost 1 uses the configured DeepSeek model; Ghost 2 uses the configured Claude model. Both use `services/rewrite.py` for editorial instructions, input bounds and quality checks. This changes prompting and inference orchestration; it does not train or fine-tune model weights.

The prompt prioritises meaning, qualifications, citations and clear prose. It avoids fixed sentence-length recipes, forced errors and detector-evasion claims. Cleanup only trims surrounding whitespace, preserving punctuation inside citations and numbers.

Medium and Aggressive now explicitly rebuild sentence frames and clause grouping. Lexical overlap excludes citations/URLs; per-sentence matching also detects copied sentences moved into a different order. These are editing heuristics, not detector probabilities or semantic checks. Light intentionally allows a close edit. If a mechanically valid output is too similar, the second attempt starts afresh from the source without the previous draft. A remaining warning is returned to the editor rather than hidden.

The research-philosophy regression fixture includes the user's original and previously returned near-copy. To compare levels on this case, use `--fixture tests/fixtures/research_philosophy.json --level aggressive --paid` with the benchmark command below. Reports include lexical overlap for comparison only. Lower overlap alone is not evidence of better writing, factual fidelity or lower detector scores; manually review the fixture's requirements.

An experimental `REWRITE_USE_PLAN=true` option adds claim extraction before writing for Medium/Aggressive inputs of at least 80 words. It is OFF by default: live tests on both supplied passages did not establish a quality benefit worth the extra cost. The normal pipeline drafts directly and then reviews meaning. Experimental plans are not assumed correct; invented protected terms are discarded and the source is retained for review.

For inputs of at least 30 words, mechanically valid drafts undergo a separate model review against the full original source. Review issues trigger targeted correction, preserving the rest of the draft rather than rewriting it again. Normally two drafts are allowed; a third is reserved for concrete unresolved preservation/meaning failures, not further style searching. Each mechanically valid draft is reviewed. Invalid review JSON fails the request instead of silently approving the draft. Reviews can miss errors or raise false alarms: `meaning_reviewed` describes the process, not a guarantee. No AI detector is called by this pipeline.

A conservative mechanical guard rejects newly introduced obligation words such as `required` or `must` when no obligation wording exists in the source. This catches the reported permission-to-obligation regression, but does not cover every modal shift and can flag a legitimate paraphrase. Reviewed Medium/Aggressive outputs above 0.90 word-sequence overlap are returned after the bounded attempts with an explicit warning that the requested rewrite level was not achieved. Similarity alone does not discard a result that passed preservation checks. These thresholds are editorial heuristics, not detector scores.

Mechanical checks compare occurrence counts of citations, numbers and URLs, retain the set of original acronyms and detected opening definition terms, reject incomplete responses and extreme length changes, and flag paragraph changes or near-copying. Acronym repetitions may change with sentence structure. Candidates must pass mechanical and enabled meaning checks. Among those candidates, fewer warnings wins; ties prefer less overlap. Unresolved failures are rejected before history or usage writes. Remaining style warnings are visible in the editor.

The service result includes token counts and generation-call counts, including reviews. A reviewed request normally uses two calls (draft, review), up to six when concrete failures require two corrections and re-reviews. Experimental planning adds one call. SDK transport retries are capped at one per call. SDK timeouts are 60 seconds per HTTP attempt, not a whole-request deadline. This prioritises quality while testing; measure cost before choosing commercial quotas. DeepSeek thinking is disabled for this editing workload. Ghost 1 never silently falls back to Claude.

## API

`POST /humanize` accepts authenticated JSON with `text`, `level` (`light`, `medium`, `aggressive`), `tone` (`academic`, `professional`, `casual`, `friendly`, `creative`), and `mode` (`auto`, `ghost_1`, `ghost_2`). The default mode is `auto`. Free accounts use Ghost 1.

Inputs are limited to 3,000 whitespace-separated words and 24,000 characters. Invalid input returns 422; failed output checks return 502; unavailable providers return 503. Existing response fields remain, with an additive `quality` object containing `warnings`, `repair_used` and `meaning_reviewed`. Warnings are editing suggestions, not detector scores.

Blocking database and provider calls run in the FastAPI worker pool. Existing subscription quotas remain disabled by the development switches in `routers/humanize.py`; the per-request size cap is separate. PostgreSQL history and usage writes share a transaction; the legacy Supabase usage path remains non-atomic. Billing and production account management are deferred.

## Verify

From `backend`, with the project virtual environment active:

```powershell
python -m unittest discover -s tests -v
```

Run the supplied dissertation paragraph against live models (incurs provider charges):

```powershell
python benchmark_rewrite.py --mode both --output ../benchmark-results/academic.json
```

The default evaluates each mode's free-tier model configuration. Add `--paid` for paid-tier models. Reports contain the full source and output, latency, token usage, repair count and a manual review checklist; do not commit private benchmark text. The benchmark does not access Supabase or update user usage.

Compare multiple runs and a varied set of documents for fidelity, naturalness, latency and token cost. The two user-supplied academic cases are not sufficient evidence of superiority over another product. In the cybersecurity case, the closing argument about differing resource endowments must survive. In the philosophy case, check permission versus obligation and the exact method descriptions.

Provider references: [Claude stop reasons](https://platform.claude.com/docs/en/build-with-claude/handling-stop-reasons), [DeepSeek request and completion fields](https://api-docs.deepseek.com/api/create-chat-completion/).
