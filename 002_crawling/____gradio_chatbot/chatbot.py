import gradio as gr

history = [
    gr.ChatMessage(role="assistant", content="How can I help you?"),
    gr.ChatMessage(role="user", content="Can you make me a plot of quarterly sales?"),
    gr.ChatMessage(role="assistant", content="I am happy to provide you that report and plot.")
]

with gr.Blocks() as demo:
    gr.Chatbot(history)

demo.launch()