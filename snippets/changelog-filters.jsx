export const ChangelogFilters = () => {
  const [area, select] = useState("API");
  return <div><select value={area} onChange={e => select(e.target.value)}><option>API</option><option>Policies</option></select><p>{area === "API" ? "Review endpoint contracts." : "Review evaluation changes."}</p></div>;
};
