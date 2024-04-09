# Approach
## Phase 1
Finetune Mistral-7B on AIME and MATH datasets
## Phase 2
Implement automated RAG --> automated in-context learning
- Step 1: Retrieve the most similar problems
- Step 2 (optional): Come up with an embedding model where Emb(P1) * Emb(P2) \isequalto Emb(Soln_of_P1) * Emb(Soln_of_P2)
## Phase 3
Introduce code calling and execution
## Phase 4
Devin-like orchesrator implementation --> come up with a plan. Execute on a step of the plan. Do not preserve intermediate competition. Reason over output. 