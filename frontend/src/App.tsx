import Chat from "./components/Chat";

export default function App() {
  return (
    <main>
      <h1>Trust the Vibe — Chat</h1>
      <p style={{ opacity: 0.7, marginTop: "-0.5rem" }}>
        Talking to <code>gpt-4o-mini</code> via the FastAPI backend.
      </p>
      <Chat />
    </main>
  );
}
