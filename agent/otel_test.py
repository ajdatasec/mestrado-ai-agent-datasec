from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter


# Define as informações do serviço
resource = Resource.create({
    "service.name": "ai-agent-hybrid",
})

# Configura o provedor de traces
provider = TracerProvider(resource=resource)
trace.set_tracer_provider(provider)

# Exportador OTLP → Collector
otlp_exporter = OTLPSpanExporter(
    endpoint="http://127.0.0.1:4317",
    insecure=True,
)

# Envia os spans para o Collector
span_processor = BatchSpanProcessor(otlp_exporter)
provider.add_span_processor(span_processor)

# Cria o tracer
tracer = trace.get_tracer("ai-agent")


with tracer.start_as_current_span("teste-ai-agent") as span:

    span.set_attribute("agent.name", "hybrid-agent")
    span.set_attribute("agent.type", "RAG-NL2SQL")

    print("Trace iniciado")
    print("Executando operação do AI Agent...")

    resultado = 10 + 20

    print(f"Resultado: {resultado}")


# Garante o envio dos spans antes do programa terminar
provider.force_flush()

print("Trace finalizado")