from strands import Agent
from strands.models.ollama import OllamaModel
from strands.handlers.callback_handler import PrintingCallbackHandler

def handle_events(**kwargs):
    # Filter and display reasoning loop events
    if 'event' in kwargs:
        event = kwargs['event']
        
        # Show content generation (reasoning and response)
        if 'contentBlockDelta' in event:
            delta = event['contentBlockDelta'].get('delta', {})
            text = delta.get('text', '')
            if text:
                print(text, end='', flush=True)
        
        # Show when content block starts/stops
        elif 'contentBlockStart' in event:
            print("\n[THINKING]")
        elif 'contentBlockStop' in event:
            print("\n[THINKING]")
        
        # Show message boundaries
        elif 'messageStart' in event:
            print("\n=== AGENT THINKING ===")
        elif 'messageStop' in event:
            print("\n=== AGENT FINISHED ===")
            stop_reason = event['messageStop'].get('stopReason', 'unknown')
            print(f"Stop reason: {stop_reason}")
        
        # Show usage metrics
        elif 'metadata' in event:
            usage = event['metadata'].get('usage', {})
            metrics = event['metadata'].get('metrics', {})
            print(f"\nTokens used: {usage.get('totalTokens', 0)} (input: {usage.get('inputTokens', 0)}, output: {usage.get('outputTokens', 0)})")
            print(f"Latency: {metrics.get('latencyMs', 0):.2f}ms")
    
    # Show final result
    elif 'result' in kwargs:
        result = kwargs['result']
        print("\n\n=== FINAL RESPONSE ===")
        if hasattr(result, 'message') and result.message:
            content = result.message.get('content', [])
            for item in content:
                if 'text' in item:
                    print(item['text'])
        print("\n=== END ===")


ollama_model = OllamaModel(
    host="http://localhost:11434",
    model_id="qwen3:4b",

)

agent = Agent(
    model=ollama_model,
    system_prompt="You are a helpful assistant, you always reason your answers before answering the user's query.",
    callback_handler=handle_events,
    )


result = agent("What is the 2 + 3 + 41 - 32 + 432 -6588 + 65988 ? ")
