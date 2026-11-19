from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter


# Informações do serviço
resource = Resource.create({
    "service.name": "ai-agent-hybrid",
})

# Provedor de traces
provider = TracerProvider(resource=resource)

# Define o provider global
trace.set_tracer_provider(provider)

# Exportador OTLP → OpenTelemetry Collector
otlp_exporter = OTLPSpanExporter(
    endpoint="http://127.0.0.1:4317",
    insecure=True,
)

# Processador de spans
span_processor = BatchSpanProcessor(otlp_exporter)

provider.add_span_processor(span_processor)


# Tracer utilizado pelo AI Agent
tracer = trace.get_tracer("ai-agent")
