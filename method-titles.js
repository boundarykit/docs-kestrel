document.addEventListener("pointerover", event => {
  const element = event.target.closest?.('.method');
  if (element) element.title = "HTTP method";
});
