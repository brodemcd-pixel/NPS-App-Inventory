import type { Metadata } from "next";
import "./globals.css";
import NavBar from "@/components/NavBar";
import ChatPanel from "@/components/ChatPanel";
import PageViewTracker from "@/components/PageViewTracker";

export const metadata: Metadata = {
  title: "Players — NFL Draft Prospect Intelligence",
  description:
    "Scouting department platform: prospect research, similarity, comparison, watchlists.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        <NavBar />
        <PageViewTracker />
        <main className="mx-auto max-w-[1600px] px-4 py-5">{children}</main>
        <ChatPanel />
      </body>
    </html>
  );
}
