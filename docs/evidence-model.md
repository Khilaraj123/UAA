# UAA Evidence Model & AI Grounding

To prevent hallucinations and speculative assertions, Universal API Assurance enforces that every claim made by an agent must be backed by traceable code or runtime evidence.

## 1. Claim Classification Taxonomy

Every attribute, parameter, and behavior noted in UAA artifacts must be categorized under one of four claim types:

1. **`documented`**: Formally specified in an authoritative API contract (OpenAPI specification, GraphQL schema, Proto definition).
2. **`observed`**: Directly verified through code execution or network response from the target service.
3. **`inferred`**: Deduced via static AST analysis, framework conventions, or type declarations.
4. **`unknown`**: Lacks direct evidence in the repository. Must NOT be guessed; flagged explicitly as requiring human clarification.

## 2. Evidence Anchors

All discovered endpoints and security findings link to concrete `EvidenceAnchor` records:

```json
{
  "source_layer": 2,
  "source_type": "framework_route",
  "file_path": "src/Controllers/OrdersController.cs",
  "line_start": 45,
  "line_end": 52,
  "symbol": "GetOrderById",
  "snippet": "[HttpGet(\"{id}\")]\npublic async Task<IActionResult> GetOrderById(int id)",
  "confidence": "high"
}
```

## 3. Adversarial Review Sign-Off

When Agent B reviews Agent A's discovery, or Agent E reviews Agent D's scenarios, the review result is recorded with provenance:
- `reviewer_role`: Identifies which agent or human reviewed the claim.
- `verdict`: `agreed`, `disputed`, or `needs_more_evidence`.
- `notes`: Critique of evidence completeness or identified omissions.

