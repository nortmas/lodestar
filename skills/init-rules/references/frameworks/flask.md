# Flask (Tier 3)

Balance policy: an existing consistent codebase pattern wins over textbook advice
unless it is a security, correctness, or performance defect. For Python idioms see
`../languages/python.md`; for config/secrets and debug exposure see
`../concerns/security.md`.

## Rules

- **Application factory pattern.** Build the app in a `create_app(config)`
  function, not as a module-level global. This makes testing, multiple configs,
  and CLI/worker entry points clean; extensions bind to the app inside it.
- **Blueprints for modularity.** One blueprint per feature/domain, registered in
  the factory with a URL prefix. No single monolithic module of routes.
- **Keep logic in services, not views.** Views parse the request, call a service,
  and shape the response. Business logic and DB work live in plain functions/
  classes so they stay testable without the request context.
- **Config classes per environment.** `Base`/`Dev`/`Prod` config objects (or
  `pydantic-settings`); load secrets from env, never hardcode. Select via an env
  var passed to the factory.
- **Use extensions correctly.** Instantiate extensions (Flask-SQLAlchemy,
  Marshmallow) once at module scope, then `ext.init_app(app)` inside the factory
  — do not bind them to a global app at import time.
- **Never `debug=True` in production.** The Werkzeug debugger exposes an RCE
  console. Gate debug behind config and run under a real WSGI server (gunicorn/
  uWSGI), not `app.run()`. Security carve-out — override even if it is the
  existing pattern.

## ❌ Bad — monolithic global app, logic in the view, debug on

```python
app = Flask(__name__)

@app.route("/users", methods=["POST"])
def create_user():
    db.session.add(User(email=request.json["email"]))   # logic in the view
    db.session.commit()
    return "ok"

app.run(debug=True)                                      # RCE console in prod
```

## ✅ Good — factory, blueprint, service layer

```python
# app/__init__.py
def create_app(config="app.config.Prod") -> Flask:
    app = Flask(__name__)
    app.config.from_object(config)
    db.init_app(app)
    app.register_blueprint(users_bp, url_prefix="/users")
    return app

# app/users/views.py
@users_bp.post("")
def create_user():
    user = user_service.create(UserIn.model_validate(request.json))
    return UserOut.model_validate(user).model_dump(), 201
```

## Research hook

On activation, `WebSearch` `"flask <installed-version> best practices"`. Prefer
official docs (flask.palletsprojects.com), then cross-check a second reputable
source. Codify findings with provenance `researched` + source URL + retrieval
date. Never block on a failed search — fall back to the rules above.

Source: best-practice · Confidence: medium
