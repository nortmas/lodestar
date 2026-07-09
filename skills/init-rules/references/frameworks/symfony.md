# Symfony (Tier 3)

Balance policy: an existing consistent codebase pattern wins over textbook advice
unless it is a security, correctness, or performance defect.

## Rules

- **Depend on services via autowiring.** Type-hint interfaces/classes in
  constructors; let the container inject. Do not fetch services from the
  container manually or use static access to shared state.
- **Controllers stay thin.** A controller reads the request, calls a service, and
  returns a response. Business logic lives in services, never in the action.
- **Doctrine repositories over inline queries.** Encapsulate queries in repository
  methods; avoid building DQL/SQL ad hoc inside controllers or services.
- **DTOs + Validator component.** Map request payloads into typed DTOs and
  validate with constraint attributes — do not read raw `$request->request->get()`
  values straight into entities.
- **Config via `.env` + secrets vault.** Non-secret env-specific values in
  `.env`/`.env.local`; real secrets in the Symfony secrets vault, never committed.
- **Attribute-based routing.** Declare routes with `#[Route]` attributes on
  actions (current standard) rather than legacy annotations or scattered YAML,
  unless the project consistently uses YAML routing.

## ❌ Bad — business logic in the controller

```php
#[Route('/orders', methods: ['POST'])]
public function create(Request $request, EntityManagerInterface $em): Response
{
    $order = new Order();
    $order->setTotal($request->request->get('total'));
    $order->setStatus('paid'); // Domain rules leaking into the controller.
    $em->persist($order);
    $em->flush();
    return $this->json($order);
}
```

## ✅ Good — delegate to a service

```php
#[Route('/orders', methods: ['POST'])]
public function create(CreateOrderDto $dto, OrderService $orders): Response
{
    // Controller only wires input to the service and returns the result.
    return $this->json($orders->place($dto), Response::HTTP_CREATED);
}
```

## Research hook

On activation, `WebSearch` `"symfony <installed-version> best practices"`. Prefer
official docs (symfony.com/doc), then cross-check a second reputable source.
Codify findings with provenance `researched` + source URL + retrieval date. Never
block on a failed search — fall back to the rules above.

Source: best-practice · Confidence: medium
