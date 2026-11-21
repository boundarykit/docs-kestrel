document.addEventListener("pointerover", event => {
  const element = event.target.closest?.('a[rel="next"]');
  if (element) element.title = "Next page";
});
