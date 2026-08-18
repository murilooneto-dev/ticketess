export default function Logo({ size = "md", variant = "stacked" }) {
  const src = variant === "wide" ? "/logo-horizontal.png" : "/logo.png";
  return <img src={src} alt="TickeTess" className={`brand-logo brand-logo-${size}`} />;
}
