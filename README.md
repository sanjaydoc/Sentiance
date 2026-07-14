# Sentiance

A **behavioral-intelligence platform**: it turns smartphone sensor data
(accelerometer + GPS) into structured human-behavior insights — **activities**
(still / walk / run / cycle / vehicle), **trips**, and **transport modes**
(car / bus / train / tram) — organized as a per-user **timeline**.

> Architecture is documented in **[ARCHITECTURE.md](ARCHITECTURE.md)** with
> decision records in **[docs/adr/](docs/adr)**. Read those first for the "why".

## What's here

The flagship **Activity & Transport-Mode** vertical, implemented end-to-end:

```
sensor.raw ──▶ features.window ──▶ activity.window ──▶ segment.detected
 (gateway)      (feature extract)    (classifier)        (segmenter + transport)
```

Stages communicate only through an **event bus**, behind a port with two
adapters — **in-memory** (tests/laptop) and **Kafka/Redpanda** (prod). The exact
same domain code runs both ways (ports & adapters, [ADR-0001](docs/adr/0001-hexagonal-ports-and-adapters.md)).

## Layout

```
sentiance/
  core/          # data contracts (schemas), config, bus + repository ports/adapters
  features/      # windowed feature extraction (time + frequency domain)
  recognition/   # activity classifier, transport-mode refinement, segmentation
  processing/    # pipeline wiring + Kafka worker
  ingestion/     # sensor intake service + FastAPI gateway
  insights/      # timeline/summary read models + webhook fan-out + FastAPI
  simulation/    # synthetic sensor-data generator (walk/run/drive/…)
  app.py         # all-in-one dev server (whole platform, one process)
  __main__.py    # `python -m sentiance` (serve) / `... demo` (in-process demo)
tests/           # pytest suite (unit + API + end-to-end pipeline)
deploy/          # docker-compose realistic stack (Redpanda + Postgres + services)
docs/adr/        # architecture decision records
```

## Quickstart

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

# See the pipeline classify a synthetic walk → drive → walk commute:
python -m sentiance demo

# Or run the whole platform in one process (docs at http://localhost:8000/docs):
python -m sentiance
```

With the server running:

```bash
# Generate + ingest a synthetic commute for a user, then read the timeline.
curl -X POST "http://localhost:8000/v1/simulate?user_id=u_demo"
curl "http://localhost:8000/v1/users/u_demo/timeline"
curl "http://localhost:8000/v1/users/u_demo/summary"
```

Sample timeline (`python -m sentiance demo`):

```
   0.0s →   60.0s  walk       0.08 km  (12 windows)
  60.0s →  180.0s  vehicle [car]  1.80 km  (24 windows)
 180.0s →  240.0s  walk       0.08 km  (12 windows)
```

## How a raw signal becomes an insight

1. **Ingestion** authenticates the tenant, enforces **consent**, deduplicates by
   `(device_id, batch_id)`, and publishes `sensor.raw`
   ([ADR-0004](docs/adr/0004-privacy-and-consent.md)).
2. **Feature extraction** slices the accelerometer magnitude into fixed **5 s
   windows** and computes time- and frequency-domain features (dominant
   frequency, spectral entropy, …) fused with GPS speed/straightness
   ([ADR-0003](docs/adr/0003-windowed-feature-extraction.md)).
3. **Recognition** classifies each window via a **swappable `Classifier`**
   (a transparent heuristic here; a trained model drops in unchanged).
4. **Segmentation** coalesces same-activity windows into segments with
   hysteresis, and refines `vehicle` into a transport mode.
5. **Insights** persists segments, serves the **timeline/summary**, and fans out
   `segment.detected` to customer **webhooks**.

## The model swap-in point

`sentiance/recognition/classifier.py` defines a `Classifier` protocol:

```python
class Classifier(Protocol):
    def classify(self, features: WindowFeatures) -> tuple[Activity, float]: ...
```

Replace `HeuristicActivityClassifier` with a trained model (sklearn, XGBoost, a
small NN) implementing the same method — no other code changes.

## Development

```bash
python -m pytest      # tests + coverage
ruff check .          # lint
ruff format .         # format
```

> Note: the `pytest` on `PATH` may be an isolated tool env; use `python -m
> pytest` to run against the project's interpreter.

## Realistic stack (Kafka + Postgres)

```bash
docker compose -f deploy/docker-compose.yml up --build
# Ingestion gateway → :8080, Insights API → :8081, Redpanda → :9092
```

The services run the same domain code as the tests; only the bus/repository
adapters differ, selected by `SENTIANCE_BUS_BACKEND` ([ADR-0001](docs/adr/0001-hexagonal-ports-and-adapters.md)).

## Roadmap

The pipeline shape extends to further verticals as additional consumer groups —
**driving behavior** (harsh events, speeding, distraction), **moments & places**
(venues, home/work), and **behavioral profiles** — with no change to existing
stages. See [ARCHITECTURE.md §10](ARCHITECTURE.md).

## License

MIT — see [LICENSE](LICENSE).
