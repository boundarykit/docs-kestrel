document.addEventListener("pointerover", event => {
  const element = event.target.closest?.('button[aria-label="Ask AI"]');
  if (element) element.title = "Ask about BoundaryKit";
});
