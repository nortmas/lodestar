# Debugging (Tier 2)

Guidance on diagnosing defects methodically and leaving no trace behind.

## The iteration loop — one hypothesis at a time
Gather evidence before changing code: one measurement beats ten guesses. Then loop:
1. **Measure.** Never hypothesize in the void.
2. **Form ONE hypothesis** consistent with the evidence.
3. **Make ONE minimal change.**
4. **Verify with a fresh measurement.**
5. If not fixed → **revert the change before trying the next hypothesis.** Never stack guesses.

Stacking fixes ("let me also try X" while the last attempt is still in the code) turns one bug into three and destroys your ability to attribute cause. Revert is not optional.

```text
❌ Bad: keep layering edits — CSS tweak + config change + new import, none verified, all still in the tree
✅ Good: change one thing → measure → it didn't move the metric → revert → next hypothesis
```

## Measure at every boundary first
When a request crosses boundaries (browser → server → database → external API), the symptom shows at the outermost layer but the bug can live at any of them. Before diagnosing the internals of ANY layer, measure at EVERY boundary: what did each side actually send and receive? A strong prior like "I just edited the frontend, so the bug is there" is wrong as often as right — a legacy server-side guard (validation, auth, a mass-assignment allowlist) silently rejecting the new request looks identical from the UI. Checking the actual request/response at each hop is usually a 30-second answer that saves an hour of spelunking the wrong layer.

## Reproduce first — as a failing test
Before touching a fix, write an automated test that reproduces the bug and fails. This proves you understand the defect, prevents regression, and tells you unambiguously when the fix works. A fix without a reproducer is a guess.

```php
// ✅ Good: lock the bug in before fixing
public function test_discount_not_applied_twice_on_retry(): void
{
    $order = OrderFactory::new()->withCoupon('SAVE10')->create();
    $this->service->apply($order);
    $this->service->apply($order); // retry
    $this->assertSame(10.0, $order->fresh()->discountTotal); // was 20.0 — the bug
}
```

## Bisect to isolate
Narrow the fault space systematically: `git bisect` across commits, binary-search a data set, or disable half the pipeline. Change one variable at a time. Randomly editing several things at once turns one bug into three.

## Structured logging over dump-debugging
Prefer temporary structured log lines or a debugger to scattered `dd()`, `var_dump()`, `print`, or `console.log`. Dumps halt or pollute execution, leak into output, and carry no context. If you must trace, log with an identifier you can grep.

```php
// ❌ Bad: halts the request, no context, easy to forget
dd($order->toArray());

// ✅ Good: greppable, contextual, non-destructive
$logger->debug('order.debug', ['id' => $order->id, 'state' => $order->state]);
```

## Use the debugger and breakpoints
Step through with Xdebug / an IDE debugger to inspect live state and the call stack rather than rebuilding the program's state in your head. Conditional breakpoints beat re-running with more prints.

## Verify the fix is actually live
When a change seems to do nothing, confirm it reached the runtime before concluding it failed. If a fresh measurement shows **nothing moved at all**, suspect delivery — wrong file, stale build/bundle, hot-reload glitch, config/route cache, an un-restarted worker running old code — not a wrong hypothesis. Investigate delivery first; only if the code is confirmed live and the metric still didn't move do you reform the hypothesis. Chasing a "broken" fix that never actually ran is a top time-sink.

## Remove debug artifacts before commit
Strip every `dd`/`dump`/`var_dump`/`console.log`/temporary log line and any `sleep` you added. Committed debug output is noise at best and a data leak at worst. A pre-commit grep for these tokens is worth wiring up.

## Balance note
Adopt the project's existing debug tooling and log channel conventions. But shipping debug dumps to production or committing them is a defect — flag and remove regardless of any local habit of leaving them in.

Source: best-practice · Confidence: high
