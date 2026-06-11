"""WorkerProfile runs the shared temporal conformance suite (TECH-4).
Every future module's effective-dated entities must subclass this the same way."""
from platform_core.conformance import TemporalConformanceSuite


class TestWorkerProfileTemporalConformance(TemporalConformanceSuite):
    pass
