---
name: test
description: Write or run tests — vitest unit tests, playwright e2e tests, storybook stories, test data factories, or CI integration. Use when adding tests to existing code or validating new features. NOT for debugging test failures (use debug skill).
---

# Test

## Environment Scope

**write+execute** — Writes test files and runs test commands (`npx vitest run`, `npx playwright test`). May execute tests that have side effects on local test databases. Does NOT modify production systems. Lists all commands in spec before execution.

## Workflow

1. **Check Existing State** — Are there already tests for this code? Run `find` on test directories to check. If tests exist, ask if user wants to extend coverage or rewrite.
2. **Gather Context** — Read the source code being tested. Identify public interfaces, edge cases, and dependencies to mock.
3. **Generate Spec** — List: test file paths, test cases (describe/it descriptions), what will be mocked, expected coverage areas. State which test runner will be used.
4. **Await Approval** — Present the spec. Do NOT write tests until user confirms.
5. **Implement** — Write test files following the patterns below.
6. **Verify** — Run the new tests: `npx vitest run <file>` (expected: <30s) or `npx playwright test <file>` (expected: <60s). If failures, enter failure loop.
7. **Report** — Show test results. If all pass, summarize coverage added.

### Failure Recovery (max 3 retries)

6a. Read test failure → determine if it's a test bug or a source code bug
6b. If test bug: fix the test. If source code bug: report to user (this is the debug skill's job)
6c. Re-run tests
6d. After 3 failures → present failures to user, ask if source code needs fixing first

### Rollback

If user cancels or tests reveal design issues:
1. Delete newly created test files
2. Revert any test utility/factory additions
3. Confirm with file listing

## Vitest Unit Tests

- Colocate tests: `ComponentName.test.tsx` next to the source
- Use `describe`/`it` structure with clear intent:

```tsx
import { render, screen } from '@testing-library/react';
import { ComponentName } from './ComponentName';

describe('ComponentName', () => {
  it('renders the title', () => {
    render(<ComponentName title="Hello" />);
    expect(screen.getByText('Hello')).toBeInTheDocument();
  });

  it('calls onClick when button is pressed', async () => {
    const onClick = vi.fn();
    render(<ComponentName onClick={onClick} />);
    await userEvent.click(screen.getByRole('button'));
    expect(onClick).toHaveBeenCalledOnce();
  });
});
```

- Prefer `screen.getByRole` over `getByTestId` for accessibility
- Mock external dependencies at module boundary, not deep internals
- Run: `npx vitest` (watch mode) or `npx vitest run` (CI mode)

## Playwright E2E Tests

- Place in `e2e/` directory
- Test critical user flows, not implementation details:

```ts
import { test, expect } from '@playwright/test';

test('user can log in and see dashboard', async ({ page }) => {
  await page.goto('/login');
  await page.getByLabel('Email').fill('user@test.com');
  await page.getByLabel('Password').fill('password');
  await page.getByRole('button', { name: 'Sign in' }).click();
  await expect(page.getByRole('heading', { name: 'Dashboard' })).toBeVisible();
});
```

- Use accessibility locators (`getByRole`, `getByLabel`, `getByText`)
- Run: `npx playwright test` or `npx playwright test --ui` for debugging
- Keep tests independent — each test starts from a clean state

## Storybook Stories

- Every UI component gets at least a `Default` story
- Add stories for important states: loading, error, empty, overflow

```tsx
import type { Meta, StoryObj } from '@storybook/react';
import { ComponentName } from './ComponentName';

const meta: Meta<typeof ComponentName> = {
  component: ComponentName,
  tags: ['autodocs'],
};
export default meta;

type Story = StoryObj<typeof ComponentName>;

export const Default: Story = { args: { title: 'Hello' } };
export const Loading: Story = { args: { isLoading: true } };
export const Error: Story = { args: { error: 'Something went wrong' } };
```

## Test Data Factories

```ts
import { faker } from '@faker-js/faker';

export function buildUser(overrides: Partial<User> = {}): User {
  return {
    id: faker.string.uuid(),
    name: faker.person.fullName(),
    email: faker.internet.email(),
    createdAt: faker.date.past(),
    ...overrides,
  };
}
```

- Factories produce valid defaults — override only what the test cares about
- Keep factories in `test/factories/` with barrel export

## CI Integration

- Pipeline order: lint → typecheck → unit tests → build → e2e tests
- Fail fast: stop pipeline on first failure
- E2E tests run against built artifacts, not dev server
- Use `--reporter=junit` for CI-friendly output

## Accessibility Testing

- `jest-axe` / `vitest-axe` in unit tests: `expect(await axe(container)).toHaveNoViolations()`
- `@storybook/addon-a11y` in every story (automatic axe checks in Storybook UI)
- Playwright: test keyboard navigation flows, focus management, screen reader announcements
- Run accessibility checks in CI — fail on critical/serious violations

## Guardrails

- NEVER write tests that depend on another test's state — each test is isolated
- NEVER test implementation details — test behavior and public interfaces
- NEVER mock the thing being tested — only mock its external dependencies
- NEVER ignore flaky tests — fix or quarantine immediately
- NEVER modify source code to make tests pass (that's the refactor skill's job)
- NEVER skip running the tests after writing them — always verify they pass

## References

- `steering/preferences/stack/react/dependency-graph.md` — Testing stack (vitest, playwright, testing-library), allowed test utilities, and component test boundaries
- `steering/orchestration/local.md` — Running the full stack for e2e test development
