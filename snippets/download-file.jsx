export const DownloadFile = ({ href = "/openapi.json", label = "Download the API specification" }) => <a href={href} download>{label}</a>;
