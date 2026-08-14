---
inclusion: manual
---

# useReducer Steering

## When to Use useReducer

### The "Multiple setState" Smell

Swap `useState` for `useReducer` when an event handler updates multiple pieces of state simultaneously. If you see 2+ `setState` calls in the same handler, that's the refactor trigger.

```tsx
// ❌ Multiple setState — coupled updates, easy to miss one
function handleSubmit() {
  setLoading(true);
  setError(null);
  setData(null);
}

// ✅ Single dispatch — all state transitions in one place
function handleSubmit() {
  dispatch({ type: 'FETCH_START' });
}
```

### Next State Depends on Previous State

When calculating new state requires looking at multiple properties of old state, a reducer ensures you work with the most current snapshot without complex functional `useState` updates.

### Predictable State Machines

When a component should only move between specific states (idle → loading → success | error), a reducer strictly enforces boundaries. Ignore invalid transitions in the reducer.

```tsx
// Reducer ignores SUCCESS if not currently loading
case 'FETCH_SUCCESS':
  if (state.status !== 'loading') return state;
  return { status: 'success', data: action.payload, error: null };
```

### Bypassing Callback Prop Drilling

Instead of passing multiple `setThis`/`setThat` callbacks down a deep tree, pass a single `dispatch` via React Context. Any nested component can trigger complex state changes by firing an action.

---

## Best Place: Inside Custom Hooks

Wrapping `useReducer` in a custom hook is the ideal pattern. The UI component never sees the reducer, switch statement, or dispatch calls.

```tsx
// hooks/use-async.ts
interface AsyncState<T> {
  status: 'idle' | 'loading' | 'success' | 'error';
  data: T | null;
  error: string | null;
}

type AsyncAction<T> =
  | { type: 'START' }
  | { type: 'SUCCESS'; payload: T }
  | { type: 'ERROR'; payload: string }
  | { type: 'RESET' };

function asyncReducer<T>(state: AsyncState<T>, action: AsyncAction<T>): AsyncState<T> {
  switch (action.type) {
    case 'START':
      return { status: 'loading', data: null, error: null };
    case 'SUCCESS':
      return { status: 'success', data: action.payload, error: null };
    case 'ERROR':
      return { status: 'error', data: null, error: action.payload };
    case 'RESET':
      return { status: 'idle', data: null, error: null };
    default:
      return state;
  }
}

export function useAsync<T>() {
  const [state, dispatch] = useReducer(asyncReducer<T>, {
    status: 'idle',
    data: null,
    error: null,
  });

  const run = useCallback(async (promise: Promise<T>) => {
    dispatch({ type: 'START' });
    try {
      const data = await promise;
      dispatch({ type: 'SUCCESS', payload: data });
      return data;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Unknown error';
      dispatch({ type: 'ERROR', payload: message });
      throw err;
    }
  }, []);

  const reset = useCallback(() => dispatch({ type: 'RESET' }), []);

  return { ...state, run, reset };
}
```

```tsx
// Component — no awareness of useReducer internals
function UserProfile({ userId }: { userId: string }) {
  const { data: user, status, error, run } = useAsync<User>();

  useEffect(() => {
    run(fetchUser(userId));
  }, [userId, run]);

  if (status === 'loading') return <Skeleton />;
  if (status === 'error') return <ErrorMessage message={error!} />;
  if (!user) return null;

  return <ProfileCard user={user} />;
}
```

### Form State with useReducer in a Custom Hook

```tsx
// hooks/use-multi-step-form.ts
interface FormState {
  step: number;
  data: Record<string, unknown>;
  errors: Record<string, string>;
  isSubmitting: boolean;
}

type FormAction =
  | { type: 'NEXT_STEP' }
  | { type: 'PREV_STEP' }
  | { type: 'SET_FIELD'; payload: { field: string; value: unknown } }
  | { type: 'SET_ERRORS'; payload: Record<string, string> }
  | { type: 'SUBMIT_START' }
  | { type: 'SUBMIT_END' }
  | { type: 'RESET' };

const initialState: FormState = {
  step: 0,
  data: {},
  errors: {},
  isSubmitting: false,
};

function formReducer(state: FormState, action: FormAction): FormState {
  switch (action.type) {
    case 'NEXT_STEP':
      return { ...state, step: state.step + 1, errors: {} };
    case 'PREV_STEP':
      return { ...state, step: Math.max(0, state.step - 1), errors: {} };
    case 'SET_FIELD':
      return { ...state, data: { ...state.data, [action.payload.field]: action.payload.value } };
    case 'SET_ERRORS':
      return { ...state, errors: action.payload };
    case 'SUBMIT_START':
      return { ...state, isSubmitting: true };
    case 'SUBMIT_END':
      return { ...state, isSubmitting: false };
    case 'RESET':
      return initialState;
    default:
      return state;
  }
}

export function useMultiStepForm(totalSteps: number) {
  const [state, dispatch] = useReducer(formReducer, initialState);

  const next = useCallback(() => {
    if (state.step < totalSteps - 1) dispatch({ type: 'NEXT_STEP' });
  }, [state.step, totalSteps]);

  const prev = useCallback(() => dispatch({ type: 'PREV_STEP' }), []);
  const setField = useCallback((field: string, value: unknown) =>
    dispatch({ type: 'SET_FIELD', payload: { field, value } }), []);
  const setErrors = useCallback((errors: Record<string, string>) =>
    dispatch({ type: 'SET_ERRORS', payload: errors }), []);
  const submit = useCallback(() => dispatch({ type: 'SUBMIT_START' }), []);
  const done = useCallback(() => dispatch({ type: 'SUBMIT_END' }), []);
  const reset = useCallback(() => dispatch({ type: 'RESET' }), []);

  return { ...state, next, prev, setField, setErrors, submit, done, reset, totalSteps };
}
```

### Dispatch via Context (Prop Drilling Alternative)

```tsx
// contexts/cart-context.tsx
import { createContext, useContext, useReducer, type Dispatch } from 'react';

interface CartState {
  items: CartItem[];
  total: number;
}

type CartAction =
  | { type: 'ADD_ITEM'; payload: CartItem }
  | { type: 'REMOVE_ITEM'; payload: { id: string } }
  | { type: 'CLEAR' };

function cartReducer(state: CartState, action: CartAction): CartState {
  switch (action.type) {
    case 'ADD_ITEM':
      const items = [...state.items, action.payload];
      return { items, total: items.reduce((sum, i) => sum + i.price, 0) };
    case 'REMOVE_ITEM':
      const filtered = state.items.filter(i => i.id !== action.payload.id);
      return { items: filtered, total: filtered.reduce((sum, i) => sum + i.price, 0) };
    case 'CLEAR':
      return { items: [], total: 0 };
    default:
      return state;
  }
}

const CartContext = createContext<CartState | null>(null);
const CartDispatchContext = createContext<Dispatch<CartAction> | null>(null);

export function CartProvider({ children }: { children: React.ReactNode }) {
  const [state, dispatch] = useReducer(cartReducer, { items: [], total: 0 });
  return (
    <CartContext.Provider value={state}>
      <CartDispatchContext.Provider value={dispatch}>
        {children}
      </CartDispatchContext.Provider>
    </CartContext.Provider>
  );
}

export function useCart() {
  const state = useContext(CartContext);
  if (!state) throw new Error('useCart must be used within CartProvider');
  return state;
}

export function useCartDispatch() {
  const dispatch = useContext(CartDispatchContext);
  if (!dispatch) throw new Error('useCartDispatch must be used within CartProvider');
  return dispatch;
}
```

```tsx
// Deeply nested component — single dispatch, no prop drilling
function AddToCartButton({ item }: { item: Product }) {
  const dispatch = useCartDispatch();
  return (
    <Button onClick={() => dispatch({ type: 'ADD_ITEM', payload: item })}>
      Add to Cart
    </Button>
  );
}
```

---

## Rules

### Keep Reducers Pure

The reducer must be deterministic: current state + action → new state. Never make API calls, mutate the DOM, or generate random IDs inside the reducer. Side effects belong in event handlers or `useEffect`, which dispatch the result.

### Standardize Action Shapes

Always use `{ type: string; payload?: T }`. Keep the API predictable.

```tsx
// ✅ Consistent shape
dispatch({ type: 'ADD_USER', payload: { name: 'Alice' } });

// ❌ Ad-hoc properties
dispatch({ type: 'ADD_USER', user: { name: 'Alice' }, id: 5 });
```

### Always Return Default State

Include a `default` case in your switch. Return current state unchanged (production) or throw an error (development) to catch action type typos.

```tsx
default:
  return state; // or: throw new Error(`Unhandled action: ${action.type}`);
```

### Extract the Reducer Function

Define reducers outside the component. Prevents recreation on every render and makes unit testing trivial.

```tsx
// ✅ Outside component — testable, stable reference
function counterReducer(state: State, action: Action): State { ... }

function Counter() {
  const [state, dispatch] = useReducer(counterReducer, initialState);
}
```

### Don't Over-engineer

If you just need `isOpen` for a dropdown, use `useState`. `useReducer` adds boilerplate — only pay that cost when state complexity justifies it. The trigger is 2+ simultaneous state updates or state-machine logic.

---

## When NOT to Use useReducer

- Single boolean/string/number state (`useState` is simpler)
- Server state (use TanStack Query)
- Global app state with many subscribers (use Zustand)
- Form state with validation (use React Hook Form + Zod)

## Anti-Patterns

- ❌ Side effects inside the reducer (API calls, DOM mutations, timers)
- ❌ Exposing `dispatch` directly from a custom hook (wrap in named functions)
- ❌ Giant monolithic reducer with 20+ action types (split into domain reducers)
- ❌ Using `useReducer` for a single toggle or counter
- ❌ Mutating state directly instead of returning a new object
