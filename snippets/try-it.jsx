export const TryIt = () => {
  const [result, setResult] = useState("");
  async function check() {
    try {
      const response = await fetch("https://api.boundarykit.com/v1/status/summary");
      setResult(String(response.status));
    } catch {
      setResult("Request unavailable");
    }
  }
  return <div><button onClick={check}>Check API status</button><output>{result}</output></div>;
};
