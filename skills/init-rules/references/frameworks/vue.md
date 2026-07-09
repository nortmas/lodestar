# Vue 3 conventions (Tier 2)

Match the repo's existing component style first; these are defaults for Vue 3 + TypeScript projects.

## Composition API + `<script setup>`
- Write new components with `<script setup>` and the Composition API. It is less boilerplate than the Options API and gives clean TypeScript inference for props, emits, and refs.
- Do not mix paradigms within a component. Follow the repo if it standardizes on Options API in legacy areas.

```vue
<!-- ❌ Bad: Options API — verbose, weaker type inference, `this` juggling -->
<script>
export default {
  props: { count: Number },
  data() { return { step: 1 }; },
  computed: { doubled() { return this.count * 2; } },
};
</script>

<!-- ✅ Good: script setup — typed, flat, no `this` -->
<script setup lang="ts">
import { computed, ref } from 'vue';
const props = defineProps<{ count: number }>();
const step = ref(1);
const doubled = computed(() => props.count * 2);
</script>
```

## `ref` vs `reactive`
- Use `ref` for primitives and for values you reassign wholesale. Use `reactive` for objects you mutate field-by-field. Pick one convention and hold it — `ref` everywhere is a defensible default.
- `reactive` loses reactivity if destructured or reassigned; that footgun is why many teams standardize on `ref`.

```ts
// ❌ Bad: destructuring reactive drops reactivity — `name` never updates the view
const state = reactive({ name: 'a', age: 1 });
const { name } = state;

// ✅ Good: ref stays reactive; access via .value in script, unwrapped in template
const name = ref('a');
const age = ref(1);
```

## Props, emits, derived state
- Type props with `defineProps<T>()` and emits with `defineEmits<T>()`. Prefer the type-only form over the runtime object form in TS projects.
- Never mutate a prop. Data flows down via props, up via emits (one-way). To derive local state, use a `computed` or copy into a local `ref`.
- Use `computed` for derived values, not methods — computeds cache and only recompute when dependencies change; a method re-runs on every render.

```ts
const emit = defineEmits<{ update: [value: string] }>();
// derived state: computed, not a method call in the template
const fullName = computed(() => `${props.first} ${props.last}`);
```

## Composables and templates
- Extract shared stateful logic into composables named `useX` (e.g. `useAuth`, `usePagination`) returning refs/computeds. This is the Composition API's replacement for mixins.
- Keep templates declarative. No heavy expressions inline — move them to a `computed` or method so they stay testable and readable.

```vue
<!-- ❌ Bad: logic buried in the template -->
<span>{{ items.filter(i => i.active).map(i => i.name).join(', ') }}</span>

<!-- ✅ Good: named computed -->
<span>{{ activeNames }}</span>
```

Source: best-practice · Confidence: high
