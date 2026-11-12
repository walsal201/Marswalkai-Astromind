function App() {
  return (
    <main className="mission-console">
      <iframe
        className="mission-console__frame"
        src={`${import.meta.env.BASE_URL}mission-console.html`}
        title="AstroMind space mission planning suite"
        aria-label="AstroMind mission console, including deep-space planning and Marswalk EVA tools"
        allow="clipboard-write"
      />
    </main>
  );
}

export default App;
