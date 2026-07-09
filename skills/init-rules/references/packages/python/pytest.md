# pytest (Tier 2)

pytest idioms only (assume pytest 7+/8+; check the installed major). For Python
typing/tooling see `../../languages/python.md`; for what to test and coverage
philosophy see `../../concerns/testing-qa.md`. Balance policy: a consistent
existing pattern wins unless it is a security/correctness/performance defect.

## Plain `assert`, no unittest scaffolding
- Write module-level `def test_*` functions with bare `assert`. pytest rewrites
  assertions for rich diffs — no `self.assertEqual`, no `TestCase` subclass.
- Group only when it buys shared fixtures; a class is not required.

## Fixtures over setup/teardown
- Replace `setUp`/`tearDown` with `@pytest.fixture`. Yield for teardown so
  cleanup lives next to setup.
- Pick the narrowest scope that is correct: `function` (default) for isolation;
  `session`/`module` only for expensive, read-only resources. Wider scope leaks
  state between tests.
- Put fixtures shared across files in `conftest.py` at the right directory level;
  pytest discovers them automatically — do not import them.

## Parametrize instead of duplicating
Use `@pytest.mark.parametrize` for input/expected tables and `ids=` for readable
case names. One assertion loop, many cases.

## Markers
Register custom markers in `pyproject.toml` (`[tool.pytest.ini_options] markers`)
so `--strict-markers` catches typos. Use them for selection (`-m "not slow"`).

## Don't over-mock; test behaviour
Mock only true external boundaries (network, clock, third-party SDKs). Mocking
the code under test just asserts your mocks. Keep tests deterministic: freeze
time (`freezegun`/`time-machine` or a clock fixture), fake I/O and randomness,
seed data. Treat coverage as a signal for untested paths, not a target to game.

❌ Bad — unittest class, manual setup, over-mocked, duplicated cases
```python
class TestDiscount(unittest.TestCase):
    def setUp(self):
        self.calc = Discount()

    def test_ten(self):
        self.assertEqual(self.calc.apply(100, 10), 90)

    def test_twenty(self):
        self.assertEqual(self.calc.apply(100, 20), 80)

    def test_total(self):
        repo = mock.Mock()                 # mocking the object under test
        repo.total.return_value = 100
        self.assertEqual(OrderTotals(repo).for_(1), 100)
```
✅ Good — plain functions, fixture, parametrize, real collaborators
```python
@pytest.fixture
def calc() -> Discount:
    return Discount()

@pytest.mark.parametrize(
    ("pct", "expected"),
    [(10, 90), (20, 80)],
    ids=["ten-percent", "twenty-percent"],
)
def test_applies_percentage_discount(calc, pct, expected):
    assert calc.apply(100, pct) == expected

def test_totals_an_order(db_session):        # real DB fixture from conftest.py
    order = make_order(db_session, items=3)
    assert OrderTotals(db_session).for_(order.id) == 300
```

Source: best-practice · Confidence: high
