import "./globals.css";
import { Providers } from "./providers";

export const metadata = {
  title: "SEH Connectors Portal",
  description: "Internal catalog of MCP connectors and usage instructions.",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
