\# Account ID Strategy



Account ID is derived from filename.



Rule:



demo\_<company>.txt → <company>

onboarding\_<company>.txt → <company>



Example:



demo\_acme.txt → account\_id = "acme"

onboarding\_acme.txt → account\_id = "acme"



This ensures:

\- Deterministic versioning

\- Idempotency

\- Proper v1 → v2 linkage

