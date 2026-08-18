export default function StatBarList({ data, labels, colorPrefix }) {
  const entries = Object.entries(data);
  const max = Math.max(1, ...entries.map(([, count]) => count));

  return (
    <ul className="stat-bar-list">
      {entries.map(([key, count]) => (
        <li key={key}>
          <div className="stat-bar-header">
            <span>{labels[key] || key}</span>
            <span>{count}</span>
          </div>
          <div className="stat-bar-track">
            <div
              className={`stat-bar-fill ${colorPrefix}-${key}`}
              style={{ width: `${(count / max) * 100}%` }}
            />
          </div>
        </li>
      ))}
    </ul>
  );
}
